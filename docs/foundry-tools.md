# Microsoft Foundry tool constructors

This reference targets the new Microsoft Foundry Agent Service and
`azure-ai-projects>=2.4.0`. All classes are imported from
`azure.ai.projects.models` unless a different module is shown.

| Tool | Class/Function name | Availability |
|---|---|---|
| Agent-to-Agent (A2A) (preview) | `A2APreviewTool` / `A2APreviewToolboxTool` | Preview |
| Apply Patch (Responses SDK) | `ApplyPatchToolParam` | GA (Responses SDK primitive) |
| Azure AI Search | `AzureAISearchTool` / `AzureAISearchToolboxTool` | GA |
| Azure Functions | `AzureFunctionTool` | GA |
| Browser Automation (preview) | `BrowserAutomationPreviewTool` / `BrowserAutomationPreviewToolboxTool` | Preview |
| Capture Structured Outputs (Responses SDK) | `CaptureStructuredOutputsTool` | GA (Responses SDK primitive) |
| Code Interpreter | `CodeInterpreterTool` / `CodeInterpreterToolboxTool` | GA |
| Computer (Responses SDK) | `ComputerTool` | GA (Responses SDK primitive) |
| Computer Use (preview) | `ComputerUsePreviewTool` | Preview |
| Custom (Responses SDK) | `CustomToolParam` | GA (Responses SDK primitive) |
| Custom Code Interpreter (preview) | `MCPTool` / `MCPToolboxTool` | Preview |
| Fabric Data Agent (preview) | `MicrosoftFabricPreviewTool` | Preview |
| Fabric IQ (preview) | `FabricIQPreviewTool` / `FabricIQPreviewToolboxTool` | Preview |
| File Search | `FileSearchTool` / `FileSearchToolboxTool` | GA |
| Function calling | `FunctionTool` | GA |
| Grounding with Bing Custom Search (preview) | `BingCustomSearchPreviewTool` | Preview |
| Grounding with Bing Search | `BingGroundingTool` | GA |
| Image Generation (preview) | `ImageGenTool` | Preview |
| Local Shell (Responses SDK) | `LocalShellToolParam` | GA (Responses SDK primitive) |
| MCP | `MCPTool` / `MCPToolboxTool` | GA |
| Memory Search (preview) | `MemorySearchPreviewTool` | Preview |
| Namespace (Responses SDK) | `NamespaceToolParam` | GA (Responses SDK primitive) |
| OpenAPI | `OpenApiTool` / `OpenApiToolboxTool` | GA |
| Reminder (preview; hosted agents only) | `ReminderPreviewToolboxTool` | Preview |
| SharePoint (preview) | `SharepointPreviewTool` | Preview |
| Shell (Responses SDK) | `FunctionShellToolParam` | GA (Responses SDK primitive) |
| Skills (preview; not a `Tool`) | `SkillInlineContent`, `ToolboxSkillReference`, `project.beta.skills.create()` | Preview |
| Tool Search (Responses SDK) | `ToolSearchToolParam` | GA (Responses SDK primitive) |
| Tool Search (toolbox) | `ToolSearchToolboxTool` | GA |
| Toolbox (resource, not a `Tool`) | `project.toolboxes.create_version()` | GA |
| Web Search | `WebSearchTool` / `WebSearchToolboxTool` | GA |
| Web Search preview (deep research) | `WebSearchPreviewTool` | Preview |
| Work IQ (preview) | `WorkIQPreviewTool` / `WorkIQPreviewToolboxTool` | Preview |

Each snippet defines the tool object before placing it in `tools`. The snippets
are independent examples: do not attach every tool to one agent. Tool support
depends on the selected model, region, agent setup, and project connections.
`GA (Responses SDK primitive)` means the stable SDK exposes the type, but
Microsoft does not list it as a separate product in the Foundry tool catalog.

For snippets that create a toolbox or skill, assume this client is available:

