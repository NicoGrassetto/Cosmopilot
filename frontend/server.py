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
from typing import Any, Callable
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

from functions import (  # noqa: E402
    GeneratedDocument,
    call_local_function,
    get_generated_document,
)


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
DOCUMENT_PATH_PATTERN = re.compile(r"^/api/documents/([0-9a-f]{32})$")
DOCUMENT_MARKDOWN_LINK_PATTERN = re.compile(
    r"\[([^\]]+)\]\([^)\r\n]*/api/documents/[0-9a-f]{32}\)",
    re.IGNORECASE,
)
DOCUMENT_RAW_LINK_PATTERN = re.compile(
    r"(?:[a-z][a-z0-9+.-]*:)?[^\s)\]]*/api/documents/[0-9a-f]{32}",
    re.IGNORECASE,
)
TOOL_ACTIVITY = {
    "get_resilience_priorities": (
        "Reading the EU27 priority scorecard",
        "Priority ranking loaded",
    ),
    "get_country_resilience_evidence": (
        "Joining the country evidence package",
        "Country evidence package loaded",
    ),
    "generate_resilience_report": (
        "Building the DOCX briefing and chart pack",
        "Document and charts generated",
    ),
    "evaluate_coordination_playbook": (
        "Evaluating the coordination playbook",
        "Coordination criteria evaluated",
    ),
    "open_coordination_case": (
        "Submitting the approved coordination case",
        "Coordination case submission completed",
    ),
}

logger = logging.getLogger("eu_resilience_frontend")


@dataclass(slots=True)
class SessionState:
    response_id: str | None = None
    pending_approval: bool = False
    coordination_case_submitted: bool = False
    lock: Lock = field(default_factory=Lock)


sessions: dict[str, SessionState] = {}
sessions_lock = Lock()


