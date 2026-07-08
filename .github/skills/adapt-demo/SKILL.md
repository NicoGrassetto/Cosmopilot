---
name: adapt-demo
description: >-
  Adapt this Cosmopilot demo repository to a new demo scenario or target
  audience. Use when asked to re-theme, re-target, rebrand, or genericize the
  demo, swap the demo domain/use-case, "make the repo generic", or "change the
  agents and tools for a new audience". Keeps the Azure platform (Cosmos DB +
  AI Foundry), architecture, and deployment fixed while swapping the business
  domain across agents, tools, frontend copy, evaluation datasets, infra names,
  and docs.
license: MIT
---

# Adapt the demo to a new audience

This repository is a **reusable demo template**. It showcases a fixed technical
platform (Azure Cosmos DB + Azure AI Foundry, real-time change feed, vector
search, a Svelte frontend, and an evaluation framework) with a **business
domain layered on top**. Today that domain is "Cosmopilot" — an operations
assistant for operational/telemetry data with an incident-triage multi-agent
scenario. The evaluation framework carries a second, unrelated example domain
("Adventure Works", an outdoor-gear trail guide).

Your job when this skill runs is to **swap the business domain** for a new
target audience while leaving the platform untouched, so the demo still deploys
and runs but tells a story that resonates with the new audience.

## Core principle: separate the platform from the domain

Before changing anything, hold this split in mind. **Never** re-theme the left
column; **always** re-theme the right column.

| Fixed platform — DO NOT change | Swappable demo domain — RE-THEME |
| --- | --- |
| Azure Cosmos DB + AI Foundry as the stack | Brand / product name ("Cosmopilot") |
| Architecture: change feed, vector search, indexing | Agent personas, instructions, and roles |
| `/infra` Bicep + deploy scripts *mechanics* | Tool **semantics** and sample payloads |
| `/evaluations` framework structure & runner | Sample data, scenarios, example queries |
| Agent **patterns** (prompt / hosted / workflow / multi-agent) | Frontend copy (greetings, placeholders) |
| Frontend framework (Svelte), build tooling | Eval datasets, ground truth, system prompts |
| Language/SDK choices, file layout | Azure resource **names** (`cosmopilot-db`, etc.) |
| Env var **names** (`AZURE_AI_PROJECT_ENDPOINT`, …) | Docs narrative (README, ROADMAP, FAQ) |

Keep tool **interfaces** (function names, parameter shapes) stable unless the
new domain genuinely needs different operations — a stable interface keeps the
frontend and workflow wiring working. Re-theme the tool *descriptions* and
*sample data* instead. If a tool name is domain-loaded (e.g. an incident-only
tool), rename it, but update every reference.

## Process

Follow these steps in order. Prefer making a plan and tracking each area as a
todo so nothing is missed.

### Step 1 — Capture the target domain profile

You cannot re-theme consistently without knowing the destination. Read
`domain-profile.template.md` in this skill directory. Fill it in from the
user's request; for anything unspecified, propose sensible defaults and state
your assumptions rather than blocking. If the audience/use-case is completely
unspecified, ask the user one focused question to get the domain, then proceed.

At minimum you must pin down:

- **Product / brand name** (replaces "Cosmopilot") and a one-line tagline.
- **Target audience** — who watches this demo, and what they care about.
- **Domain / industry** and the **core narrative** (the equivalent of today's
  "Operate + Discover").
- **Primary data entities** (replaces telemetry/conversations/incidents).
- **Agent roles** for each of the four patterns and their instructions.
- **Tool set** — names, purposes, and realistic sample payloads over the new
  entities.
- **Example scenarios / queries** used in sample data and eval datasets.
- **Naming** — Azure resource base name, database name, container name,
  partition key path.

### Step 2 — Inventory the current domain content

Get a precise map of everything domain-coupled before editing. Run the helper
script (it prints every file + line that mentions a known domain token):

```bash
python .github/skills/adapt-demo/inventory-domain.py
```

Pass extra tokens for the *current* domain if you have added any:
`python .github/skills/adapt-demo/inventory-domain.py --extra "myoldbrand" "myoldterm"`.

If Python is unavailable, fall back to searching the repo yourself for:
`cosmopilot`, `Cosmos DB`, `telemetry`, `operational`, `incident`, `anomaly`,
`change feed`, `adventure works`, `trail guide`.

Cross-check the inventory against the file map below so you do not miss a
location the token search cannot infer (e.g. generic greetings in the frontend).

### Step 3 — Genericize (establish the swap points)

Make the domain a clean, swappable layer rather than assumptions scattered in
prose. For each domain-coupled file, identify the exact strings that encode the
*old* domain (names, personas, entities, sample data, copy). This is the "make
the repo generic" step: you are isolating what varies per audience from what is
structural. Do not delete structure, wiring, or platform config — only the
domain content is in scope. Keep the four agent patterns and the eval framework
intact.

### Step 4 — Apply the new domain