```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

project = AIProjectClient(
    endpoint="https://<account>.services.ai.azure.com/api/projects/<project>",
    credential=DefaultAzureCredential(),
)
```

## Tool snippets

### Agent-to-Agent (A2A) (preview)

```python
from azure.ai.projects.models import A2APreviewTool

a2a_tool = A2APreviewTool(
    project_connection_id="<a2a-project-connection-id>",
)

tools = [a2a_tool]
```

The project connection stores the remote A2A endpoint and its authentication.
Set `base_url` only when the connection does not already carry the endpoint.

### Apply Patch (Responses SDK)

```python
from azure.ai.projects.models import ApplyPatchToolParam

apply_patch_tool = ApplyPatchToolParam()

tools = [apply_patch_tool]
```

This is a low-level Responses tool model rather than a separate Foundry tool
catalog entry. The surrounding runtime must safely handle emitted patch calls.

### Azure AI Search

```python
from azure.ai.projects.models import (
    AISearchIndexResource,
    AzureAISearchTool,
    AzureAISearchToolResource,
)

azure_ai_search_tool = AzureAISearchTool(
    azure_ai_search=AzureAISearchToolResource(
        indexes=[
            AISearchIndexResource(
                project_connection_id="<azure-ai-search-connection-id>",
                index_name="<index-name>",
                query_type="vector_semantic_hybrid",
                top_k=5,
            )
        ]
    )
)

tools = [azure_ai_search_tool]
```

The connection must point to the Azure AI Search service that owns the index.
The tool currently targets one index per tool instance.

### Azure Functions

```python
from azure.ai.projects.models import (
    AzureFunctionBinding,
    AzureFunctionDefinition,
    AzureFunctionDefinitionFunction,
    AzureFunctionStorageQueue,
    AzureFunctionTool,
)

azure_function_tool = AzureFunctionTool(
    azure_function=AzureFunctionDefinition(
        function=AzureFunctionDefinitionFunction(
            name="GetWeather",
            description="Get the weather for a location.",
            parameters={
                "type": "object",
                "properties": {"location": {"type": "string"}},
                "required": ["location"],
            },
        ),
        input_binding=AzureFunctionBinding(
            storage_queue=AzureFunctionStorageQueue(
                queue_service_endpoint="https://<account>.queue.core.windows.net",
                queue_name="weather-input",
            )
        ),
        output_binding=AzureFunctionBinding(
            storage_queue=AzureFunctionStorageQueue(
                queue_service_endpoint="https://<account>.queue.core.windows.net",
                queue_name="weather-output",
            )
        ),
    )
)

tools = [azure_function_tool]
```

This queue-based integration requires the standard agent setup. For an
HTTP-triggered Azure Function, expose it through MCP or OpenAPI instead.

### Browser Automation (preview)

```python
from azure.ai.projects.models import (
    BrowserAutomationPreviewTool,
    BrowserAutomationToolConnectionParameters,
    BrowserAutomationToolParameters,
)

browser_automation_tool = BrowserAutomationPreviewTool(
    browser_automation_preview=BrowserAutomationToolParameters(
        connection=BrowserAutomationToolConnectionParameters(
            project_connection_id="<playwright-workspace-connection-id>",
        )
    )
)

tools = [browser_automation_tool]
```

Use a dedicated Playwright workspace and trusted sites. Browser actions can
have real-world side effects and require application-level safety controls.

### Capture Structured Outputs (Responses SDK)

```python
from azure.ai.projects.models import (
    CaptureStructuredOutputsTool,
    StructuredOutputDefinition,
)

capture_outputs_tool = CaptureStructuredOutputsTool(
    outputs=StructuredOutputDefinition(
        name="analysis_result",
        description="Capture the final analysis result.",
        schema={
            "type": "object",
            "properties": {"summary": {"type": "string"}},
            "required": ["summary"],
            "additionalProperties": False,
        },
        strict=True,
    )
)

tools = [capture_outputs_tool]
```

