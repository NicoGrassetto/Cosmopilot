# Cosmopilot Agents

This directory contains four agent implementations demonstrating different Azure AI Foundry agent patterns for the Cosmopilot project.

## Agents Overview

| Agent | Type | Description |
|-------|------|-------------|
| [prompt-agent](./prompt-agent/) | Prompt (`.prompty`) | Declarative conversational assistant for operational data queries |
| [hosted-agent](./hosted-agent/) | Hosted Agent | Python agent deployed on Foundry with code interpreter & custom tools |
| [workflow](./workflow/) | Workflow (YAML) | Event-driven data enrichment pipeline referencing the prompt agent |
| [multi-agent](./multi-agent/) | MAF Multi-Agent | Incident triage system with 4 collaborating agents |

> All agents share their tool definitions from [`_shared/`](./_shared/) — see below.

## Shared tools (DRY)

Tools are declared **once** in [`_shared/`](./_shared/) and reused across every
agent, instead of being re-declared per agent:

```python
from _shared import tools

tools=tools("code_interpreter", "query_cosmos_db", "get_change_feed_events")
```

- **Python agents** (`hosted-agent`, `multi-agent`) import `tools(*names)` — the
  single source of truth for each tool's JSON schema and implementation.
- **All agent styles** (including `prompt-agent` and `workflow`, which can't
  import Python) can share the same tools through a **Foundry Toolbox**: the
  `cosmos-mcp` server in `_shared/` exposes the Cosmos tools over MCP, and
  `_shared/toolbox.yaml` bundles them with `code_interpreter` behind one
  `TOOLBOX_ENDPOINT`.

Run the tool tests with `python -m unittest discover -s agents/_shared/tests`.
Full details in [`_shared/README.md`](./_shared/README.md).

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Cosmos DB Change Feed                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │   Workflow (YAML)       │
              │   data-enrichment      │
              │                        │
              │  ┌──────────────────┐  │
              │  │  Prompt Agent    │  │  ← classifies events
              │  │  (cosmopilot-    │  │
              │  │   assistant)     │  │
              │  └──────────────────┘  │
              └────────────┬───────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │   Hosted Agent         │  ← interactive data analysis
              │   (data-insights)      │
              └────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │   MAF Multi-Agent      │  ← incident triage
              │   ┌────┐ ┌────┐       │
              │   │Det.│→│Diag│       │
              │   └────┘ └────┘       │
              │       ↓       ↓       │
              │   ┌────┐ ┌────┐       │
              │   │Rem.│→│Rep.│       │
              │   └────┘ └────┘       │
              └────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Azure CLI authenticated (`az login`)
- Azure AI Foundry project provisioned (see `/infra`)
- Environment variables set — copy the repo-root [`.env.example`](../.env.example)
  to `.env` and fill in the placeholders:
  ```bash
  cp .env.example .env          # macOS / Linux
  Copy-Item .env.example .env   # Windows PowerShell
  ```
  At minimum set `AZURE_AI_PROJECT_ENDPOINT` and `COSMOS_DB_ENDPOINT`; the file
  documents every variable each agent and tool uses.

### Run the Prompt Agent

```bash
pip install prompty
prompty run agents/prompt-agent/cosmopilot-assistant.prompty \
  --input user_query="What errors occurred in the last hour?"
```

### Run the Hosted Agent

```bash
cd agents/hosted-agent
pip install -r requirements.txt
python agent.py
```

### Run the Multi-Agent Scenario

```bash
cd agents/multi-agent
pip install -r requirements.txt
python orchestrator.py
```

## Workflow Details

The **data-enrichment workflow** (`workflow/data-enrichment.yaml`) is triggered by Cosmos DB change feed events and:

1. **Classifies** the event using the prompt agent (category + severity)
2. **Embeds** the event summary into a vector
3. **Writes** the enriched document back to Cosmos DB
4. **Alerts** on critical-severity events

It references the prompt agent at `../prompt-agent/cosmopilot-assistant.prompty`.
