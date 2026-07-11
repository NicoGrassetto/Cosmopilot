"""Cosmopilot chat backend.

A thin FastAPI layer between the React frontend and Azure AI Foundry:

* ``GET  /api/agents`` — lists the agents registered in the Foundry project so the
  frontend can populate its agent selector.
* ``POST /api/chat``   — forwards a user message to a chosen agent and returns the
  agent's reply. Passing back ``response_id`` keeps a multi-turn conversation
  threaded through the Responses API.

Auth is via ``DefaultAzureCredential`` (run ``az login`` first). The only required
environment variable is ``AZURE_AI_PROJECT_ENDPOINT`` (see ``.env.example``).
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Load .env from the repo root (one level up) as well as the backend dir.
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

app = FastAPI(title="Cosmopilot Chat API", version="1.0.0")

# The Vite dev server (5173) and preview server (4173) call this API from the
# browser, so allow those origins. Adjust for production as needed.
_allowed = os.environ.get(
    "CORS_ALLOW_ORIGINS",
    "http://localhost:5173,http://localhost:4173,http://127.0.0.1:5173,http://127.0.0.1:4173",
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _allowed if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@lru_cache(maxsize=1)
def _project_client() -> AIProjectClient:
    """Build (once) the Foundry project client.

    Cached so the credential/token and underlying HTTP session are reused across
    requests instead of being rebuilt on every call.
    """
    endpoint = os.environ.get("AZURE_AI_PROJECT_ENDPOINT")
    if not endpoint:
        raise RuntimeError(
            "AZURE_AI_PROJECT_ENDPOINT is not set. Copy .env.example to .env and "
            "fill in your Foundry project endpoint, then run `az login`."
        )
    return AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())


class ChatRequest(BaseModel):
    agent: str
    message: str
    # When present, threads this turn onto a prior response for multi-turn context.
    response_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    response_id: Optional[str] = None


@app.get("/api/health")
def health() -> dict:
    """Liveness probe that also reports whether the Foundry endpoint is configured."""
    return {"status": "ok", "configured": bool(os.environ.get("AZURE_AI_PROJECT_ENDPOINT"))}


@app.get("/api/agents")
def list_agents() -> dict:
    """List the agents available in the Foundry project for the selector."""
    try:
        client = _project_client()
        agents = []
        for agent in client.agents.list():
            name = getattr(agent, "name", None)
            if not name:
                continue
            agents.append(
                {
                    "name": name,
                    "description": getattr(agent, "description", "") or "",
                    "kind": str(getattr(agent, "kind", "") or ""),
                }
            )
        # Stable alphabetical order so the dropdown doesn't reshuffle between loads.
        agents.sort(key=lambda a: a["name"].lower())
        return {"agents": agents}
    except Exception as exc:  # noqa: BLE001 - surface a clean error to the UI
        raise HTTPException(status_code=502, detail=f"Could not list agents: {exc}") from exc


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    """Send ``message`` to the named agent and return its reply."""
    if not req.agent.strip():
        raise HTTPException(status_code=400, detail="An agent must be selected.")
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        client = _project_client()
        openai_client = client.get_openai_client()

        kwargs: dict = {
            "input": req.message,
            # Route the request to a registered Foundry PromptAgent by name.
            "extra_body": {
                "agent_reference": {"type": "agent_reference", "name": req.agent}
            },
        }
        if req.response_id:
            kwargs["previous_response_id"] = req.response_id

        response = openai_client.responses.create(**kwargs)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Agent request failed: {exc}") from exc

    return ChatResponse(reply=_extract_text(response), response_id=getattr(response, "id", None))


def _extract_text(response) -> str:
    """Pull the assistant text out of a Responses API result.

    Prefers the SDK's ``output_text`` convenience property and falls back to
    walking the structured ``output`` items for older/edge shapes.
    """
    text = getattr(response, "output_text", None)
    if text:
        return text

    parts: list[str] = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            piece = getattr(content, "text", None)
            if isinstance(piece, str):
                parts.append(piece)
    return "\n".join(parts).strip() or "(no textual response)"
