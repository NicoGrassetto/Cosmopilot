# Cosmopilot Frontend

A **React** (Vite) chat interface for talking to your Azure AI Foundry agents.

## Features

- 💬 **Chat area** — threaded conversation with user/agent bubbles, typing
  indicator, and inline error messages.
- 🧠 **Agent selector** — dropdown populated live from your Foundry project; each
  agent keeps its own conversation thread (multi-turn context).
- 🎨 Gradient UI, responsive layout, no heavy UI libraries.

## Stack

HTML + CSS + JavaScript + **React 18** + **Vite**.

## Prerequisites

The [backend](../backend/README.md) must be running (default
`http://localhost:8000`). The Vite dev server proxies `/api/*` to it.

## Setup & run

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

### Configuration

- `VITE_API_TARGET` — backend URL the dev server proxies to (default
  `http://localhost:8000`).
- `VITE_API_BASE` — absolute API base if you serve the built app without the Vite
  proxy (e.g. `https://api.example.com`). Leave unset to use same-origin `/api`.

## Build

```bash
npm run build     # outputs to dist/
npm run preview   # serve the production build
```

## Project structure

```
frontend/
├── index.html
├── vite.config.js            # React plugin + /api proxy to the backend
├── src/
│   ├── main.jsx
│   ├── App.jsx               # chat state, agent threads, orchestration
│   ├── api.js                # fetch helpers for /api/agents and /api/chat
│   ├── index.css
│   └── components/
│       ├── AgentSelector.jsx
│       ├── MessageBubble.jsx
│       ├── InputBox.jsx
│       └── TypingIndicator.jsx
```
