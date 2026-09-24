# azure-ai-projects

Method reference for the synchronous `azure.ai.projects.AIProjectClient`.

- **Latest published release:** [2.7.0][pypi], released **September 18, 2026**.
- **Checked:** September 22, 2026, against PyPI metadata, the [release notes][changelog], and the [2.7.0 release-tagged source][sdk-source], including handwritten extensions to generated operations.
- **Requirements:** Python 3.10 or newer; `openai>=3.0.0`.
- **Default Foundry REST API version:** `v1`.
- **Coverage:** 186 public client methods across 24 tables, plus 16 methods across seven tables for returned realtime objects.

> **Versioned reference:** [requirements.txt](../requirements.txt) records the
> repository's current dependency pins, while the tables below describe exactly
> Projects 2.7.0. Earlier environments, such as Projects 2.4.0 with OpenAI 2.x,
> cannot provide this entire API surface. The demo notebooks check the selected
> kernel before live execution; changing a manifest does not itself update the
> packages installed in that kernel.

## What changed in 2.7.0

- Added preview Voice Agents: conversation/audio retrieval, realtime WebSocket sessions, and telephony.
- Added `client.beta.agents.create_from_prompt` for generating a Voice Agent from high-level inputs.
- Added `client.toolboxes.invoke_latest_toolbox_mcp`.
- Added prompt-agent harness and skill configuration, invocation moderation, and further agent/toolbox/data-generation model fields.
- Added the optional `voice` dependency group: `websockets` for synchronous realtime connections and `aiohttp` for asynchronous connections.
- Changed beta model contracts: `DataGenerationJobOptions` and `SimulationSeedDataGenerationJobOptions` no longer expose `max_samples` as a constructor argument/property; `ToolboxObject` now requires `updated_at` and `versions`.

See the [release notes][changelog] for the complete changes and examples.

## Scope and conventions

- `client` means an `AIProjectClient` instance. Each table documents one callable namespace, with **one row per public method**. Overloads and overridden implementations share a row.
- Private methods, constructors/context-manager special methods, and data-model members are excluded. Container namespaces with no public methods are identified explicitly rather than given placeholder method rows.
- The result column shows the **declared synchronous SDK return type**, with model module prefixes omitted. Full signatures, parameters, and overloads are available through each section's reference link.
- `ItemPaged[T]` is a lazy, paginated iterable; iteration can issue additional requests. `Iterator[bytes]` yields binary chunks, not a local file path.
- `begin_*` methods return long-running-operation pollers. Use the poller's `result()` to wait for completion; receiving a poller does not mean the service operation has finished.
- A stable package can include preview APIs. Access through `client.beta` opts into preview behavior without requiring `allow_preview=True`. Preview features on non-beta surfaces require that constructor option; not every method outside `beta` is necessarily GA.
- The asynchronous client is available from `azure.ai.projects.aio`. This document does not duplicate its async signatures; see the [async client reference][async-client-api].
- `client.get_openai_client()` returns a client from the **separate `openai` package**. Its Responses, Conversations, Evaluations, Files, and Fine-Tuning APIs are not additional `AIProjectClient` submodules and are not enumerated here. For example, use `openai_client.evals`, not `client.evals`.
- `azure.ai.projects.models` contains request/response types. It is not `client.models`; model asset operations are under `client.beta.models`.

For example, with the endpoint exported and Azure authentication configured:

```python
import os

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

with (
    DefaultAzureCredential() as credential,
    AIProjectClient(
        endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
        credential=credential,
        allow_preview=True,
    ) as client,
):
    for deployment in client.deployments.list():
        print(deployment.name)
```

## Client namespace map

```text
client
  agents
  connections
  datasets
  deployments
  evaluation_rules
  indexes
  telemetry
  toolboxes
  beta
    agents
    agent_insight_monitors
    datasets
    evaluation_taxonomies
    evaluators
    insights
    memory_stores
    models
    red_teams
    routines
    schedules
    skills
    voice_agents
      conversations
      realtime
      telephony
```

## `client`

Project client lifecycle, authenticated OpenAI access, and low-level HTTP requests.
[API reference][client-api].

| Method | Purpose | Declared result |
| --- | --- | --- |
| `close` | Close the project's HTTP client and release its transport resources. A context manager handles this automatically. | `None` |
| `get_openai_client` | Create an authenticated OpenAI client for the project. Optional `agent_name` targets an agent endpoint and requires preview opt-in. Additional options go to the OpenAI constructor. | `openai.OpenAI` |
| `send_request` | Send an `HttpRequest` through the project's Azure Core policy pipeline; supports `stream=True`. | `HttpResponse` |

