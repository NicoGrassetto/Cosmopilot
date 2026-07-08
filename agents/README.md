# Cosmopilot Agents

This directory contains four agent implementations demonstrating different Azure AI Foundry agent patterns for the Cosmopilot project, plus a shared [`skills/`](./skills/) primitive that several of them reuse.

## Agents Overview

| Agent | Type | Description |
|-------|------|-------------|
| [prompt-agent](./prompt-agent/) | Prompt (`.prompty`) | Declarative conversational assistant for operational data queries |
| [hosted-agent](./hosted-agent/) | Hosted Agent | Python agent deployed on Foundry with code interpreter & custom tools |
| [workflow](./workflow/) | Workflow (YAML) | Event-driven data enrichment pipeline referencing the prompt agent |
| [multi-agent](./multi-agent/) | MAF Multi-Agent | Incident triage system with 4 collaborating agents |

## Skills (shared behavioral primitive)

Beyond the four agent patterns, [`skills/`](./skills/) holds **Foundry skills** —
versioned [`SKILL.md`](https://agentskills.io) behavioral guidelines (escalation
policy, query standards, output formats) that several agents share instead of
duplicating the same rules in each prompt. Author a skill once, provision it to
your Foundry project through the versioned Skills API, and update it without
redeploying any agent.

| Skill | Purpose | Used by |
|-------|---------|---------|
| `incident-triage-policy` | Severity thresholds, escalation + human-approval gates | multi-agent |
| `cosmos-query-standards` | Safe, cost-aware Cosmos DB query conventions | hosted-agent, multi-agent |
| `change-feed-summary-format` | Canonical event classification / summary format | workflow, hosted-agent, multi-agent |

Skills reach agents two ways: **toolbox (MCP) discovery** for prompt/multi-agent
and external MCP clients, or **direct injection** for the hosted agent (it
appends the skill bodies to its instructions at startup — see
[`hosted-agent/skills.py`](./hosted-agent/skills.py)). Full authoring,
provisioning, and versioning guidance is in [`skills/README.md`](./skills/README.md).

These are distinct from the dev-time GitHub Copilot skills in `.github/skills/`,
even though both use the same `SKILL.md` format.

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

### Provision the shared skills

```bash
cd agents/skills
pip install azure-ai-projects azure-identity
python provision_skills.py --toolbox cosmopilot
```

Uploads each `SKILL.md` to your Foundry project as a versioned skill and
references them from a `cosmopilot` toolbox. See [`skills/README.md`](./skills/README.md).

## Workflow Details

The **data-enrichment workflow** (`workflow/data-enrichment.yaml`) is triggered by Cosmos DB change feed events and:

1. **Classifies** the event using the prompt agent (category + severity)
2. **Embeds** the event summary into a vector
3. **Writes** the enriched document back to Cosmos DB
4. **Alerts** on critical-severity events

It references the prompt agent at `../prompt-agent/cosmopilot-assistant.prompty`.
