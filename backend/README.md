# Cosmopilot Chat Backend

A small [FastAPI](https://fastapi.tiangolo.com/) service that bridges the React
frontend and Azure AI Foundry. It lists the agents in your Foundry project and
proxies chat messages to whichever agent the user selects.

## Endpoints

| Method | Path           | Purpose                                              |
| ------ | -------------- | ---------------------------------------------------- |
| `GET`  | `/api/health`  | Liveness + whether the Foundry endpoint is set.      |
| `GET`  | `/api/agents`  | Lists Foundry agents (name, description, kind).       |
| `POST` | `/api/chat`    | Sends a message to an agent, returns its reply.       |

`POST /api/chat` body:

```json
{ "agent": "knowledge-assistant", "message": "Hello", "response_id": null }
```

The response includes a `response_id`; send it back on the next turn to keep the
conversation threaded (multi-turn context via the Responses API).

## Setup

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # optional but recommended
pip install -r requirements.txt
```

Auth uses `DefaultAzureCredential`, so sign in first:

```bash
az login
```

Set `AZURE_AI_PROJECT_ENDPOINT` (copy the repo-root `.env.example` to `.env`).
The backend loads `.env` from both the repo root and the `backend/` directory.

## Run

```bash
uvicorn app:app --reload --port 8000
```

Then start the frontend (`cd ../frontend && npm run dev`). The Vite dev server
proxies `/api/*` to `http://localhost:8000`.
