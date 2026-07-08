# Cosmopilot Agents

This directory contains four agent implementations demonstrating different Azure AI Foundry agent patterns for the Cosmopilot project.

## Agents Overview

| Agent | Type | Description |
|-------|------|-------------|
| [prompt-agent](./prompt-agent/) | Prompt (`.prompty`) | Declarative conversational assistant for operational data queries |
| [hosted-agent](./hosted-agent/) | Hosted Agent | Python agent deployed on Foundry with code interpreter & custom tools |
| [workflow](./workflow/) | Workflow (YAML) | Event-driven data enrichment pipeline referencing the prompt agent |
| [multi-agent](./multi-agent/) | MAF Multi-Agent | Incident triage system with 4 collaborating agents |

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
- Environment variables set:
  ```bash
  export AZURE_AI_PROJECT_ENDPOINT="https://<your-account>.services.ai.azure.com"
  export COSMOS_DB_ENDPOINT="https://<your-cosmosdb>.documents.azure.com:443/"
  ```

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
