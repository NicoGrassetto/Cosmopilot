# Foundry Tools Roadmap

Tracks which Azure AI Foundry Agent Service tools we have implemented across the
Cosmopilot agents. Update the **Status** and **Where** columns as tools are added.

**Legend:** ✅ Implemented · 🚧 In progress · ⬜ Not started · 🔬 Preview (Foundry-side)

> Every tool below is now wired into at least one agent under `src/agents/`.
> Preview/grounding tools (Bing, SharePoint, Fabric, Azure AI Search, Work IQ,
> A2A, MCP, Azure Function) require the matching **connection/resource** to exist
> in the Foundry project before the agent can be registered.

## Action / execution tools

| Tool | `type` | Status | Where |
|---|---|---|---|
| Function calling | `function` | ✅ | `integration-assistant` |
| Code Interpreter | `code_interpreter` | ✅ | `hr-agent`, `insights-assistant` |
| MCP | `mcp` | ✅ | `integration-assistant` |
| OpenAPI | `openapi` | ✅ | `integration-assistant` |
| Azure Functions | `azure_function` | ✅ | `devops-assistant` |
| Image Generation | `image_generation` | ✅ | `browser-assistant` |
| Computer Use 🔬 | `computer_use_preview` | ✅ | `browser-assistant` |
| Browser Automation 🔬 | `browser_automation_preview` | ✅ | `browser-assistant` |
| Local Shell | `local_shell` | ✅ | `devops-assistant` |
| Shell | `shell` | ✅ | `devops-assistant` |
| Apply Patch | `apply_patch` | ✅ | `devops-assistant` |
| A2A (Agent-to-Agent) 🔬 | `a2a_preview` | ✅ | `orchestrator-assistant` |
| Custom | `custom` | ✅ | `integration-assistant` |
| Namespace | `namespace` | ✅ | `orchestrator-assistant` |
| Tool Search | `tool_search` | ✅ | `orchestrator-assistant` |
| Toolbox Search 🔬 | `toolbox_search_preview` | ✅ | `orchestrator-assistant` |
| Capture Structured Outputs | `capture_structured_outputs` | ✅ | `insights-assistant` |

## Knowledge / grounding tools

| Tool | `type` | Status | Where |
|---|---|---|---|
| File Search | `file_search` | ✅ | `hr-agent`, `research-assistant` |
| Azure AI Search | `azure_ai_search` | ✅ | `knowledge-assistant` |
| Bing Grounding | `bing_grounding` | ✅ | `research-assistant` |
| Bing Custom Search 🔬 | `bing_custom_search_preview` | ✅ | `research-assistant` |
| SharePoint Grounding 🔬 | `sharepoint_grounding_preview` | ✅ | `knowledge-assistant` |
| Fabric Data Agent 🔬 | `fabric_dataagent_preview` | ✅ | `insights-assistant` |
| Fabric IQ 🔬 | `fabric_iq_preview` | ✅ | `insights-assistant` |
| Work IQ 🔬 | `work_iq_preview` | ✅ | `knowledge-assistant` |
| Memory Search 🔬 | `memory_search_preview` | ✅ | `knowledge-assistant` |
| Web Search | `web_search` / `web_search_preview` | ✅ | `research-assistant` |

## Agents

| Agent | Type | Tools used | Location |
|---|---|---|---|
| hr-assistant | Prompt agent | `file_search`, `code_interpreter` | `src/agents/hr-agent/` |
| research-assistant | Prompt agent | `web_search`, `bing_grounding`, `bing_custom_search_preview`, `file_search` | `src/agents/research-assistant/` |
| knowledge-assistant | Prompt agent | `azure_ai_search`, `sharepoint_grounding_preview`, `work_iq_preview`, `memory_search_preview` | `src/agents/knowledge-assistant/` |
| insights-assistant | Prompt agent | `fabric_dataagent_preview`, `fabric_iq_preview`, `code_interpreter`, `capture_structured_outputs` | `src/agents/insights-assistant/` |
| devops-assistant | Prompt agent | `local_shell`, `shell`, `apply_patch`, `azure_function` | `src/agents/devops-assistant/` |
| integration-assistant | Prompt agent | `openapi`, `mcp`, `function`, `custom` | `src/agents/integration-assistant/` |
| browser-assistant | Prompt agent | `computer_use_preview`, `browser_automation_preview`, `image_generation` | `src/agents/browser-assistant/` |
| orchestrator-assistant | Prompt agent | `a2a_preview`, `tool_search`, `namespace`, `toolbox_search_preview` | `src/agents/orchestrator-assistant/` |
| deep-research-assistant | Hosted (LangGraph) | `web_search` (Foundry, called from graph) | `src/agents/deep-research-assistant/` |

> **deep-research-assistant** is a *hosted agent* (bring-your-own LangChain/LangGraph
> code), not a prompt agent. It runs an iterative plan → search → reflect → synthesize
> loop and is surfaced on Foundry over the Responses protocol via
> `langchain_azure_ai.agents.hosting`. Deploy with `azd` (see its `azure.yaml`).

---

_Tool list sourced from `azure-ai-projects` 2.3.0 `ToolType` enum._
