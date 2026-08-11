from __future__ import annotations

import argparse
import json
import logging
import mimetypes
import os
import re
import secrets
import sys
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from typing import Any
from urllib.parse import urlsplit


FRONTEND_DIR = Path(__file__).resolve().parent
STATIC_DIR = FRONTEND_DIR / "static"
REPOSITORY_ROOT = FRONTEND_DIR.parent
SRC_DIR = REPOSITORY_ROOT / "src"
AGENT_DIR = SRC_DIR / "agents" / "eu-resilience-agent"
sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(AGENT_DIR))

from azure.ai.projects import AIProjectClient  # noqa: E402
from azure.identity import DefaultAzureCredential  # noqa: E402

from functions import call_local_function  # noqa: E402


AGENT_NAME = "eu-resilience-agent"
APPROVAL_MESSAGE = (
    "Approve and open the coordination case exactly as shown in the pending "
    "decision card."
)
MAX_REQUEST_BYTES = 32_768
MAX_MESSAGE_CHARACTERS = 8_000
MAX_TOOL_ITERATIONS = 8
MAX_SESSIONS = 256
SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{16,96}$")

logger = logging.getLogger("eu_resilience_frontend")


@dataclass(slots=True)
class SessionState:
    response_id: str | None = None
    pending_approval: bool = False
    coordination_case_submitted: bool = False
    lock: Lock = field(default_factory=Lock)


sessions: dict[str, SessionState] = {}
sessions_lock = Lock()


