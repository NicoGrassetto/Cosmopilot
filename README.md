<h1 align="center"> Cosmopilot</h1>

<p align="center">
  <img src="assets/banner.png" alt="Cosmopilot Banner" width="60%" />
</p>

<p align="center">A demo of the beautiful things we can achieve when we combine all of what Microsoft Foundry has to offer.</p>

<!-- latest-feature:start -->
> [!TIP]
> **Latest feature: Foundry project resource inspection**
>
> Cosmopilot can inspect the connections and model deployments available to a Microsoft Foundry project through the Azure AI Projects SDK. The [connection helpers](src/connections.py) support lookup by name, default-connection resolution, and filtered listing. The [deployment helpers](src/deployments.py) support lookup by name and filtering by publisher, model, or deployment type. Both use `DefaultAzureCredential` and the configured `AZURE_AI_PROJECT_ENDPOINT`.
<!-- latest-feature:end -->

<p align="center">
  <a href="LICENSE"><img alt="Open Source" src="https://img.shields.io/badge/Open%20Source-%E2%9D%A4-2ea44f" /></a>
  <a href="LICENSE"><img alt="License MIT" src="https://img.shields.io/badge/License-MIT-2ea44f" /></a>
  <a href="https://github.com/NicoGrassetto/Cosmopilot/codespaces"><img alt="Open in Codespaces" src="https://img.shields.io/badge/Open%20in-Codespaces-fb8c00?logo=github" /></a>
  <a href="https://github.com/NicoGrassetto/Cosmopilot"><img alt="GitHub stars" src="https://img.shields.io/github/stars/NicoGrassetto/Cosmopilot" /></a>
</p>

Cosmopilot is a demo showcasing Microsoft Foundry as your AI platform choice. This repo aims at covering every feature Microsoft Foundry offers (GA and Preview) in a somewhat standardised repo structure drawn from what I've observed at my customers and through the Microsoft documentation and OS IP. This does not reflect in any shape of form what YOU should be doing but merely shows you how Microsoft and other folks organise these things.

> [!WARNING]
> This project is simply a demo of Microsoft Foundry capabilities and is intended solely for exploration and validation purposes. 

---

## Project Structure

```text
Cosmopilot/
├── backend/                # FastAPI bridge to Microsoft Foundry
│   ├── app.py
│   └── requirements.txt
├── frontend/               # React application powered by Vite
│   └── src/
│       ├── components/
│       ├── api.js
│       └── App.jsx
├── src/
│   ├── agents/             # Foundry agent definitions and shared helpers
│   │   ├── eu-resilience-agent/
│   │   ├── trail-guide-agent/
│   │   ├── weather-agent/
│   │   ├── agent.py
│   │   └── routines.py
│   ├── evaluations/        # Evaluation, scheduling, and insight workflows
│   │   ├── eu-resilience-agent-evaluations/
│   │   ├── trail-guide-agent-evaluations/
│   │   └── weather-agent-evaluations/
│   └── skills.py
├── data/
│   ├── eu_resilience/
│   │   ├── datasets/       # Evaluation datasets and results
│   │   └── documents/      # Source and grounding documents
│   ├── knowledge_assistant/
│   │   ├── datasets/
│   │   └── documents/
│   ├── trail_guide/
│   │   ├── datasets/
│   │   └── documents/
│   └── weather/
│       ├── datasets/
│       └── documents/
├── docs/                   # Tool and evaluation documentation
├── infra/                  # Bicep templates and deployment scripts
├── notebooks/              # Exploratory notebooks
├── assets/                 # Documentation images
├── azure.yaml              # Azure Developer CLI configuration
└── requirements.txt        # Shared Python dependencies
```

---

## LLMOps

### Online evaluation

This repository uses the following online evaluation pipeline:

<p align="center">
  <img src="assets/online-evals.png" alt="Online evaluation pipeline" width="50%" />
</p>

User interactions are evaluated and captured in Azure Application Insights. A curation pipeline removes personally identifiable information (PII), semantically deduplicates the resulting examples, and applies additional quality checks. Selected cases enter the repository through a pull request so they can be reviewed and labeled before important production failures are promoted to the regression set. This feedback loop complements the golden, validation, and evaluation datasets and turns production signals into repeatable predeployment quality gates.

### Offline evaluation

This repository uses the following offline evaluation pipeline:

<p align="center">
  <img src="assets/offline-evals.png" alt="Offline evaluation pipeline" width="50%" />
</p>

Pull requests trigger evaluations against stable regression cases and the broader evaluation set so quality regressions can be caught before changes are merged. The golden set provides human-reviewed reference examples, while the validation set supports held-out predeployment checks. Scheduled evaluation runs exercise these datasets beyond individual code changes. In parallel, scheduled red-team runs probe adversarial behavior, and confirmed findings are retained in the safety set as repeatable safety gates.

---

## Deploy

This repository uses Azure Developer CLI to provision infrastructure only.

1. Sign in to Azure:

  ```bash
  azd auth login
  ```

2. From the repository root, provision the infrastructure:

  ```bash
  azd up
  ```

3. Follow the prompts to select an Azure subscription, name the environment, and choose the Azure AI Search region.

---

## Local Development

After infrastructure provisioning, `azd` automatically populates the root `.env` file with the deployed environment values. The generated file is ignored by Git.