This is an SDK Responses primitive. For a normal final JSON response, also
consider `PromptAgentDefinition.text` with a JSON schema response format.

### Code Interpreter

```python
from azure.ai.projects.models import (
    AutoCodeInterpreterToolParam,
    CodeInterpreterTool,
)

code_interpreter_tool = CodeInterpreterTool(
    container=AutoCodeInterpreterToolParam(
        file_ids=["<uploaded-file-id>"],
    )
)

tools = [code_interpreter_tool]
```

Use `CodeInterpreterTool()` when no files are needed. Code executes in a
Microsoft-managed sandbox and availability varies by region and model.

### Computer (Responses SDK)

```python
from azure.ai.projects.models import ComputerTool

computer_tool = ComputerTool()

tools = [computer_tool]
```

This low-level Responses tool is distinct from the documented Computer Use
preview integration. Verify support for the exact model and runtime before use.

### Computer Use (preview)

```python
from azure.ai.projects.models import ComputerUsePreviewTool

computer_use_tool = ComputerUsePreviewTool(
    environment="windows",
    display_width=1024,
    display_height=768,
)

tools = [computer_use_tool]
```

Computer Use requires a `computer-use-preview` deployment. Your application
must execute each requested action, capture a fresh screenshot, and return it
to the model. Run the loop only in an isolated environment.

### Custom (Responses SDK)

```python
from azure.ai.projects.models import CustomTextFormatParam, CustomToolParam

custom_tool = CustomToolParam(
    name="execute_sql",
    description="Accept a SQL statement as plain text.",
    format=CustomTextFormatParam(),
)

tools = [custom_tool]
```

The application is responsible for executing custom tool calls. Validate all
model-generated input before passing it to another system.

### Custom Code Interpreter (preview)

```python
from azure.ai.projects.models import MCPTool

custom_code_interpreter_tool = MCPTool(
    server_label="custom-code-interpreter",
    server_url="https://<custom-code-interpreter-host>/mcp",
    project_connection_id="<mcp-project-connection-id>",
    require_approval="always",
)

tools = [custom_code_interpreter_tool]
```

Custom Code Interpreter is an MCP server hosted on Azure Container Apps
Dynamic Sessions, not a separate Python tool class. Provision the session pool
and MCP endpoint before creating this tool.

### Fabric Data Agent (preview)

```python
from azure.ai.projects.models import (
    FabricDataAgentToolParameters,
    MicrosoftFabricPreviewTool,
    ToolProjectConnection,
)

fabric_data_agent_tool = MicrosoftFabricPreviewTool(
    fabric_dataagent_preview=FabricDataAgentToolParameters(
        project_connections=[
            ToolProjectConnection(
                project_connection_id="<fabric-data-agent-connection-id>",
            )
        ]
    )
)

tools = [fabric_data_agent_tool]
```

The Fabric data agent must be published. This integration uses signed-in user
identity passthrough and honors the user's Fabric permissions.

### Fabric IQ (preview)

```python
from azure.ai.projects.models import FabricIQPreviewTool

fabric_iq_tool = FabricIQPreviewTool(
    project_connection_id="<fabric-iq-connection-id>",
    server_label="fabric-iq",
    server_url="https://api.fabric.microsoft.com/<fabric-iq-mcp-path>",
    require_approval="never",
)

tools = [fabric_iq_tool]
```

The connection must use delegated user authentication. The exact MCP URL
depends on whether the target is an ontology, data agent, or Power BI semantic
model.

### File Search

```python
from azure.ai.projects.models import FileSearchTool

file_search_tool = FileSearchTool(
    vector_store_ids=["<vector-store-id>"],
    max_num_results=10,
)

tools = [file_search_tool]
```

Upload files and wait for vector-store ingestion to finish before invoking the
agent. Direct prompt-agent integration requires at least one vector store ID.