class FrontendRequestHandler(SimpleHTTPRequestHandler):
    server_version = "CosmopilotFrontend/1.0"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self'; "
            "script-src 'self'; connect-src 'self'; base-uri 'none'; "
            "form-action 'self'; frame-ancestors 'none'",
        )
        super().end_headers()

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path == "/api/health":
            self._send_json(
                HTTPStatus.OK,
                {
                    "status": "ready",
                    "agent": AGENT_NAME,
                    "azureConfigured": bool(
                        os.environ.get("AZURE_AI_PROJECT_ENDPOINT")
                    ),
                },
            )
            return

        if path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self) -> None:
        path = urlsplit(self.path).path
        if path not in {"/api/chat", "/api/session/reset"}:
            self._send_json(
                HTTPStatus.NOT_FOUND,
                {"error": "API route not found."},
            )
            return

        origin = self.headers.get("Origin")
        if origin and urlsplit(origin).netloc != self.headers.get("Host"):
            self._send_json(
                HTTPStatus.FORBIDDEN,
                {"error": "Cross-origin requests are not allowed."},
            )
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"error": "Content-Length must be an integer."},
            )
            return

        if content_length <= 0 or content_length > MAX_REQUEST_BYTES:
            self._send_json(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                {"error": "Request body is empty or too large."},
            )
            return

        try:
            payload = json.loads(self.rfile.read(content_length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"error": "Request body must be valid JSON."},
            )
            return

        if not isinstance(payload, dict):
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"error": "Request body must be a JSON object."},
            )
            return

        if path == "/api/session/reset":
            session_id = payload.get("sessionId")
            if isinstance(session_id, str):
                with sessions_lock:
                    sessions.pop(session_id, None)
            self._send_json(HTTPStatus.OK, {"status": "reset"})
            return

        message = payload.get("message")
        if not isinstance(message, str) or not message.strip():
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"error": "message must be a non-empty string."},
            )
            return
        message = message.strip()
        if len(message) > MAX_MESSAGE_CHARACTERS:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {
                    "error": (
                        f"message cannot exceed {MAX_MESSAGE_CHARACTERS} "
                        "characters."
                    )
                },
            )
            return

        approve_coordination_case = payload.get(
            "approveCoordinationCase",
            False,
        )
        if not isinstance(approve_coordination_case, bool):
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"error": "approveCoordinationCase must be a boolean."},
            )
            return
        if approve_coordination_case and message != APPROVAL_MESSAGE:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"error": "Approval must use the explicit approval instruction."},
            )
            return

        requested_session_id = payload.get("sessionId")
        if requested_session_id is None:
            session_id = secrets.token_urlsafe(24)
        elif (
            isinstance(requested_session_id, str)
            and SESSION_ID_PATTERN.fullmatch(requested_session_id)
        ):
            session_id = requested_session_id
        else:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"error": "sessionId has an invalid format."},
            )
            return

        with sessions_lock:
            state = sessions.get(session_id)
            if state is None:
                if len(sessions) >= MAX_SESSIONS:
                    sessions.pop(next(iter(sessions)))
                state = SessionState()
                sessions[session_id] = state

        with state.lock:
            if approve_coordination_case and not state.pending_approval:
                self._send_json(
                    HTTPStatus.CONFLICT,
                    {"error": "A pending decision card is required before approval."},
                )
                return

            try:
                with (
                    DefaultAzureCredential() as credential,
                    AIProjectClient(
                        endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
                        credential=credential,
                        allow_preview=True,
                    ) as client,
                ):
                    agent = next(
                        iter(
                            client.agents.list_versions(
                                agent_name=AGENT_NAME,
                                order="desc",
                            )
                        ),
                        None,
                    )
                    if agent is None:
                        raise RuntimeError(
                            f"No version of {AGENT_NAME!r} is available."
                        )

                    openai = client.get_openai_client()
                    try:
                        agent_reference = {
                            "agent_reference": {
                                "type": "agent_reference",
                                "name": agent.name,
                                "id": agent.id,
                            }
                        }
                        request: dict[str, Any] = {
                            "input": message,
                            "extra_body": agent_reference,
                        }
                        if state.response_id:
                            request["previous_response_id"] = state.response_id
                        response = openai.responses.create(**request)
                        coordination_case_attempted = False
                        coordination_case_submitted = False

                        for _ in range(MAX_TOOL_ITERATIONS):
                            tool_outputs = []
                            for item in response.output:
                                if getattr(item, "type", None) != "function_call":
                                    continue

                                function_name = getattr(item, "name", "")
                                allow_side_effects = (
                                    function_name == "open_coordination_case"
                                    and approve_coordination_case
                                    and not coordination_case_attempted
                                )
                                if function_name == "open_coordination_case":
                                    coordination_case_attempted = True

                                function_output = call_local_function(
                                    function_name,
                                    getattr(item, "arguments", None) or "{}",
                                    allow_side_effects=allow_side_effects,
                                )
                                if allow_side_effects:
                                    try:
                                        coordination_case_submitted = (
                                            json.loads(function_output).get(
                                                "submission_status"
                                            )
                                            == "submitted"
                                        )
                                    except (AttributeError, json.JSONDecodeError):
                                        coordination_case_submitted = False
                                    if coordination_case_submitted:
                                        state.coordination_case_submitted = True
                                        state.pending_approval = False

                                tool_outputs.append(
                                    {
                                        "type": "function_call_output",
                                        "call_id": getattr(item, "call_id", ""),
                                        "output": function_output,
                                    }
                                )

                            if not tool_outputs:
                                break

                            response = openai.responses.create(
                                input=tool_outputs,
                                previous_response_id=response.id,
                                extra_body=agent_reference,
                            )
                        else:
                            raise RuntimeError(
                                "Agent exceeded the local tool iteration limit."
                            )

                        state.response_id = response.id
                        response_text = response.output_text or (
                            "The agent completed without a text response."
                        )
                        if approve_coordination_case:
                            state.coordination_case_submitted = (
                                coordination_case_submitted
                            )
                            state.pending_approval = not coordination_case_submitted
                        else:
                            state.pending_approval = bool(
                                re.search(
                                    r"decision\s+card",
                                    response_text,
                                    re.IGNORECASE,
                                )
                                and re.search(
                                    r"pending\s+approval",
                                    response_text,
                                    re.IGNORECASE,
                                )
                            )
                            if state.pending_approval:
                                state.coordination_case_submitted = False
                    finally:
                        openai.close()
            except KeyError as exc:
                logger.exception("Missing Azure environment setting")
                self._send_json(
                    HTTPStatus.SERVICE_UNAVAILABLE,
                    {"error": f"Missing required environment setting: {exc.args[0]}"},
                )
                return
            except Exception as exc:
                logger.exception("Agent request failed")
                self._send_json(
                    HTTPStatus.BAD_GATEWAY,
                    {
                        "error": "The agent request failed.",
                        "detail": str(exc)[:500],
                    },
                )
                return

        self._send_json(
            HTTPStatus.OK,
            {
                "sessionId": session_id,
                "responseId": state.response_id,
                "message": response_text,
                "pendingApproval": state.pending_approval,
                "coordinationCaseSubmitted": state.coordination_case_submitted,
            },
        )

    def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, message_format: str, *args: Any) -> None:
        logger.info("%s - %s", self.address_string(), message_format % args)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4173)
    arguments = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    )
    mimetypes.add_type("image/svg+xml", ".svg")

    server = ThreadingHTTPServer(
        (arguments.host, arguments.port),
        FrontendRequestHandler,
    )
    logger.info(
        "EU Resilience Desk available at http://%s:%d",
        arguments.host,
        arguments.port,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()