def _public_document_metadata(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None

    document_id = payload.get("id")
    download_url = payload.get("download_url")
    if (
        not isinstance(document_id, str)
        or not DOCUMENT_PATH_PATTERN.fullmatch(
            f"/api/documents/{document_id}"
        )
        or download_url != f"/api/documents/{document_id}"
    ):
        return None

    string_fields = {
        "title": "title",
        "fileName": "file_name",
        "contentType": "content_type",
        "scope": "scope",
        "generatedAt": "generated_at",
        "snapshotDate": "snapshot_date",
    }
    result: dict[str, Any] = {
        "id": document_id,
        "downloadUrl": download_url,
    }
    for public_name, source_name in string_fields.items():
        value = payload.get(source_name)
        if isinstance(value, str):
            result[public_name] = value
    chart_count = payload.get("chart_count")
    if isinstance(chart_count, int) and not isinstance(chart_count, bool):
        result["chartCount"] = chart_count
    return result


def _remove_generated_document_links(response_text: str) -> str:
    response_text = DOCUMENT_MARKDOWN_LINK_PATTERN.sub(
        r"\1 (use the download card below)",
        response_text,
    )
    response_text = DOCUMENT_RAW_LINK_PATTERN.sub(
        "the download card below",
        response_text,
    )
    response_text = re.sub(
        r"\bdownload link below\b",
        "download card below",
        response_text,
        flags=re.IGNORECASE,
    )
    return re.sub(
        r"\blink below\b",
        "download card below",
        response_text,
        flags=re.IGNORECASE,
    )


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

        document_match = DOCUMENT_PATH_PATTERN.fullmatch(path)
        if document_match:
            document = get_generated_document(document_match.group(1))
            if document is None:
                self._send_json(
                    HTTPStatus.NOT_FOUND,
                    {"error": "Generated document not found or expired."},
                )
                return
            self._send_document(document)
            return

        if path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self) -> None:
        path = urlsplit(self.path).path
        if path not in {
            "/api/chat",
            "/api/chat/stream",
            "/api/session/reset",
        }:
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

            streaming = path == "/api/chat/stream"
            emit: Callable[[dict[str, Any]], None] = (
                self._send_stream_event if streaming else lambda event: None
            )
            documents: list[dict[str, Any]] = []

            try:
                if streaming:
                    self._begin_event_stream()
                    emit(
                        {
                            "type": "status",
                            "stage": "connecting",
                            "message": "Connecting to the EU resilience agent",
                        }
                    )
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
                    emit(
                        {
                            "type": "status",
                            "stage": "agent_ready",
                            "message": "Agent ready; reviewing the request",
                        }
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
                        emit(
                            {
                                "type": "status",
                                "stage": "reasoning",
                                "message": "Selecting the governed evidence workflow",
                            }
                        )
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

                                activity = TOOL_ACTIVITY.get(
                                    function_name,
                                    (
                                        "Running a governed data operation",
                                        "Governed data operation completed",
                                    ),
                                )
                                emit(
                                    {
                                        "type": "tool_start",
                                        "tool": function_name,
                                        "message": activity[0],
                                    }
                                )
                                function_output = call_local_function(
                                    function_name,
                                    getattr(item, "arguments", None) or "{}",
                                    allow_side_effects=allow_side_effects,
                                )
                                try:
                                    output_payload = json.loads(function_output)
                                except json.JSONDecodeError:
                                    output_payload = {}
                                if not isinstance(output_payload, dict):
                                    output_payload = {}

                                if allow_side_effects:
                                    coordination_case_submitted = (
                                        output_payload.get("submission_status")
                                        == "submitted"
                                    )
                                    if coordination_case_submitted:
                                        state.coordination_case_submitted = True
                                        state.pending_approval = False

                                document = _public_document_metadata(
                                    output_payload.get("document")
                                )
                                if document is not None and not any(
                                    existing["id"] == document["id"]
                                    for existing in documents
                                ):
                                    documents.append(document)
                                    emit(
                                        {
                                            "type": "document",
                                            "message": "Downloadable DOCX briefing ready",
                                            "document": document,
                                        }
                                    )

                                emit(
                                    {
                                        "type": "tool_complete",
                                        "tool": function_name,
                                        "message": (
                                            f"{activity[1]} with an error"
                                            if output_payload.get("error")
                                            else activity[1]
                                        ),
                                        "success": not bool(
                                            output_payload.get("error")
                                        ),
                                    }
                                )
                                tool_outputs.append(
                                    {
                                        "type": "function_call_output",
                                        "call_id": getattr(item, "call_id", ""),
                                        "output": function_output,
                                    }
                                )

                            if not tool_outputs:
                                emit(
                                    {
                                        "type": "status",
                                        "stage": "finalizing",
                                        "message": "Preparing the executive response",
                                    }
                                )
                                break

                            emit(
                                {
                                    "type": "status",
                                    "stage": "reasoning",
                                    "message": "Integrating the governed tool results",
                                }
                            )
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
                        if documents:
                            response_text = _remove_generated_document_links(
                                response_text
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
            except (BrokenPipeError, ConnectionResetError):
                logger.info("Client disconnected from the agent event stream")
                return
            except KeyError as exc:
                logger.exception("Missing Azure environment setting")
                self._send_agent_error(
                    streaming,
                    HTTPStatus.SERVICE_UNAVAILABLE,
                    {"error": f"Missing required environment setting: {exc.args[0]}"},
                )
                return
            except Exception as exc:
                logger.exception("Agent request failed")
                self._send_agent_error(
                    streaming,
                    HTTPStatus.BAD_GATEWAY,
                    {
                        "error": "The agent request failed.",
                        "detail": str(exc)[:500],
                    },
                )
                return

            response_id = state.response_id
            pending_approval = state.pending_approval
            case_submitted = state.coordination_case_submitted

        result = {
            "sessionId": session_id,
            "responseId": response_id,
            "message": response_text,
            "pendingApproval": pending_approval,
            "coordinationCaseSubmitted": case_submitted,
            "documents": documents,
        }
        if streaming:
            self._send_stream_event({"type": "result", **result})
        else:
            self._send_json(HTTPStatus.OK, result)

    def _begin_event_stream(self) -> None:
        self.send_response(HTTPStatus.OK.value)
        self.send_header(
            "Content-Type",
            "application/x-ndjson; charset=utf-8",
        )
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Accel-Buffering", "no")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True

    def _send_stream_event(self, payload: dict[str, Any]) -> None:
        body = (
            json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
            + "\n"
        ).encode("utf-8")
        self.wfile.write(body)
        self.wfile.flush()

    def _send_agent_error(
        self,
        streaming: bool,
        status: HTTPStatus,
        payload: dict[str, Any],
    ) -> None:
        if streaming:
            self._send_stream_event({"type": "error", **payload})
        else:
            self._send_json(status, payload)

    def _send_document(self, document: GeneratedDocument) -> None:
        try:
            stream = document.path.open("rb")
        except OSError:
            self._send_json(
                HTTPStatus.NOT_FOUND,
                {"error": "Generated document not found or expired."},
            )
            return

        with stream:
            size = os.fstat(stream.fileno()).st_size
            self.send_response(HTTPStatus.OK.value)
            self.send_header("Content-Type", document.content_type)
            self.send_header("Content-Length", str(size))
            self.send_header(
                "Content-Disposition",
                f'attachment; filename="{document.file_name}"',
            )
            self.send_header("Cache-Control", "private, no-store")
            self.end_headers()
            while chunk := stream.read(64 * 1024):
                self.wfile.write(chunk)

    def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, message_format: str, *args: Any) -> None:
        message = message_format % args
        message = re.sub(
            r"/api/documents/[0-9a-f]{32}",
            "/api/documents/<redacted>",
            message,
        )
        logger.info("%s - %s", self.address_string(), message)


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