## `client.agents`

Manage named agents, versions, endpoints, hosted-agent sessions/files, and Microsoft 365 publishing.
Agent invocation uses the OpenAI client rather than a `run` method in this group.
[API reference][agents-api].

| Method | Purpose | Declared result |
| --- | --- | --- |
| `create_session` | Create a session for an agent version. | `AgentSessionResource` |
| `create_version` | Save a new version of an agent definition. | `AgentVersionDetails` |
| `create_version_from_code` | Upload code and create a hosted-agent version. | `AgentVersionDetails` |
| `create_version_from_manifest` | Create an agent version from a manifest and parameter values. | `AgentVersionDetails` |
| `delete` | Delete a named agent. | `DeleteAgentResponse` |
| `delete_session` | Delete an agent session. | `None` |
| `delete_session_file` | Delete a file or directory in a session. | `None` |
| `delete_version` | Delete a specific agent version. | `DeleteAgentVersionResponse` |
| `disable` | Disable an agent. | `None` |
| `download_code` | Download an agent version's code archive. | `Iterator[bytes]` |
| `download_session_file` | Download a file from a session. | `Iterator[bytes]` |
| `enable` | Enable an agent. | `None` |
| `get` | Retrieve a named agent. | `AgentDetails` |
| `get_microsoft365_package` | Generate and download a Microsoft 365 app package for an agent. | `Iterator[bytes]` |
| `get_microsoft365_publish_defaults` | Retrieve default configuration for Microsoft 365 publishing. | `Microsoft365PublishDefaults` |
| `get_session` | Retrieve an agent session. | `AgentSessionResource` |
| `get_session_log_stream` | Request the hosted-agent session's console log stream. See the SSE note below. | `SessionLogEvent` |
| `get_version` | Retrieve a specific agent version. | `AgentVersionDetails` |
| `list` | Enumerate agents in the project. | `ItemPaged[AgentDetails]` |
| `list_session_files` | Enumerate files and directories in a session. | `ItemPaged[SessionDirectoryEntry]` |
| `list_sessions` | Enumerate an agent's sessions. | `ItemPaged[AgentSessionResource]` |
| `list_versions` | Enumerate an agent's versions. | `ItemPaged[AgentVersionDetails]` |
| `publish_to_microsoft365` | Publish an agent to Microsoft 365. | `Microsoft365PublishResult` |
| `stop_session` | Stop an agent session. | `None` |
| `update_details` | Update agent endpoint configuration, such as version routing and protocols. | `AgentDetails` |
| `upload_session_file` | Upload a file into a session. | `SessionFileWriteResult` |

The log endpoint is documented as Server-Sent Events (SSE), although the generated
method's return annotation is `SessionLogEvent`. Treat each log frame's `data` as
opaque text; its current JSON formatting is not a stable schema.

## `client.connections`

Inspect resources connected to the project.
[API reference][connections-api].

| Method | Purpose | Declared result |
| --- | --- | --- |
| `get` | Retrieve a connection by name; optionally include its credentials. | `Connection` |
| `get_default` | Resolve the default connection for a connection type; optionally include credentials. | `Connection` |
| `list` | Enumerate connections, optionally filtered by connection type. | `ItemPaged[Connection]` |

`include_credentials` defaults to `False` on `get` and `get_default`. Treat returned
credentials as secrets. `get_default` raises `ValueError` if no default is found.

## `client.datasets`

Manage versioned dataset assets and upload local content.
[API reference][datasets-api].

| Method | Purpose | Declared result |
| --- | --- | --- |
| `create_or_update` | Create or update a named dataset version. | `DatasetVersion` |
| `delete` | Delete a dataset version. | `None` |
| `get` | Retrieve a dataset version. | `DatasetVersion` |
| `get_credentials` | Obtain credentials for accessing a dataset's backing storage. | `DatasetCredential` |
| `list` | Enumerate the latest version of each dataset. | `ItemPaged[DatasetVersion]` |
| `list_versions` | Enumerate versions of a named dataset. | `ItemPaged[DatasetVersion]` |
| `pending_upload` | Prepare storage for an upload and return upload information. | `PendingUploadResponse` |
| `upload_file` | Upload a local file to blob storage and register a dataset referencing it. | `FileDatasetVersion` |
| `upload_folder` | Recursively upload a folder, preserve relative paths, and register a dataset. | `FolderDatasetVersion` |

Synthetic data generation is separate: see `client.beta.datasets`.