Authenticate with Azure before running Azure-dependent code locally:

```bash
azd auth login
```

Python 3.10 or newer is required; Python 3.12 is recommended. Create the virtual environment and install dependencies once from the repository root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

For each new terminal session, activate the existing environment:

```bash
source .venv/bin/activate
```

Dependencies remain installed in `.venv`; reinstall them only when a requirements file changes.

### Persistent agent memory (preview)

Agent creation scripts now ensure a dedicated memory store exists before
creating the agent version. The shared
[`ensure_agent_memory_store`](src/memory_storage.py) helper reuses existing
stores, including when setup runs concurrently. It never deletes or resets
memories during agent creation.

| Agent | Memory store |
| --- | --- |
| Weather | `weather-agent-memory` |
| Trail guide | `trail-guide-agent-memory` |
| EU resilience (current and legacy setup) | `eu-resilience-agent-memory` |
| Ping-pong prompt agent | `ping-pong-agent-memory` |
| Pong-ping hosted agent | `pong-ping-hosted-agent-memory` |

Creating a new store requires `AZURE_AI_PROJECT_ENDPOINT`,
`AZURE_DEPLOYMENT_NAME` (the memory extraction chat deployment), and
`AZURE_OPENAI_EMBEDDING_DEPLOYMENT`. The infrastructure exports these values;
the setup scripts do not load `.env` automatically. For example:

```bash
azd exec -- env PYTHONPATH=src .venv/bin/python src/agents/weather-agent/create_weather_agent.py
```

The prompt agents retain their existing tools and also attach
`MemorySearchPreviewTool`, with preview access enabled and a 300-second
inactivity delay for memory updates. Their `{{$userId}}` scope resolves to the
authenticated API caller. When a backend uses a shared service identity, this
does **not** isolate that backend's end users: a multi-user application must
provide trusted per-user scoping and authorization.

The hosted LangChain sample uses `AzureAIMemoryRetrieverTool` in its
[runtime](src/agents/pong-ping-agent/main.py), rather than in the hosted
deployment definition. It retrieves existing memories; unlike the prompt-agent
tool, it does not automatically extract new memories. Populate its store with
the `create-memory` or `begin-update-memories` commands in
[`memory_storage.py`](src/memory_storage.py), using the same scope.

Before creating the hosted agent, configure `AGENT_MEMORY_SCOPE` with an
explicit, trusted user or tenant scope:

```bash
azd env set AGENT_MEMORY_SCOPE "<trusted-user-or-tenant-scope>"
azd exec -- env PYTHONPATH=src .venv/bin/python src/agents/pong-ping-agent/create-pong-ping-agent.py
```

The hosted setup passes the store name and scope into the container and bundles
the current runtime with the root pinned requirements automatically; a
prebuilt ZIP is not needed. This demo uses one configured scope per hosted
deployment, not automatic per-user routing. Do not share that scope across
users whose memories must remain separate. For a local runtime, export
`AGENT_MEMORY_STORE_NAME` and `AGENT_MEMORY_SCOPE` as shown in
[`.env.example`](.env.example).

Memory stores persist independently of agent versions. Deleting an agent does
not replace explicit memory cleanup: use `delete-scope` for a user's scoped
memories or `delete` for an entire store. Memory setup remains in the agent
creation scripts, not the infrastructure-only `azd postprovision` hook.

---


## Foundry API Notebooks

These standalone notebooks walk through every public method in their selected
preview modules from [azure-ai-projects 2.7.0](docs/azure-ai-projects.md):

| Notebook | Module | Public methods |
| --- | --- | --- |
| [Red Teaming](notebooks/red-teaming.ipynb) | `client.beta.red_teams` | 3 |
| [Routines](notebooks/routines.ipynb) | `client.beta.routines` | 8 |
| [Schedules](notebooks/schedules.ipynb) | `client.beta.schedules` | 6 |
| [Skills](notebooks/skills.ipynb) | `client.beta.skills` | 11 |
| [Voice Agents](notebooks/voice-agents.ipynb) | `client.beta.voice_agents.*` | 29, plus 16 returned realtime-object methods |
| [Memory Stores](notebooks/memory-stores.ipynb) | `client.beta.memory_stores` | 13 |

**Run All is offline by default.** Each notebook defines its walkthrough using
only the Python standard library until `RUN_LIVE_DEMO` is explicitly enabled.
Live runs require an existing kernel with `azure-ai-projects==2.7.0`,
`openai>=3.0.0`, and the notebook-specific dependencies and Azure configuration.
Voice realtime additionally requires the SDK's optional `voice` dependencies.
The [root dependency manifest](requirements.txt) records the repository's current
pins, but editing it alone does not update the selected kernel. Each notebook
checks its SDK version before live calls. No notebook installs packages, creates
an environment, or automatically loads `.env`.

Read each notebook's prerequisites and cost/consent notes before opting in.
Live examples can create billable resources, invoke models, and, with separate
Voice Agent consent, place real phone calls. Cleanup targets only resources
owned by that demo. Red-team runs are an exception: their SDK module has no
cancel/delete methods, so submitted run records persist.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

<p align="center">
  <img src="assets/overlay.png" alt="Cosmopilot Overlay" width="50%" />
</p>

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