### Function calling

```python
from azure.ai.projects.models import FunctionTool

function_tool = FunctionTool(
    name="get_order",
    description="Retrieve an order by ID.",
    parameters={
        "type": "object",
        "properties": {"order_id": {"type": "string"}},
        "required": ["order_id"],
        "additionalProperties": False,
    },
    strict=True,
)

tools = [function_tool]
```

The model requests the call, but application code must execute the function and
send a `function_call_output` item back through the Responses API.

### Grounding with Bing Custom Search (preview)

```python
from azure.ai.projects.models import (
    BingCustomSearchConfiguration,
    BingCustomSearchPreviewTool,
    BingCustomSearchToolParameters,
)

bing_custom_search_tool = BingCustomSearchPreviewTool(
    bing_custom_search_preview=BingCustomSearchToolParameters(
        search_configurations=[
            BingCustomSearchConfiguration(
                project_connection_id="<bing-custom-search-connection-id>",
                instance_name="<custom-search-instance-name>",
            )
        ]
    )
)

tools = [bing_custom_search_tool]
```

The configured domains must be public and indexed by Bing. Bing grounding has
separate terms, pricing, display requirements, and data-boundary implications.

### Grounding with Bing Search

```python
from azure.ai.projects.models import (
    BingGroundingSearchConfiguration,
    BingGroundingSearchToolParameters,
    BingGroundingTool,
)

bing_grounding_tool = BingGroundingTool(
    bing_grounding=BingGroundingSearchToolParameters(
        search_configurations=[
            BingGroundingSearchConfiguration(
                project_connection_id="<bing-grounding-connection-id>",
                market="en-US",
                count=10,
            )
        ]
    )
)

tools = [bing_grounding_tool]
```

Microsoft recommends starting with Web Search for new general web-grounding
scenarios. Bing grounding requires a connected Grounding with Bing resource.

### Image Generation (preview)

```python
from azure.ai.projects.models import ImageGenTool

image_generation_tool = ImageGenTool(
    model="gpt-image-1",
    quality="low",
    size="1024x1024",
)

tools = [image_generation_tool]
```

Deploy both an orchestrator model and a supported image model in the project.
Responses also require the `x-ms-oai-image-generation-deployment` header.

### Local Shell (Responses SDK)

```python
from azure.ai.projects.models import LocalShellToolParam

local_shell_tool = LocalShellToolParam()

tools = [local_shell_tool]
```

The client runtime executes local-shell calls. Treat commands as untrusted and
run them in a restricted environment with explicit approval controls.

### MCP

```python
from azure.ai.projects.models import MCPTool

mcp_tool = MCPTool(
    server_label="microsoft-learn",
    server_url="https://learn.microsoft.com/api/mcp",
    project_connection_id="<mcp-project-connection-id>",
    allowed_tools=["microsoft_docs_search"],
    require_approval="always",
)

tools = [mcp_tool]
```

Omit `project_connection_id` for a public server that needs no authentication.
Keep approvals enabled for tools that read sensitive data or cause side effects.

### Memory Search (preview)

```python
from azure.ai.projects.models import MemorySearchPreviewTool

memory_search_tool = MemorySearchPreviewTool(
    memory_store_name="<memory-store-name>",
    scope="{{$userId}}",
    update_delay=300,
)

tools = [memory_search_tool]
```

Create the memory store first through `project.beta.memory_stores`. The scope
isolates memories; `{{$userId}}` resolves to the signed-in user's object ID.

### Namespace (Responses SDK)

```python
from azure.ai.projects.models import (
    CustomTextFormatParam,
    CustomToolParam,
    NamespaceToolParam,
)

lookup_customer_tool = CustomToolParam(
    name="lookup_customer",
    description="Look up a customer record.",
    format=CustomTextFormatParam(),
)

namespace_tool = NamespaceToolParam(
    name="crm",
    description="Customer relationship management tools.",
    tools=[lookup_customer_tool],
)

tools = [namespace_tool]
```