## `client.deployments`

Inspect model deployments available to the project. This group does not create deployments.
[API reference][deployments-api].

| Method | Purpose | Declared result |
| --- | --- | --- |
| `get` | Retrieve a deployment by name. | `Deployment` |
| `list` | Enumerate deployments, with optional model, publisher, or deployment-type filters. | `ItemPaged[Deployment]` |

## `client.evaluation_rules`

Manage rules that control evaluation behavior, rather than evaluation definitions/runs
on the OpenAI client.
[API reference][evaluation-rules-api].

| Method | Purpose | Declared result |
| --- | --- | --- |
| `create_or_update` | Create or update an evaluation rule. | `EvaluationRule` |
| `delete` | Delete an evaluation rule. | `None` |
| `get` | Retrieve an evaluation rule. | `EvaluationRule` |
| `list` | Enumerate evaluation rules. | `ItemPaged[EvaluationRule]` |

## `client.indexes`

Manage project index assets and their versions.
[API reference][indexes-api].

| Method | Purpose | Declared result |
| --- | --- | --- |
| `create_or_update` | Create or update an index version. | `Index` |
| `delete` | Delete an index version. | `None` |
| `get` | Retrieve a specific index version. | `Index` |
| `list` | Enumerate the latest version of each index. | `ItemPaged[Index]` |
| `list_versions` | Enumerate versions of a named index. | `ItemPaged[Index]` |

## `client.telemetry`

This handwritten subclient is attached by the public client extension, not the generated
base client. Retrieving a connection string does not itself configure tracing or export spans.
[Release-tagged source][telemetry-source].

| Method | Purpose | Declared result |
| --- | --- | --- |
| `get_application_insights_connection_string` | Retrieve the connection string for the project's connected Application Insights resource. Raises `ResourceNotFoundError` if no connection exists. | `str` |

## `client.toolboxes`

Manage versioned collections of tools and skills.
[API reference][toolboxes-api].

| Method | Purpose | Declared result |
| --- | --- | --- |
| `create_version` | Create a new toolbox version. | `ToolboxVersionObject` |
| `delete` | Delete a toolbox. | `None` |
| `delete_version` | Delete a specific toolbox version. | `None` |
| `get` | Retrieve a toolbox and its current configuration. | `ToolboxObject` |
| `get_version` | Retrieve a specific toolbox version. | `ToolboxVersionObject` |
| `invoke_latest_toolbox_mcp` | Send an MCP request to the latest toolbox version's endpoint. New in 2.7.0. | `Any` |
| `list` | Enumerate toolboxes. | `ItemPaged[ToolboxObject]` |
| `list_versions` | Enumerate versions of a toolbox. | `ItemPaged[ToolboxVersionObject]` |
| `update` | Update a toolbox to point to a specified version. | `ToolboxObject` |

## `client.beta`

**Preview container; no direct public methods.** Its subclients are documented below.
Their preview feature headers are supplied by the SDK.
[API reference][beta-api].

## `client.beta.agents`

Preview agent optimization jobs and prompt-based agent generation.
[API reference][beta-agents-api].

| Method | Purpose | Declared result |
| --- | --- | --- |
| `begin_create_optimization_job` | Start an agent optimization job and return its completion poller. | `AgentOptimizationLROPoller` |
| `cancel_optimization_job` | Request cancellation of an optimization job. | `AgentOptimizationJob` |
| `create_from_prompt` | Generate and create a Voice Agent using `GenerateVoiceAgentRequest`. New in 2.7.0. | `AgentDetails` |
| `delete_optimization_job` | Delete an optimization job. | `None` |
| `get_optimization_job` | Retrieve an optimization job and its status. | `AgentOptimizationJob` |
| `list_optimization_jobs` | Enumerate optimization job summaries. | `ItemPaged[AgentOptimizationJobListItem]` |

## `client.beta.agent_insight_monitors`

Preview monitors that analyze agent behavior and maintain insights across runs.
This is distinct from the report-oriented `client.beta.insights` group.
[API reference][agent-insight-monitors-api].

