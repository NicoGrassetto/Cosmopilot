# Shared agent tools (`_shared`)

**Declare each agent tool once, reuse it across every Cosmopilot agent.**

The same three tools (`code_interpreter`, `query_cosmos_db`,
`get_change_feed_events`) used to be re-declared in four places, with the full
function JSON schemas duplicated inside `hosted-agent/agent.py`. This folder is
now the single source of truth.

## Two layers of reuse

| Layer | File | Reused by | Mechanism |
|-------|------|-----------|-----------|
| **Python module** | [`cosmos_tools.py`](./cosmos_tools.py) | Python agents (`hosted-agent`, `multi-agent`) | Import `tools(*names)` |
| **Foundry Toolbox** | [`toolbox.yaml`](./toolbox.yaml) + [`cosmos_mcp_server.py`](./cosmos_mcp_server.py) | **All** agent styles incl. `prompt-agent` & `workflow` | One shared `TOOLBOX_ENDPOINT` |

The MCP server does **not** re-implement the tools — each MCP tool delegates to
the shared implementation in `cosmos_tools.py`, so there is still one copy.

## Layer 1 — shared Python module

```python
from _shared import tools

agent = client.agents.create(
    name="cosmopilot-data-insights",
    model="gpt-4o-mini",
    instructions="...",
    tools=tools("code_interpreter", "query_cosmos_db", "get_change_feed_events"),
)
```

`tools(*names)`:
- Builds the Foundry `tools=[...]` list from tool names.
- Deep-copies each schema (agents can't mutate the shared definition).
- Deduplicates, preserving first-seen order.
- Raises `KeyError` on an unknown name, so typos fail fast.

Helpers: `all_tools()`, `cosmos_tools()`, `tool_names()`. Implementations
(`query_cosmos_db`, `get_change_feed_events`) live here too and lazy-import
`azure.cosmos`, so importing the definitions needs **no** Azure SDK.

> The consuming agents add `agents/` to `sys.path` so `from _shared import ...`
> works when run as `python agent.py`. No install step required.

## Layer 2 — Foundry Toolbox (all agent styles)

Prompt agents (`.prompty`) and YAML workflows can't import Python. To share the
same tools with them, expose the Cosmos functions over MCP and register them —
plus `code_interpreter` — in one **Toolbox**. Every agent then reads a single
`TOOLBOX_ENDPOINT`, and re-pointing the toolbox's default version rolls all
agents forward at once.

1. Run the MCP server (`pip install -r requirements.txt`, then
   `python cosmos_mcp_server.py`) and deploy it somewhere reachable.
2. Create a `remoteTool` connection to it and a toolbox from
   [`toolbox.yaml`](./toolbox.yaml) using the
   [Foundry Toolkit in VS Code](https://code.visualstudio.com/docs/intelligentapps/tool-catalog)
   or the [Foundry Portal](https://ai.azure.com/) (preferred), or the
   `azd ai toolbox` CLI.
3. Set `TOOLBOX_ENDPOINT` on each agent and have the agent connect to that one
   MCP endpoint.

See the Foundry [Toolbox docs](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/toolbox).
Add `toolbox_search_preview` (already in `toolbox.yaml`) once a toolbox grows
past ~5 tools so model context cost stays flat.

## Configuration

All environment variables are documented in the repo-root
[`.env.example`](../../.env.example) — copy it to `.env` and fill in the
placeholders. The variables this folder relies on:

| Variable | Used by | Notes |
|----------|---------|-------|
| `COSMOS_DB_ENDPOINT` | `cosmos_tools.py` impls | Required for live Cosmos calls (Entra ID auth) |
| `COSMOS_DB_DATABASE` | `cosmos_tools.py` impls | Defaults to `cosmopilot` |
| `COSMOS_MCP_SERVER_URL` | `toolbox.yaml` | Where `cosmos_mcp_server.py` is hosted |
| `TOOLBOX_ENDPOINT` | agents (Layer 2) | The shared toolbox MCP endpoint; **don't** prefix `FOUNDRY_` |

## Tests

Pure stdlib `unittest` (no Azure SDK needed):

```bash
python -m unittest discover -s agents/_shared/tests
```

`test_hosted_agent_tools_unchanged` pins the builder output to the original
inline definitions, so the refactor can't silently change agent behavior.

## Adding a new tool

1. Add its schema (and, if it's a custom function, its implementation) to
   `cosmos_tools.py` and register it in `ALL_TOOL_SCHEMAS` /
   `TOOL_IMPLEMENTATIONS`.
2. Reference it by name via `tools("...")` in any agent.
3. For cross-style reuse, expose it in `cosmos_mcp_server.py` and add it to
   `toolbox.yaml`.
