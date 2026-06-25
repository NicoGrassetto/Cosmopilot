<h1 align="center">🤖 Cosmopilot</h1>

<p align="center">
  <img src="assets/banner.png" alt="Cosmopilot Banner" width="100%" />
</p>

<p align="center">AI-powered chatbot with real-time operational data and voice capabilities.</p>

<p align="center">
  <a href="LICENSE"><img alt="Open Source" src="https://img.shields.io/badge/Open%20Source-%E2%9D%A4-2ea44f" /></a>
  <a href="https://github.com/NicoGrassetto/Cosmopilot"><img alt="GitHub stars" src="https://img.shields.io/github/stars/NicoGrassetto/Cosmopilot" /></a>
</p>

Cosmopilot is a conversational AI application that combines Azure Cosmos DB for real-time operational data storage with Microsoft Foundry for fast inference and embeddings. It features a lightweight frontend built with Svelte, real-time message synchronization via Cosmos DB change feeds, and integrated voice capabilities.

## 🚀 Get started

### Prerequisites

- Azure subscription with quotas for Cosmos DB and AI Foundry
- Azure CLI installed and authenticated
- Node.js 18+ for frontend development

### Deploy Infrastructure

1. Review infrastructure in [infra/main.bicep](infra/main.bicep).
2. Configure deployment values (prompted by script or edit [infra/main.parameters.json](infra/main.parameters.json)).
3. Run deployment:
   ```bash
   cd infra
   ./deploy.sh
   ```

### Run Frontend

1. Install dependencies: `cd frontend && npm install`
2. Start dev server: `npm run dev`
3. Open browser to `http://localhost:5173`

## 📦 What's in this repository

| Directory | What it is |
| --- | --- |
| `infra/` | Bicep infrastructure-as-code for Cosmos DB and AI Foundry Project provisioning. |
| `frontend/` | Svelte + Vite frontend application for the chatbot UI. |
| `src/` | Core backend logic (indexing functions, change feed processors). |
| `tests/` | Test suite for backend and integration testing. |
| `docs/` | Architecture documentation and design decisions. |
| `assets/` | Images and media files. |

## 🏗️ Architecture

- **Cosmos DB (SQL API):** Stores conversation history, sessions, and operational data with real-time change feed.
- **AI Foundry Project:** Manages model deployments (GPT-4o Nano for inference, text-embedding-3-nano for embeddings).
- **Frontend:** Svelte application that connects directly to backend APIs (no traditional backend server).
- **Indexing:** Change feed processor listens to Cosmos DB mutations and calls embedding model for semantic search.
- **Voice:** Speech-to-text and text-to-speech integration (planned).

## 🛠️ Key Features

- ✅ Real-time chat with Cosmos DB synchronization
- ✅ Semantic search via embeddings (text-embedding-3-nano)
- ✅ Fast inference (GPT-4o Nano)
- ✅ Change feed-based indexing pipeline
- ✅ Multi-tenant support (partition by tenantId)
- 🚧 Voice capabilities (speech-to-text, text-to-speech)
- 🚧 Evaluations framework

## 📋 Development

- **Editor:** Helix + Zellij for terminal-native development
- **Build:** `npm run build` (frontend), Bicep validation via Azure CLI
- **Test:** `npm run test` (frontend tests, backend integration tests)

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

![Cosmopilot Overlay](assets/overlay.png)

<!-- COMMENTED OUT - Original notes:
# Cosmopilot

- Conversation history and sessions stored in Cosmos DB
- Operational data in Cosmos DB
- Vectors in Cosmos DB

- Microsoft Foundry + fast model + fast embedding
- Feed in realtime changes
- Use change feed

Use Helix + Zellij + opencode and a lightweight and fast model

/infra (Cosmos DB + make sure the IP bs is disabled, etc etc)

front-end in /frontend

Use-case operational data

/src

/tests

/docs

/.github


No backend except for indexing 

frontend connects direclty to backend( TS)

indexing is handled by a function in the change feed. python or js or whatever

https://github.com/copilotkit/copilotkit

Add voice to it 

(Speech to text and text to speech)
In the agent add a way to vibe code operational data for cosmos db (via a script to bootstrap it) similarly should change the script that creates realtime operational data.
Repo should be empty (no opeorational data)

Nano or mini model

diskANN for faster ops

Add evals set

Complete demo of "Operate" + "Discover"
-->