| Method | Purpose | Declared result |
| --- | --- | --- |
| `begin_create_run` | Start an Agent Insights run for a monitor and return a completion poller. | `AgentInsightRunLROPoller` |
| `cancel_run` | Request cancellation of a monitor run. | `AgentInsightRun` |
| `create` | Create an Agent Insights monitor for an agent. | `AgentInsightMonitor` |
| `delete` | Delete a monitor and all of its runs, insights, and state. | `None` |
| `get` | Retrieve a monitor. | `AgentInsightMonitor` |
| `get_insight` | Retrieve a full insight belonging to a monitor. | `AgentInsight` |
| `get_run` | Retrieve an individual monitor run. | `AgentInsightRun` |
| `list` | Enumerate monitor summaries, optionally filtered by agent name. | `ItemPaged[AgentInsightMonitorListItem]` |
| `list_insights` | Enumerate a monitor's current insights. | `ItemPaged[AgentInsight]` |
| `list_runs` | Enumerate runs for a monitor. | `ItemPaged[AgentInsightRun]` |
| `reset` | Reset a monitor's overview, checkpoint, and active insight state. | `None` |
| `update` | Update a monitor's configuration. | `AgentInsightMonitor` |
| `update_insight` | Change an insight's lifecycle status. | `AgentInsight` |

## `client.beta.datasets`

Preview jobs that generate synthetic or derived data. Ordinary dataset registration
and uploads remain under `client.datasets`.
[API reference][beta-datasets-api].

| Method | Purpose | Declared result |
| --- | --- | --- |
| `begin_create_generation_job` | Start a data-generation job and return its completion poller. | `DatasetGenerationLROPoller` |
| `cancel_generation_job` | Request cancellation of a data-generation job. | `DataGenerationJob` |
| `delete_generation_job` | Delete a data-generation job. | `None` |
| `get_generation_job` | Retrieve a data-generation job and its status. | `DataGenerationJob` |
| `list_generation_jobs` | Enumerate data-generation jobs. | `ItemPaged[DataGenerationJob]` |

## `client.beta.evaluation_taxonomies`

Preview taxonomies describing the categories or risks used in evaluation.
[API reference][evaluation-taxonomies-api].

| Method | Purpose | Declared result |
| --- | --- | --- |
| `create` | Create an evaluation taxonomy. | `EvaluationTaxonomy` |
| `delete` | Delete a taxonomy. | `None` |
| `get` | Retrieve a taxonomy. | `EvaluationTaxonomy` |
| `list` | Enumerate taxonomies. | `ItemPaged[EvaluationTaxonomy]` |
| `update` | Update a taxonomy. | `EvaluationTaxonomy` |

## `client.beta.evaluators`

Preview evaluator versions, artifact uploads, and evaluator-generation jobs.
[API reference][evaluators-api].

| Method | Purpose | Declared result |
| --- | --- | --- |
| `begin_create_generation_job` | Start an evaluator-generation job and return its completion poller. | `EvaluatorGenerationLROPoller` |
| `cancel_generation_job` | Request cancellation of an evaluator-generation job. | `EvaluatorGenerationJob` |
| `create_version` | Create an evaluator version. | `EvaluatorVersion` |
| `delete_generation_job` | Delete an evaluator-generation job. | `None` |
| `delete_version` | Delete an evaluator version. | `None` |
| `get_credentials` | Obtain credentials for evaluator artifact storage. | `DatasetCredential` |
| `get_generation_job` | Retrieve an evaluator-generation job. | `EvaluatorGenerationJob` |
| `get_version` | Retrieve an evaluator version. | `EvaluatorVersion` |
| `list` | Enumerate the latest evaluator versions. | `ItemPaged[EvaluatorVersion]` |
| `list_generation_jobs` | Enumerate evaluator-generation jobs. | `ItemPaged[EvaluatorGenerationJob]` |
| `list_versions` | Enumerate versions of an evaluator. | `ItemPaged[EvaluatorVersion]` |
| `pending_upload` | Prepare an evaluator artifact upload. | `PendingUploadResponse` |
| `update_version` | Update an evaluator version. | `EvaluatorVersion` |

The current job-starting names are `begin_create_generation_job` here and under
`client.beta.datasets`, and `begin_create_optimization_job` under `client.beta.agents`.
Use these names rather than older examples with non-`begin_` creation methods.

## `client.beta.insights`

Preview analytical reports, such as evaluation clustering or comparisons.
[API reference][insights-api].

| Method | Purpose | Declared result |
| --- | --- | --- |
| `generate` | Request generation of an insight report. | `Insight` |
| `get` | Retrieve an insight report. | `Insight` |
| `list` | Enumerate insight reports. | `ItemPaged[Insight]` |

## `client.beta.memory_stores`

Preview persistent memory stores and scoped memory items.
[API reference][memory-stores-api].
[Demo notebook](../notebooks/memory-stores.ipynb).

