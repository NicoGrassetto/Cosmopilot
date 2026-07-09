# Cosmopilot Skills

**Skills** are reusable *behavioral guidelines* — escalation policies, query
standards, output formats — that you author once and share across agents,
instead of copy-pasting the same rules into every agent's prompt or code. In
Microsoft Foundry a skill is a [`SKILL.md`](https://agentskills.io) file
(Markdown + YAML front matter) stored centrally through the **versioned Skills
API**. Update a skill once, promote the new version, and every agent that
references it picks up the change with **no redeploy**.

> Reference: [Use skills with Microsoft Foundry agents (preview)](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/skills)

## Not the same as `.github/skills/`

| `.github/skills/` | `agents/skills/` (this folder) |
| --- | --- |
| **Dev-time** GitHub Copilot skills | **Runtime** skills for the deployed Foundry agents |
| Help *you build/adapt* the demo | Configure how the demo's agents *behave* |

The file format is identical (both follow the agentskills.io spec), but the two
serve different audiences. Keep runtime skills here.

## Layout

Each skill lives in its own subdirectory, and the directory name **must** equal
the `name` in the front matter (lowercase letters, numbers, hyphens; ≤ 64 chars):

```
agents/skills/
├── incident-triage-policy/     severity thresholds, escalation, approval gates
│   └── SKILL.md
├── cosmos-query-standards/     safe, cost-aware Cosmos DB query conventions
│   └── SKILL.md
├── change-feed-summary-format/ canonical event classification/summary format
│   └── SKILL.md
├── provision_skills.py         upload sources to Foundry + reference from a toolbox
└── README.md
```

`SKILL.md` front matter rules: `name` and `description` must be **unquoted**;
`description` ≤ 1024 chars; the Markdown body becomes the injected instructions.
A skill directory may also carry sibling asset files (reference docs) that ship
in the same package and are read on demand.

## Which agent uses which skill, and how

Skills reach agents two ways. This repo uses both:

| Delivery mode | How it works | Cosmopilot consumers |
| --- | --- | --- |
| **Toolbox (MCP)** | Skills are referenced from a toolbox version; any MCP client discovers them via MCP Resources alongside tools | `prompt-agent`, `multi-agent`, and external MCP clients (GitHub Copilot, Claude Code) |
| **Direct injection** | The agent downloads / bundles `SKILL.md` and appends the body to its own instructions at startup | `hosted-agent` (see `../hosted-agent/skills.py`) |

Mapping of skills to agents:

| Skill | Consumed by |
| --- | --- |
| `incident-triage-policy` | multi-agent detector / diagnostician / remediator / reporter |
| `cosmos-query-standards` | hosted-agent, multi-agent detector |
| `change-feed-summary-format` | workflow classifier, hosted-agent, multi-agent reporter |

## Provision skills into Foundry

Skills are a **data-plane** artifact (the Skills API), not infrastructure — so
they are created *after* `infra/` is deployed, not in `main.bicep`. Git stays the
source of truth; Foundry mirrors each version.

```bash
cd agents/skills
pip install azure-ai-projects azure-identity
az login
export AZURE_AI_PROJECT_ENDPOINT="https://<account>.services.ai.azure.com/api/projects/<project>"

python provision_skills.py                       # upload + promote every skill
python provision_skills.py --toolbox cosmopilot  # ...and reference them from a toolbox
python provision_skills.py --list                # list skills already in the project
```

Equivalent one-off commands with the Azure Developer CLI Foundry extension:

```bash
azd ai skill create incident-triage-policy --file ./incident-triage-policy/SKILL.md --no-prompt
azd ai skill update incident-triage-policy --file ./incident-triage-policy/SKILL.md --no-prompt  # new version, auto-promoted
azd ai skill list -o table
```

## Consume skills in the hosted agent

`../hosted-agent/skills.py` resolves skills and returns their bodies so
`agent.py` can append them to its instructions. Pick the source with an env var:

```bash
# Default: read the bundled SKILL.md sources in this folder (offline).
FOUNDRY_SKILLS_SOURCE=local

# Or pull the active version from Foundry at startup.
FOUNDRY_SKILLS_SOURCE=foundry
```

## Update flow (no redeploy)

1. Edit the `SKILL.md` body.
2. Re-run `python provision_skills.py` (or `azd ai skill update <name> --file ...`).
   Each run creates a new **immutable** version and promotes it to `default_version`.
3. Toolbox references and agents that don't pin a version pick up the new default
   automatically. Roll back anytime with `azd ai skill update <name> --set-default-version <v>`.

## Preview limitations

- Skills are in **public preview** (`Foundry-Features: Skills=V1Preview`; the
  Python SDK enables this via `allow_preview=True`).
- The Skills API is **not** reachable over a private endpoint — provision from a
  project with public network access enabled.
- RBAC: the caller needs the **Foundry User** role on the project.
