# Cosmopilot Tools

A catalog of every tool wired into the Cosmopilot agents (`src/agents/`), what it
does, its value proposition, and which agent uses it.

**Reference:** [Agent tools overview — Microsoft Foundry tool catalog](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/tool-catalog)

**Status legend:** ✅ active · ⏸️ disabled (code present but commented out) · 🔬 Foundry preview

> Grounding/action tools that reach external data (Azure AI Search, Bing, Fabric,
> SharePoint, Work IQ, Azure Functions, MCP, A2A) require the matching
> **connection/resource** to exist in the Foundry project before the agent can be
> registered. See `docs/tools-roadmap.md` for the implementation matrix.

---

## Knowledge & grounding tools

These keep an agent's answers grounded in real data instead of the model's memory.

### [File Search](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/file-search) — `file_search` ✅
- **Used by:** `hr-agent`, `research-assistant`
- **What it does:** Vector-search over documents you upload into a Foundry/OpenAI vector store.
- **Value:** Turn a pile of PDFs/policies into a searchable knowledge base with zero index management — the service handles chunking, embedding, and retrieval.

### [Azure AI Search](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/ai-search) — `azure_ai_search` ✅
- **Used by:** `knowledge-assistant` *(verified working end-to-end)*
- **What it does:** Grounds answers in an existing Azure AI Search index (keyword, semantic, vector, or hybrid).
- **Value:** Reuse an enterprise-grade search index you already own — full control over schema, relevance, filters, and security — and get answers with source citations.

### [Grounding with Bing Search](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/bing-tools) — `bing_grounding` ✅
- **Used by:** `research-assistant`
- **What it does:** Fetches live public web results through Bing and grounds the answer in them.
- **Value:** Real-time, cited web knowledge so the agent isn't limited to its training cutoff.

### [Bing Custom Search](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/bing-tools) — `bing_custom_search_preview` 🔬 ⏸️
- **Used by:** `research-assistant` *(disabled — runtime rejects it with HTTP 400)*
- **What it does:** Like Bing grounding but scoped to a curated set of domains/sites.
- **Value:** Narrow web grounding to trusted sources (e.g. your docs + partner sites) to cut noise.

### [Web Search](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/web-search) — `web_search` ✅
- **Used by:** `research-assistant`, `deep-research-assistant`
- **What it does:** Built-in real-time web retrieval with inline citations (the recommended web-grounding path).
- **Value:** Simplest way to add current, attributable web knowledge to an agent.

### [SharePoint](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/sharepoint) — `sharepoint_grounding_preview` 🔬 ⏸️
- **Used by:** `knowledge-assistant` *(disabled)*
- **What it does:** Chats over private documents in a SharePoint site, respecting the user's permissions.
- **Value:** Ground answers in existing intranet content without copying it into a separate index.

### Work IQ — `work_iq_preview` 🔬 ⏸️
- **Used by:** `knowledge-assistant` *(disabled)*
- **Reference:** [tool catalog](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/tool-catalog)
- **What it does:** Grounds answers in the signed-in user's Microsoft 365 work context (mail, files, Teams, calendar) on-behalf-of that user.
- **Value:** Deeply personalized, work-aware answers — but requires a per-user M365 identity + Copilot license (see `docs/tools-roadmap.md`).

### Memory Search — `memory_search_preview` 🔬 ⏸️
- **Used by:** `knowledge-assistant` *(disabled — see note; store still provisioned)*
- **Reference:** [tool catalog](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/tool-catalog)
- **What it does:** Reads/writes a persistent, per-user memory store so the agent remembers facts across conversations.
- **Value:** Continuity and personalization across sessions. **Note:** in the current runtime it monopolizes the turn and starves `azure_ai_search`, so it's commented out until the preview coexists with retrieval tools.

### [Microsoft Fabric (Data Agent)](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/fabric) — `fabric_dataagent_preview` 🔬 ✅
- **Used by:** `insights-assistant`
- **What it does:** Connects to a Microsoft Fabric data agent to query governed analytics data in natural language.
- **Value:** Ask business questions over your Fabric lakehouse/warehouse without writing SQL.

### Fabric IQ — `fabric_iq_preview` 🔬 ✅
- **Used by:** `insights-assistant`
- **Reference:** [Microsoft Fabric tool](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/fabric)
- **What it does:** Semantic/BI layer over Fabric for richer, model-aware analytics grounding.
- **Value:** Higher-level, metric-aware answers on top of Fabric data.

---

## Action & execution tools

These let an agent *do* things — run code, call APIs, drive a browser, orchestrate other agents.

### [Code Interpreter](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/code-interpreter) — `code_interpreter` ✅
- **Used by:** `hr-agent`, `insights-assistant`
- **What it does:** Writes and runs Python in a sandbox for math, data analysis, and charting.
- **Value:** Accurate computation and visualizations instead of the model guessing numbers.

### [Function calling](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/function-calling) — `function` ✅
- **Used by:** `integration-assistant`
- **What it does:** Exposes your own functions; the model decides when to call them and your app executes.
- **Value:** The core extensibility primitive — connect an agent to any bespoke logic you own.

### [Model Context Protocol (MCP)](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/model-context-protocol) — `mcp` ✅
- **Used by:** `integration-assistant`
- **What it does:** Connects the agent to tools hosted on an MCP server endpoint.
- **Value:** Reuse standardized, shareable tool servers across many agents/teams without re-implementing.