| Method | Purpose | Declared result |
| --- | --- | --- |
| `begin_update_memories` | Extract/update memories from conversation context and return a completion poller. | `UpdateMemoriesLROPoller` |
| `create` | Create a memory store. | `MemoryStoreDetails` |
| `create_memory` | Add an explicit memory item. | `MemoryItem` |
| `delete` | Delete a memory store. | `DeleteMemoryStoreResult` |
| `delete_memory` | Delete an individual memory item. | `DeleteMemoryResult` |
| `delete_scope` | Delete memories belonging to a scope within a store. | `MemoryStoreDeleteScopeResult` |
| `get` | Retrieve a memory store. | `MemoryStoreDetails` |
| `get_memory` | Retrieve a memory item. | `MemoryItem` |
| `list` | Enumerate memory stores. | `ItemPaged[MemoryStoreDetails]` |
| `list_memories` | Enumerate memory items within a scope. | `ItemPaged[MemoryItem]` |
| `search_memories` | Find relevant memories using conversation context. | `MemoryStoreSearchResult` |
| `update` | Update a memory store. | `MemoryStoreDetails` |
| `update_memory` | Update an existing memory item. | `MemoryItem` |

## `client.beta.models`

Preview model weight assets, not model deployments.
[API reference][models-api].

| Method | Purpose | Declared result |
| --- | --- | --- |
| `create` | Upload local weights with AzCopy and register a model version; optionally wait for registration. | `ModelVersion` or `None` |
| `delete` | Delete a model version. | `None` |
| `get` | Retrieve a model version. | `ModelVersion` |
| `get_credentials` | Obtain credentials for model asset storage. | `DatasetCredential` |
| `list` | Enumerate the latest version of each model asset. | `ItemPaged[ModelVersion]` |
| `list_versions` | Enumerate a model asset's versions. | `ItemPaged[ModelVersion]` |
| `pending_create_version` | Submit asynchronous registration after uploading model weights. | `CreateAsyncResponse` |
| `pending_upload` | Provision upload storage and obtain upload information. | `ModelPendingUploadResponse` |
| `update` | Update a model version. | `ModelVersion` |

`create` performs the pending-upload, AzCopy transfer, and pending-create sequence.
AzCopy must be available on `PATH` or supplied with `azcopy_path`. By default,
`wait_for_commit=True` returns the registered model; `False` returns `None` after
the asynchronous commit is accepted. `pending_create_version` returns an
acknowledgement object, not a `begin_*` poller.

## `client.beta.red_teams`

Preview red-team runs that probe a target for safety/security risks.
[API reference][red-teams-api].
[Demo notebook](../notebooks/red-teaming.ipynb).

| Method | Purpose | Declared result |
| --- | --- | --- |
| `create` | Submit a red-team run. | `RedTeam` |
| `get` | Retrieve a red-team run. | `RedTeam` |
| `list` | Enumerate red-team runs. | `ItemPaged[RedTeam]` |

## `client.beta.routines`

Preview triggered automations and their dispatch history.
[API reference][routines-api].
[Demo notebook](../notebooks/routines.ipynb).

| Method | Purpose | Declared result |
| --- | --- | --- |
| `create_or_update` | Create or update a routine's trigger/action configuration. | `Routine` |
| `delete` | Delete a routine. | `None` |
| `disable` | Disable a routine. | `Routine` |
| `dispatch` | Queue an asynchronous dispatch of a routine. | `DispatchRoutineResult` |
| `enable` | Enable a routine. | `Routine` |
| `get` | Retrieve a routine. | `Routine` |
| `list` | Enumerate routines. | `ItemPaged[Routine]` |
| `list_runs` | Enumerate a routine's prior runs. | `ItemPaged[RoutineRun]` |

## `client.beta.schedules`

Preview schedules and their execution history.
[API reference][schedules-api].
[Demo notebook](../notebooks/schedules.ipynb).

| Method | Purpose | Declared result |
| --- | --- | --- |
| `create_or_update` | Create or update a schedule. | `Schedule` |
| `delete` | Delete a schedule. | `None` |
| `get` | Retrieve a schedule. | `Schedule` |
| `get_run` | Retrieve an individual schedule run. | `ScheduleRun` |
| `list` | Enumerate schedules. | `ItemPaged[Schedule]` |
| `list_runs` | Enumerate runs for a schedule. | `ItemPaged[ScheduleRun]` |

## `client.beta.skills`

Preview reusable skills and their versioned content.
[API reference][skills-api].
[Demo notebook](../notebooks/skills.ipynb).

