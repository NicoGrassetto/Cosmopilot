from __future__ import annotations

import json
import sys
from contextlib import contextmanager
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from types import SimpleNamespace
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest


FRONTEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FRONTEND_DIR))

import server  # noqa: E402


class FakeCredential:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None


class FakeOpenAI:
    def __init__(self, responses):
        self.responses = self
        self.queued_responses = list(responses)
        self.calls = []
        self.closed = False

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.queued_responses.pop(0)

    def close(self):
        self.closed = True


class FakeProjectClient:
    def __init__(self, openai):
        self.openai = openai
        self.agents = SimpleNamespace(
            list_versions=lambda **kwargs: [
                SimpleNamespace(name=server.AGENT_NAME, id="agent-version-1")
            ]
        )

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def get_openai_client(self):
        return self.openai


@contextmanager
def running_server(monkeypatch, responses):
    openai = FakeOpenAI(responses)
    monkeypatch.setattr(server, "DefaultAzureCredential", FakeCredential)
    monkeypatch.setattr(
        server,
        "AIProjectClient",
        lambda **kwargs: FakeProjectClient(openai),
    )
    monkeypatch.setenv(
        "AZURE_AI_PROJECT_ENDPOINT",
        "https://example.test/api/projects/demo",
    )
    with server.sessions_lock:
        server.sessions.clear()

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.FrontendRequestHandler)
    thread = Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_port}", openai
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=2)


def post_json(url, payload):
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request) as response:
        return response.status, json.load(response)


def test_serves_workspace_and_health(monkeypatch):
    with running_server(monkeypatch, []) as (base_url, _):
        with urlopen(f"{base_url}/") as response:
            html = response.read().decode("utf-8")
        with urlopen(f"{base_url}/api/health") as response:
            health = json.load(response)

    assert "EU Resilience Desk" in html
    assert health == {
        "status": "ready",
        "agent": server.AGENT_NAME,
        "azureConfigured": True,
    }


def test_dispatches_local_function_and_retains_response_context(monkeypatch):
    function_calls = []
    monkeypatch.setattr(
        server,
        "call_local_function",
        lambda name, arguments, **kwargs: function_calls.append(
            (name, arguments, kwargs)
        )
        or '{"returned_country_count": 1}',
    )
    responses = [
        SimpleNamespace(
            id="response-1",
            output=[
                SimpleNamespace(
                    type="function_call",
                    name="get_resilience_priorities",
                    arguments='{"limit": 1}',
                    call_id="call-1",
                )
            ],
            output_text="",
        ),
        SimpleNamespace(
            id="response-2",
            output=[],
            output_text="Spain is the highest priority.",
        ),
        SimpleNamespace(
            id="response-3",
            output=[],
            output_text="The review remains active.",
        ),
    ]

    with running_server(monkeypatch, responses) as (base_url, openai):
        status, first = post_json(
            f"{base_url}/api/chat",
            {"message": "Rank one country"},
        )
        second_status, second = post_json(
            f"{base_url}/api/chat",
            {
                "message": "Continue the review",
                "sessionId": first["sessionId"],
            },
        )

    assert status == 200
    assert second_status == 200
    assert first["message"] == "Spain is the highest priority."
    assert second["message"] == "The review remains active."
    assert first["pendingApproval"] is False
    assert first["coordinationCaseSubmitted"] is False
    assert function_calls == [
        (
            "get_resilience_priorities",
            '{"limit": 1}',
            {"allow_side_effects": False},
        )
    ]
    assert openai.calls[1]["previous_response_id"] == "response-1"
    assert openai.calls[2]["previous_response_id"] == "response-2"
    assert openai.closed is True


def test_rejects_approval_without_existing_review(monkeypatch):
    with running_server(monkeypatch, []) as (base_url, openai):
        request = Request(
            f"{base_url}/api/chat",
            data=json.dumps(
                {
                    "message": server.APPROVAL_MESSAGE,
                    "approveCoordinationCase": True,
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with pytest.raises(HTTPError) as error:
            urlopen(request)
        payload = json.load(error.value)

    assert error.value.code == 409
    assert payload["error"] == "A pending decision card is required before approval."
    assert openai.calls == []


def test_submits_only_after_pending_decision_card(monkeypatch):
    function_calls = []
    monkeypatch.setattr(
        server,
        "call_local_function",
        lambda name, arguments, **kwargs: function_calls.append(
            (name, kwargs["allow_side_effects"])
        )
        or json.dumps(
            {
                "coordination_case_id": "EU-CRC-20260811-TEST1234",
                "submission_status": "submitted",
            }
        ),
    )
    responses = [
        SimpleNamespace(
            id="decision-response",
            output=[],
            output_text="## Decision card\n\nStatus: **Pending approval**",
        ),
        SimpleNamespace(
            id="approval-response",
            output=[
                SimpleNamespace(
                    type="function_call",
                    name="open_coordination_case",
                    arguments="{}",
                    call_id="case-call",
                )
            ],
            output_text="",
        ),
        SimpleNamespace(
            id="receipt-response",
            output=[],
            output_text="Case EU-CRC-20260811-TEST1234 submitted.",
        ),
    ]

    with running_server(monkeypatch, responses) as (base_url, _):
        _, decision = post_json(
            f"{base_url}/api/chat",
            {"message": "Prepare a decision card"},
        )
        _, receipt = post_json(
            f"{base_url}/api/chat",
            {
                "message": server.APPROVAL_MESSAGE,
                "sessionId": decision["sessionId"],
                "approveCoordinationCase": True,
            },
        )

    assert decision["pendingApproval"] is True
    assert receipt["pendingApproval"] is False
    assert receipt["coordinationCaseSubmitted"] is True
    assert function_calls == [("open_coordination_case", True)]


def test_successful_case_cannot_be_retried_when_summary_fails(monkeypatch):
    monkeypatch.setattr(
        server,
        "call_local_function",
        lambda *args, **kwargs: json.dumps(
            {
                "coordination_case_id": "EU-CRC-20260811-TEST1234",
                "submission_status": "submitted",
            }
        ),
    )
    responses = [
        SimpleNamespace(
            id="decision-response",
            output=[],
            output_text="## Decision card\n\nStatus: **Pending approval**",
        ),
        SimpleNamespace(
            id="approval-response",
            output=[
                SimpleNamespace(
                    type="function_call",
                    name="open_coordination_case",
                    arguments="{}",
                    call_id="case-call",
                )
            ],
            output_text="",
        ),
        RuntimeError("summary failed after submission"),
    ]

    with running_server(monkeypatch, responses) as (base_url, _):
        _, decision = post_json(
            f"{base_url}/api/chat",
            {"message": "Prepare a decision card"},
        )
        approval_payload = {
            "message": server.APPROVAL_MESSAGE,
            "sessionId": decision["sessionId"],
            "approveCoordinationCase": True,
        }
        with pytest.raises(HTTPError) as first_error:
            post_json(f"{base_url}/api/chat", approval_payload)
        with pytest.raises(HTTPError) as retry_error:
            post_json(f"{base_url}/api/chat", approval_payload)

    assert first_error.value.code == 502
    assert retry_error.value.code == 409