Work area by area using the **File map** below. For each area:

1. Replace the brand/product name and taglines.
2. Rewrite agent instructions/personas for the new roles.
3. Re-theme tool descriptions and regenerate realistic sample payloads over the
   new entities (keep interfaces stable unless a rename is justified).
4. Update sample scenarios, eval datasets, and system prompts to the new domain.
5. Update frontend copy (greeting, placeholder text, demo responses).
6. Update infra resource names and docs narrative.

Be internally consistent: the same brand name, entity vocabulary, and tone must
appear everywhere. A viewer should never see a leftover reference to the old
domain.

### Step 5 — Validate

- Re-run the inventory script; confirm **no** stale references to the *old*
  domain remain (only intentional platform terms like real Azure service names
  should stay).
- Keep it runnable: preserve valid YAML/JSON/Python/Svelte. Where the repo has
  build/lint/test (e.g. `frontend` has `npm` scripts; `evaluations` has
  `pyproject.toml`), run them to confirm you did not break structure.
- Confirm Azure resource names still satisfy their constraints (Cosmos DB
  account name must be globally unique, lowercase, letters/numbers/hyphens).
- Summarize what changed per area and restate any assumptions you made.

## File map — what to change per area

Run the inventory script for exact line numbers; this table is the authoritative
list of *where the domain lives*.

### Agents (`/agents`) — the heart of the re-theme
- `prompt-agent/cosmopilot-assistant.prompty` — rename file + `name`/`description`,
  rewrite the `system:` persona, default inputs, and example query.
- `hosted-agent/agent.py` + `agent.manifest.yaml` — agent `name`, `instructions`,
  and the function tools (`query_cosmos_db`, `get_change_feed_events`): keep the
  query interface, re-theme descriptions/defaults; rename container defaults.
- `multi-agent/agents.yaml` + `orchestrator.py` — the four roles (detector,
  diagnostician, remediator, reporter) and their instructions/tools, plus the
  sample telemetry payload in `orchestrator.py`'s `main()`.
- `workflow/data-enrichment.yaml` — trigger container/database names,
  classification categories, and the enrichment prompt.
- `README.md` — the agents overview table, architecture diagram labels, and
  run examples.

### Frontend (`/frontend`)
- `src/components/Chatbot.svelte` — the initial greeting message and the demo
  bot response copy. Optionally the input placeholder in `InputBox.svelte`.
- `README.md` — any product naming.
- Keep the Svelte framework, build config, and component structure unchanged.

### Evaluations (`/evaluations`)
- `adventure-works-agent/` (agent code, `prompts/*.txt`) and
  `datasets/per_agent/adventure-works.jsonl` — the concrete example domain.
  Re-theme these to the new domain (rename the folder/dataset to match the new
  agent), or add a new per-agent folder + dataset alongside.
- `README.md`, `runner.py` — example `--agent` names in usage snippets.
- Keep `evals/`, `simulators/`, `redteam/`, `config/` framework code intact
  (only values/prompts change, not the framework).

### Infra (`/infra`)
- `main.parameters.json` — `cosmosAccountName`, `sqlDatabaseName`,
  `containerName`, `projectName`, and `partitionKeyPath` if the entity changes.
- `main.bicep` / `main.json` — default naming only; keep resource definitions.
- `deploy.ps1` / `deploy.sh` / `README.md` — prompt defaults and product name.
- Do **not** change resource types, SKUs, or wiring.

### Docs (root)
- `README.md` (heaviest), `ROADMAP.md`, `FAQ.md`, `CHANGELOG.md`, `AUTHORS.md`,
  `SUPPORT.md`, `SECURITY.md`, `ARCHITECTURE.md`, `CONTRIBUTING.md` — product
  name, tagline, use-case narrative, and any domain examples. Preserve
  deployment steps and platform facts.
- `assets/` images (banner/overlay) are branded; note if they should be
  regenerated, but do not fabricate binary assets.

## Guidelines

- **Platform stays, domain changes.** If unsure whether something is platform or
  domain, treat env var names, Azure service names, SDK calls, and file/dir
  structure as platform (keep them).
- **Consistency over cleverness.** One brand name, one entity vocabulary, one
  tone, everywhere.
- **Keep it deployable and runnable.** Never leave invalid config or broken
  wiring. Validate before finishing.
- **Prefer stable interfaces.** Re-theme tool descriptions and sample data; only
  rename tools/params when the new domain truly requires different operations,
  and then update every reference.
- **State assumptions.** In autonomous runs, choose sensible defaults for any
  unfilled profile field and report them rather than stalling.
- **Reversible and repeatable.** This skill should work for the *next* audience
  too — keep the platform/domain separation clean so the swap can happen again.

## Resources in this skill

- `domain-profile.template.md` — the fill-in profile that defines a target
  audience/domain. Complete it in Step 1.
- `inventory-domain.py` — prints every file/line carrying a known domain token,
  so nothing is missed in Steps 2 and 5.