| Method | Purpose | Declared result |
| --- | --- | --- |
| `create` | Create a new skill version from a skill-creation request. | `SkillVersion` |
| `create_from_files` | Upload files and create a skill version. | `SkillVersion` |
| `delete` | Delete a skill. | `DeleteSkillResult` |
| `delete_version` | Delete a specific skill version. | `DeleteSkillVersionResult` |
| `download` | Download the default skill version as ZIP content. | `Iterator[bytes]` |
| `download_version` | Download a specific skill version as ZIP content. | `Iterator[bytes]` |
| `get` | Retrieve a skill's details. | `SkillDetails` |
| `get_version` | Retrieve a specific skill version. | `SkillVersion` |
| `list` | Enumerate skills. | `ItemPaged[SkillDetails]` |
| `list_versions` | Enumerate a skill's versions. | `ItemPaged[SkillVersion]` |
| `update` | Update a skill. | `SkillDetails` |

## `client.beta.voice_agents`

**Preview container; no direct public methods.** New in 2.7.0, it groups
`conversations`, `realtime`, and `telephony`.
[API reference][voice-agents-api].
[Demo notebook](../notebooks/voice-agents.ipynb).

Voice Agent definitions/versions are managed through `client.agents`; guided
generation is available through `client.beta.agents.create_from_prompt`.

## `client.beta.voice_agents.conversations`

Preview persisted Voice Agent conversations, responses, transcripts, and recordings.
[API reference][voice-conversations-api].

| Method | Purpose | Declared result |
| --- | --- | --- |
| `delete` | Delete a voice conversation. | `None` |
| `download_audio` | Stream the conversation's merged recording. | `Iterator[bytes]` |
| `download_audio_item` | Stream an individual conversation item's audio. | `Iterator[bytes]` |
| `download_generated_audio_item` | Stream an item's generated audio. | `Iterator[bytes]` |
| `get` | Retrieve a voice conversation. | `VoiceConversation` |
| `get_audio` | Retrieve metadata for the merged recording, not its binary content. | `VoiceRecording` |
| `get_audio_item` | Retrieve metadata for an item's audio. | `VoiceAudioItem` |
| `get_generated_audio_item` | Retrieve metadata for an item's generated audio. | `VoiceGeneratedAudioItem` |
| `get_item` | Retrieve a conversation item. | `RealtimeConversationItem` |
| `get_response` | Retrieve a response in a conversation. | `VoiceResponse` |
| `list` | Enumerate voice conversations. | `ItemPaged[VoiceConversation]` |
| `list_items` | Enumerate items in a conversation. | `ItemPaged[RealtimeConversationItem]` |
| `list_response_items` | Enumerate items produced by a particular response. | `ItemPaged[RealtimeConversationItem]` |
| `list_responses` | Enumerate responses in a conversation. | `ItemPaged[VoiceResponse]` |

## `client.beta.voice_agents.realtime`

Preview live, bidirectional Voice Agent sessions. Uses the optional `voice` dependencies.
[API reference][voice-realtime-api].

| Method | Purpose | Declared result |
| --- | --- | --- |
| `connect` | Prepare a WebSocket connection for `agent_name`; optional session correlation, structured inputs, URL, headers, and query overrides are supported. Enter the returned context manager to open the connection. | `BetaRealtimeConnectionManager` |

The returned manager and connection expose additional SDK methods, listed below
under **Returned realtime objects**.

## `client.beta.voice_agents.telephony`

Preview phone bindings, active calls, transfer targets, and durable outbound-call jobs.
[API reference][voice-telephony-api].

| Method | Purpose | Declared result |
| --- | --- | --- |
| `cancel_call_job` | Request cancellation of an outbound-call job. | `TelephonyCallJob` |
| `create_binding` | Create an agent's telephony binding. | `TelephonyBinding` |
| `create_call_job` | Submit an outbound-call job. | `TelephonyCallJob` |
| `delete_binding` | Delete a telephony binding. | `None` |
| `end_call` | End an active telephony call. | `TelephonyCallRecord` |
| `get_binding` | Retrieve a telephony binding. | `TelephonyBinding` |
| `get_call` | Retrieve a call record. | `TelephonyCallRecord` |
| `get_call_job` | Retrieve an outbound-call job. | `TelephonyCallJob` |
| `get_transfer_targets` | Retrieve an agent's configured call-transfer targets. | `TelephonyTransferTargets` |
| `list_bindings` | Enumerate an agent's telephony bindings. | `ItemPaged[TelephonyBindingListItem]` |
| `list_calls` | Enumerate telephony call summaries. | `ItemPaged[TelephonyCallSummary]` |
| `replace_transfer_targets` | Replace the configured set of transfer targets. | `TelephonyTransferTargets` |
| `transfer_call` | Transfer an active call. | `TelephonyCallRecord` |
| `update_binding` | Update a telephony binding. | `TelephonyBinding` |

