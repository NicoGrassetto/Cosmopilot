# Target domain profile

Fill this in **before** re-theming the repo. It defines the destination for the
demo so every agent, tool, dataset, and doc stays consistent. Copy this file per
audience (e.g. `domain-profile.acme.md`) or fill it in-conversation. For any
field left blank, the `adapt-demo` skill will choose a sensible default and tell
you what it assumed.

> Current (source) domain for reference: **Cosmopilot** — an AI operations
> assistant over Azure Cosmos DB operational/telemetry data, with an
> incident-triage multi-agent scenario. Replace every item below.

## 1. Brand & narrative

- **Product / brand name:** <!-- e.g. "FraudLens" — replaces "Cosmopilot" -->
- **Tagline (one line):** <!-- e.g. "Real-time fraud triage with AI + Cosmos DB" -->
- **Target audience:** <!-- who is watching? e.g. "retail-bank fraud analysts" -->
- **What they care about:** <!-- the outcome that makes them lean in -->
- **Industry / domain:** <!-- e.g. financial services, healthcare, retail, gaming -->
- **Core narrative / demo arc:** <!-- the equivalent of today's "Operate + Discover" -->

## 2. Data model

- **Primary entities:** <!-- replaces telemetry / conversations / incidents -->
- **Example record (one realistic sample document):**
  <!-- paste a small JSON example of the main entity -->
- **What "real-time change" means here:** <!-- what streams via the change feed? -->
- **What semantic/vector search returns:** <!-- what does "Discover" surface? -->

## 3. Agents (one row per pattern)

| Pattern | New agent name | Role / persona | Key instructions |
| --- | --- | --- | --- |
| Prompt agent | | | |
| Hosted agent | | | |
| Workflow | | | |
| Multi-agent (4 roles) | | | |

> The multi-agent scenario has four collaborating roles (today: detector,
> diagnostician, remediator, reporter). List the new four and what each does.

1. <!-- role 1 -->
2. <!-- role 2 -->
3. <!-- role 3 -->
4. <!-- role 4 -->

## 4. Tools

Keep interfaces stable when you can; re-theme descriptions and sample payloads.
Only rename a tool if the new domain needs a genuinely different operation.

| Tool name | Keep / rename | Purpose in new domain | Sample input | Sample output |
| --- | --- | --- | --- | --- |
| `query_cosmos_db` | | | | |
| `get_change_feed_events` | | | | |
| `code_interpreter` | keep | | | |
| <!-- new tool? --> | | | | |

## 5. Scenarios & evaluation

- **Top 3–5 example user queries** (used in sample data, frontend, eval datasets):
  1.
  2.
  3.
- **System prompt persona for the eval example agent:**
- **Ground-truth answers** for the example queries (for the eval dataset):
- **Tone / voice:** <!-- e.g. concise + data-driven, friendly, formal, playful -->

## 6. Naming (infra & resources)

| Setting | Current value | New value |
| --- | --- | --- |
| Resource base / project name | `cosmopilot` | |
| Cosmos DB account name (globally unique, lowercase, letters/numbers/hyphens) | `cosmopilot-db` | |
| SQL database name | `cosmopilot` | |
| Container name | `conversations` | |
| Partition key path | `/tenantId` | |

## 7. Out of scope (leave unchanged)

- Azure Cosmos DB + AI Foundry as the platform.
- Environment variable names, SDK calls, deployment mechanics.
- Framework structure of `/evaluations` and the four agent patterns.
- Svelte framework and build tooling.

## Assumptions log

Record any field the skill defaulted on, so the presenter can review:

- <!-- e.g. "Partition key kept as /tenantId (no per-entity key provided)." -->