### [OpenAPI](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/openapi) — `openapi` ✅
- **Used by:** `integration-assistant`
- **What it does:** Turns any OpenAPI 3.0/3.1 spec into callable agent tools.
- **Value:** Instantly wire an existing REST API into an agent with little or no glue code.

### [Custom tool](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/tool-catalog) — `custom` ✅
- **Used by:** `integration-assistant`
- **What it does:** A freeform tool definition for bespoke integrations not covered by the built-ins.
- **Value:** Escape hatch for custom capabilities and grammars.

### [Azure Functions](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/azure-functions) — `azure_function` ✅
- **Used by:** `devops-assistant`
- **What it does:** Lets the agent invoke your Azure Functions for custom actions and dynamic data.
- **Value:** Serverless, scalable back-end actions with your own auth and business logic.

### Local Shell — `local_shell` ✅
- **Used by:** `devops-assistant`
- **Reference:** [tool catalog](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/tool-catalog)
- **What it does:** Emits shell commands for a local runtime to execute.
- **Value:** Automate local/devbox operations from natural language.

### Shell — `shell` ✅
- **Used by:** `devops-assistant`
- **Reference:** [tool catalog](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/tool-catalog)
- **What it does:** Runs shell commands in a managed environment the agent controls.
- **Value:** Hands-free execution of build/ops/diagnostic commands.

### Apply Patch — `apply_patch` ✅
- **Used by:** `devops-assistant`
- **Reference:** [tool catalog](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/tool-catalog)
- **What it does:** Applies structured code diffs/patches to files.
- **Value:** Safe, reviewable file edits for coding/automation workflows.

### [Image Generation](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/image-generation) — `image_generation` 🔬 ✅
- **Used by:** `browser-assistant`
- **What it does:** Generates images inline as part of a conversation.
- **Value:** Produce visuals (mockups, diagrams, marketing assets) without leaving the agent.

### [Computer Use](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/computer-use) — `computer_use_preview` 🔬 ✅
- **Used by:** `browser-assistant`
- **What it does:** Interacts with computer systems through their GUI (clicks, typing, navigation).
- **Value:** Automate legacy apps and UIs that have no API.

### [Browser Automation](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/browser-automation) — `browser_automation_preview` 🔬 ✅
- **Used by:** `browser-assistant`
- **What it does:** Performs web tasks (navigate, fill forms, extract) from natural-language prompts.
- **Value:** End-to-end web workflows and scraping without brittle custom scripts.

### [Agent-to-Agent (A2A)](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/agent-to-agent) — `a2a_preview` 🔬 ✅
- **Used by:** `orchestrator-assistant`
- **What it does:** Calls other agents through A2A-compatible endpoints.
- **Value:** Compose specialist agents into a multi-agent system with a single orchestrator.

### Namespace — `namespace` ✅
- **Used by:** `orchestrator-assistant`
- **Reference:** [tool catalog](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/tool-catalog)
- **What it does:** Groups a set of tools under a named namespace the orchestrator can route to.
- **Value:** Keeps large tool sets organized and routable in multi-agent setups.

### Tool Search — `tool_search` ✅
- **Used by:** `orchestrator-assistant`
- **Reference:** [tool catalog](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/tool-catalog)
- **What it does:** Lets the agent discover the right tool from a large catalog at runtime.
- **Value:** Scales to many tools without overflowing the prompt with definitions.

### [Toolbox Search](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/toolbox) — `toolbox_search_preview` 🔬 ✅
- **Used by:** `orchestrator-assistant`
- **What it does:** Exposes a curated bundle of tools as a single MCP endpoint, searchable at runtime.
- **Value:** Configure tools once, reuse the bundle across many agents, and version it centrally.

### Capture Structured Outputs — `capture_structured_outputs` ✅
- **Used by:** `insights-assistant`
- **Reference:** [tool catalog](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/tool-catalog)
- **What it does:** Forces the agent to emit results against a defined output schema.
- **Value:** Reliable, machine-parseable outputs for downstream systems (no fragile text parsing).

---

## Agent → tools map

| Agent | Active tools | Disabled |
|---|---|---|
| `hr-agent` | `file_search`, `code_interpreter` | — |
| `research-assistant` | `web_search`, `bing_grounding`, `file_search` | `bing_custom_search_preview` |
| `knowledge-assistant` | `azure_ai_search` | `sharepoint_grounding_preview`, `work_iq_preview`, `memory_search_preview` |
| `insights-assistant` | `fabric_dataagent_preview`, `fabric_iq_preview`, `code_interpreter`, `capture_structured_outputs` | — |
| `devops-assistant` | `local_shell`, `shell`, `apply_patch`, `azure_function` | — |
| `integration-assistant` | `openapi`, `mcp`, `function`, `custom` | — |
| `browser-assistant` | `computer_use_preview`, `browser_automation_preview`, `image_generation` | — |
| `orchestrator-assistant` | `a2a_preview`, `namespace`, `tool_search`, `toolbox_search_preview` | — |
| `deep-research-assistant` | `web_search` (LangGraph reflection loop) | — |

> Separate from callable tools, every agent also loads local **Skills** (Markdown
> guidelines injected into its system prompt). See `docs/tools-roadmap.md`.