## Returned realtime objects

These are part of `azure-ai-projects`, not the separate OpenAI client. Here,
`manager` is the result of `client.beta.voice_agents.realtime.connect(...)`, and
`conn` is the connection yielded by `with manager as conn:`.
All of these APIs are preview. [Release-tagged realtime source][realtime-source].

The event-sending methods return `None`; receive acknowledgements and generated
content through `conn.recv()` or by iterating over `conn`.

### `manager`

Prefer the context-manager form so the connection is closed automatically.

| Method | Purpose | Declared result |
| --- | --- | --- |
| `enter` | Open the WebSocket connection explicitly instead of entering with `with`. | `BetaRealtimeConnection` |

### `conn`

The connection also exposes the read-only boolean property `closed`, which is
not a method and therefore is not a table row.

| Method | Purpose | Declared result |
| --- | --- | --- |
| `close` | Close the connection, optionally specifying a WebSocket close code and reason. | `None` |
| `recv` | Receive and parse the next typed server event; supports a timeout. | `ServerEvent` |
| `send` | Send a typed client event over the connection. | `None` |

### `conn.session`

| Method | Purpose | Declared result |
| --- | --- | --- |
| `avatar_connect` | Send the client's SDP to negotiate an avatar media session over WebRTC. | `None` |
| `update` | Update realtime session configuration. | `None` |

### `conn.input_audio_buffer`

| Method | Purpose | Declared result |
| --- | --- | --- |
| `append` | Append audio bytes or a base64 audio string to the input buffer. | `None` |
| `clear` | Discard buffered input audio. | `None` |
| `commit` | Commit buffered audio as a user turn. | `None` |

### `conn.output_audio_buffer`

| Method | Purpose | Declared result |
| --- | --- | --- |
| `clear` | Stop and clear audio currently being played back, for example on interruption. | `None` |

### `conn.conversation.item`

`conn.conversation` is a container with no direct public methods; its methods
are under `item`.

| Method | Purpose | Declared result |
| --- | --- | --- |
| `create` | Insert an item into the realtime conversation. | `None` |
| `delete` | Request deletion of a conversation item. | `None` |
| `retrieve` | Ask the server to emit a `conversation.item.retrieved` event for an item. | `None` |
| `truncate` | Truncate previously generated assistant audio at a specified playback time. | `None` |

### `conn.response`

| Method | Purpose | Declared result |
| --- | --- | --- |
| `cancel` | Cancel an in-progress response. | `None` |
| `create` | Request generation of a response. | `None` |

## Sources and verification

The inventory includes both [generated operations][generated-source] and
[handwritten operation extensions][operations-source], plus the
[public client extension][client-source] and [realtime implementation][realtime-source].
This matters for methods absent from the generated base classes, such as dataset
uploads, model registration, telemetry, and custom job pollers.

The release tag is the version-specific source of truth. Microsoft Learn links
below are rolling references and may subsequently describe a newer release.
This is a static API inventory, not a claim that live Azure operations were tested.