Namespaces group related function or custom tools and reduce naming collisions.
The application still executes the nested tools.

### OpenAPI

```python
from azure.ai.projects.models import (
    OpenApiAnonymousAuthDetails,
    OpenApiFunctionDefinition,
    OpenApiTool,
)

openapi_spec = {
    "openapi": "3.1.0",
    "info": {"title": "Weather API", "version": "1.0.0"},
    "servers": [{"url": "https://wttr.in"}],
    "paths": {
        "/{location}": {
            "get": {
                "operationId": "get_weather",
                "parameters": [
                    {
                        "name": "location",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                ],
                "responses": {"200": {"description": "OK"}},
            }
        }
    },
}

openapi_tool = OpenApiTool(
    openapi=OpenApiFunctionDefinition(
        name="weather_api",
        description="Retrieve weather for a location.",
        spec=openapi_spec,
        auth=OpenApiAnonymousAuthDetails(),
    )
)

tools = [openapi_tool]
```

Every operation needs a descriptive `operationId`. Use
`OpenApiProjectConnectionAuthDetails` for secrets stored in a project
connection or `OpenApiManagedAuthDetails` for Microsoft Entra authentication.

### Reminder (preview; hosted agents only)

```python
from azure.ai.projects.models import ReminderPreviewToolboxTool

reminder_tool = ReminderPreviewToolboxTool(
    name="schedule_reminder",
    description="Re-invoke this agent at a requested future time.",
)

tools = [reminder_tool]

toolbox = project.toolboxes.create_version(
    name="reminder-toolbox",
    description="Self-scheduling tools",
    tools=tools,
)
```

Reminder is toolbox-only and works only with hosted agents. It re-invokes the
same agent on the same conversation after 1 to 43,200 minutes.

### SharePoint (preview)

```python
from azure.ai.projects.models import (
    SharepointGroundingToolParameters,
    SharepointPreviewTool,
    ToolProjectConnection,
)

sharepoint_tool = SharepointPreviewTool(
    sharepoint_grounding_preview=SharepointGroundingToolParameters(
        project_connections=[
            ToolProjectConnection(
                project_connection_id="<sharepoint-connection-id>",
            )
        ]
    )
)

tools = [sharepoint_tool]
```

SharePoint requires delegated user identity, same-tenant access, and a
Microsoft 365 Copilot license or the supported pay-as-you-go retrieval model.

### Shell (Responses SDK)

```python
from azure.ai.projects.models import ContainerAutoParam, FunctionShellToolParam

shell_tool = FunctionShellToolParam(
    environment=ContainerAutoParam(),
)

tools = [shell_tool]
```

Use a container environment for isolation. The shell tool can also reference an
existing container or a local environment when the runtime supports it.

### Skills (preview; not a `Tool`)

```python
from azure.ai.projects.models import SkillInlineContent, ToolboxSkillReference

skill_content = SkillInlineContent(
    description="Generate a concise personalized greeting.",
    instructions="Use the user's name when available and keep the greeting brief.",
)

skill_reference = ToolboxSkillReference(name="greeting")

tools = []

project.beta.skills.create(
    name="greeting",
    inline_content=skill_content,
)

toolbox = project.toolboxes.create_version(
    name="skills-toolbox",
    description="Toolbox with a reusable greeting skill",
    tools=tools,
    skills=[skill_reference],
)
```

Skills are MCP resources, not callable tools. Toolbox skill discovery is for
hosted agents whose MCP client supports `resources/list` and `resources/read`.
Prompt agents do not support skills through a toolbox; inject their content into
the prompt instead. The Skills API also requires a public endpoint.

### Tool Search (Responses SDK)