[pypi]: https://pypi.org/project/azure-ai-projects/2.7.0/
[changelog]: https://github.com/Azure/azure-sdk-for-python/blob/azure-ai-projects_2.7.0/sdk/ai/azure-ai-projects/CHANGELOG.md
[sdk-source]: https://github.com/Azure/azure-sdk-for-python/tree/azure-ai-projects_2.7.0/sdk/ai/azure-ai-projects
[generated-source]: https://github.com/Azure/azure-sdk-for-python/blob/azure-ai-projects_2.7.0/sdk/ai/azure-ai-projects/azure/ai/projects/operations/_operations.py
[operations-source]: https://github.com/Azure/azure-sdk-for-python/tree/azure-ai-projects_2.7.0/sdk/ai/azure-ai-projects/azure/ai/projects/operations
[client-source]: https://github.com/Azure/azure-sdk-for-python/blob/azure-ai-projects_2.7.0/sdk/ai/azure-ai-projects/azure/ai/projects/_patch.py
[realtime-source]: https://github.com/Azure/azure-sdk-for-python/blob/azure-ai-projects_2.7.0/sdk/ai/azure-ai-projects/azure/ai/projects/_realtime.py
[telemetry-source]: https://github.com/Azure/azure-sdk-for-python/blob/azure-ai-projects_2.7.0/sdk/ai/azure-ai-projects/azure/ai/projects/operations/_patch_telemetry.py
[client-api]: https://learn.microsoft.com/en-us/python/api/azure-ai-projects/azure.ai.projects.aiprojectclient?view=azure-python
[async-client-api]: https://learn.microsoft.com/en-us/python/api/azure-ai-projects/azure.ai.projects.aio.aiprojectclient?view=azure-python
[agents-api]: https://learn.microsoft.com/en-us/python/api/azure-ai-projects/azure.ai.projects.operations.agentsoperations?view=azure-python
[connections-api]: https://learn.microsoft.com/en-us/python/api/azure-ai-projects/azure.ai.projects.operations.connectionsoperations?view=azure-python
[datasets-api]: https://learn.microsoft.com/en-us/python/api/azure-ai-projects/azure.ai.projects.operations.datasetsoperations?view=azure-python
[deployments-api]: https://learn.microsoft.com/en-us/python/api/azure-ai-projects/azure.ai.projects.operations.deploymentsoperations?view=azure-python
[evaluation-rules-api]: https://learn.microsoft.com/en-us/python/api/azure-ai-projects/azure.ai.projects.operations.evaluationrulesoperations?view=azure-python
[indexes-api]: https://learn.microsoft.com/en-us/python/api/azure-ai-projects/azure.ai.projects.operations.indexesoperations?view=azure-python
[toolboxes-api]: https://learn.microsoft.com/en-us/python/api/azure-ai-projects/azure.ai.projects.operations.toolboxesoperations?view=azure-python
[beta-api]: https://learn.microsoft.com/en-us/python/api/azure-ai-projects/azure.ai.projects.operations.betaoperations?view=azure-python
[beta-agents-api]: https://learn.microsoft.com/en-us/python/api/azure-ai-projects/azure.ai.projects.operations.betaagentsoperations?view=azure-python
[agent-insight-monitors-api]: https://learn.microsoft.com/en-us/python/api/azure-ai-projects/azure.ai.projects.operations.betaagentinsightmonitorsoperations?view=azure-python
[beta-datasets-api]: https://learn.microsoft.com/en-us/python/api/azure-ai-projects/azure.ai.projects.operations.betadatasetsoperations?view=azure-python
[evaluation-taxonomies-api]: https://learn.microsoft.com/en-us/python/api/azure-ai-projects/azure.ai.projects.operations.betaevaluationtaxonomiesoperations?view=azure-python
[evaluators-api]: https://learn.microsoft.com/en-us/python/api/azure-ai-projects/azure.ai.projects.operations.betaevaluatorsoperations?view=azure-python
[insights-api]: https://learn.microsoft.com/en-us/python/api/azure-ai-projects/azure.ai.projects.operations.betainsightsoperations?view=azure-python
[memory-stores-api]: https://learn.microsoft.com/en-us/python/api/azure-ai-projects/azure.ai.projects.operations.betamemorystoresoperations?view=azure-python
[models-api]: https://learn.microsoft.com/en-us/python/api/azure-ai-projects/azure.ai.projects.operations.betamodelsoperations?view=azure-python
[red-teams-api]: https://learn.microsoft.com/en-us/python/api/azure-ai-projects/azure.ai.projects.operations.betaredteamsoperations?view=azure-python
[routines-api]: https://learn.microsoft.com/en-us/python/api/azure-ai-projects/azure.ai.projects.operations.betaroutinesoperations?view=azure-python
[schedules-api]: https://learn.microsoft.com/en-us/python/api/azure-ai-projects/azure.ai.projects.operations.betaschedulesoperations?view=azure-python
[skills-api]: https://learn.microsoft.com/en-us/python/api/azure-ai-projects/azure.ai.projects.operations.betaskillsoperations?view=azure-python
[voice-agents-api]: https://learn.microsoft.com/en-us/python/api/azure-ai-projects/azure.ai.projects.operations.betavoiceagentsoperations?view=azure-python
[voice-conversations-api]: https://learn.microsoft.com/en-us/python/api/azure-ai-projects/azure.ai.projects.operations.betavoiceagentsconversationsoperations?view=azure-python
[voice-realtime-api]: https://learn.microsoft.com/en-us/python/api/azure-ai-projects/azure.ai.projects.operations.betarealtime?view=azure-python
[voice-telephony-api]: https://learn.microsoft.com/en-us/python/api/azure-ai-projects/azure.ai.projects.operations.betavoiceagentstelephonyoperations?view=azure-python