```python
from azure.ai.projects.models import FunctionTool, ToolSearchToolParam

deferred_function = FunctionTool(
    name="get_inventory",
    description="Read current inventory for a product.",
    parameters={
        "type": "object",
        "properties": {"product_id": {"type": "string"}},
        "required": ["product_id"],
        "additionalProperties": False,
    },
    strict=True,
    defer_loading=True,
)

tool_search = ToolSearchToolParam(execution="server")

tools = [tool_search, deferred_function]
```

This Responses primitive discovers tool definitions marked with
`defer_loading=True`. It is different from enabling search across a Foundry
toolbox.

### Tool Search (toolbox)

```python
from azure.ai.projects.models import MCPToolboxTool, ToolSearchToolboxTool

github_tools = MCPToolboxTool(
    server_label="github",
    server_url="https://api.githubcopilot.com/mcp",
    project_connection_id="<github-mcp-connection-id>",
    require_approval="always",
    description="Work with GitHub repositories and issues.",
)

tool_search = ToolSearchToolboxTool(
    description="Discover toolbox tools by capability.",
)

tools = [github_tools, tool_search]

toolbox = project.toolboxes.create_version(
    name="searchable-toolbox",
    description="GitHub tools with intent-based discovery",
    tools=tools,
)
```

`ToolSearchToolboxTool` is the stable class introduced in SDK 2.4.0. It
replaces `ToolboxSearchPreviewToolboxTool`. With search enabled, the toolbox MCP
endpoint initially exposes `tool_search` and `call_tool` instead of every inner
tool definition.

### Toolbox (resource, not a `Tool`)

```python
from azure.ai.projects.models import WebSearchToolboxTool

web_search_tool = WebSearchToolboxTool(
    name="web_search",
    description="Search the public web for current information.",
)

tools = [web_search_tool]

toolbox = project.toolboxes.create_version(
    name="research-toolbox",
    description="Reusable research tools",
    tools=tools,
)
```

A toolbox is a versioned project resource that exposes its contents through an
MCP endpoint. SDK 2.3.0 and later uses `ToolboxTool` subclasses for the
`tools` list rather than direct-agent `Tool` subclasses.

### Web Search

```python
from azure.ai.projects.models import (
    WebSearchApproximateLocation,
    WebSearchTool,
)

web_search_tool = WebSearchTool(
    user_location=WebSearchApproximateLocation(
        country="US",
        region="Washington",
        city="Seattle",
    ),
    search_context_size="medium",
)

tools = [web_search_tool]
```

Web Search is the recommended general web-grounding tool. It uses Bing-backed
services, so review the applicable terms, pricing, and data-boundary notes.

### Web Search preview (deep research)

```python
from azure.ai.projects.models import WebSearchPreviewTool

web_search_preview_tool = WebSearchPreviewTool(
    search_context_size="high",
)

tools = [web_search_preview_tool]
```

Use this preview form for the documented deep-research pattern with an
`o3-deep-research` deployment. Prefer `WebSearchTool` for normal web search.

### Work IQ (preview)

```python
from azure.ai.projects.models import WorkIQPreviewTool

work_iq_tool = WorkIQPreviewTool(
    project_connection_id="<work-iq-connection-id>",
)

tools = [work_iq_tool]
```

Work IQ uses delegated user authentication and Microsoft 365 permissions. Each
caller needs the required Microsoft 365 Copilot license, and VNet-restricted
project endpoints are not supported.

## Sources

- [Foundry tool catalog](https://learn.microsoft.com/azure/foundry/agents/concepts/tool-catalog)
- [Create and manage a toolbox](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/toolbox)
- [Foundry tool best practices](https://learn.microsoft.com/azure/foundry/agents/concepts/tool-best-practice)
- [Azure AI Projects Python models](https://learn.microsoft.com/python/api/azure-ai-projects/azure.ai.projects.models)
- [Azure AI Projects release history](https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/ai/azure-ai-projects/CHANGELOG.md)