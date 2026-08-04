# Microsoft Foundry `client.agents` API

This document describes the synchronous Python methods available through
`AIProjectClient.agents`. It is written for this repository, which requires
`azure-ai-projects>=2.3.0`.

The API was checked on August 3, 2026, against:

- the stable Microsoft Learn Python reference;
- the published `azure-ai-projects` 2.3.0 and 2.4.0 wheels;
- the Microsoft `Azure/azure-sdk-for-python` source and samples.

`azure-ai-projects` is not upper-bounded in this repository, so a newer
installed release can add or change preview behavior. Pin the package when an
exact API contract matters.

## What `client.agents` represents

Do not construct `AgentsOperations` yourself. Create an `AIProjectClient` and
use its `agents` property:

```python
import os

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

client = AIProjectClient(
    endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential(),
)
```

In simple terms:

- **Agent**: a stable name and endpoint, such as `support-agent`.
- **Agent version**: one saved definition of that agent's model, instructions,
  tools, or hosted code. Creating another version does not require another
  agent name.
- **Agent endpoint**: decides which version receives traffic and which
  protocols it exposes.
- **Hosted-agent session**: a running sandbox for a hosted agent. Prompt agents
  do not use the session methods in this API.

Creating the first version under a new name creates the named agent resource as
well. To send prompts to an agent, use the OpenAI client returned by
`client.get_openai_client()`; `client.agents` manages the agent resources.

## Method index

| Area | Method | Simple purpose |
| --- | --- | --- |
| Versions | `create_version` | Save a new agent definition. |
| Versions | `create_version_from_manifest` | Build a version from a manifest and its inputs. |
| Hosted code | `create_version_from_code` | Upload a zip as a hosted-agent version. |
| Agents | `get` | Read one named agent. |
| Agents | `list` | List agents in the project. |
| Versions | `get_version` | Read one exact version. |
| Versions | `list_versions` | List versions of one agent. |
| Endpoint | `update_details` | Change endpoint routing, protocols, or the agent card. |
| Endpoint | `enable` | Allow new requests and sessions. |
| Endpoint | `disable` | Stop accepting new requests and sessions. |
| Delete | `delete` | Delete an agent and its versions. |
| Delete | `delete_version` | Delete one version. |
| Hosted code | `download_code` | Download a hosted version's source zip. |
| Sessions | `create_session` | Start a hosted-agent session. |
| Sessions | `get_session` | Read one session. |
| Sessions | `list_sessions` | List an agent's sessions. |
| Sessions | `stop_session` | Stop a running session. |
| Sessions | `delete_session` | Delete a session. |
| Session logs | `get_session_log_stream` | Stream a session's console logs. |
| Session files | `list_session_files` | List sandbox files and directories. |
| Session files | `upload_session_file` | Put a file in a session sandbox. |
| Session files | `download_session_file` | Read a file from a session sandbox. |
| Session files | `delete_session_file` | Delete a sandbox file or directory. |

## Conventions used below

- Signatures show the recommended typed overload. The generated SDK also
  accepts a JSON mapping or `IO[bytes]` request body for several methods. Those
  overloads are noted where relevant.
- Microsoft-generated signatures use a private sentinel such as
  `<object object>` for arguments that can instead be supplied inside `body`.
  This document shows those arguments as required in the typed overload.
- `**kwargs: Any` represents Azure Core per-request options. Most application
  code does not need it.
- List methods return `ItemPaged[T]`, a lazy iterable. Iterating can make more
  network requests to retrieve later pages.
- Service failures normally raise `azure.core.exceptions.HttpResponseError` or
  a more specific Azure Core subclass.
- Agent names must start and end with an alphanumeric character, may contain
  hyphens in the middle, and must be no longer than 63 characters.
- Metadata supports at most 16 string pairs. Keys can be at most 64 characters;
  values can be at most 512 characters.
- The asynchronous client in `azure.ai.projects.aio` exposes matching methods.
  Await individual operations and use asynchronous iteration for paged results.

## Version creation

### 1. `create_version`

**Signature**

```python
create_version(
    agent_name: str,
    *,
    definition: AgentDefinition,
    content_type: str = "application/json",
    metadata: dict[str, str] | None = None,
    description: str | None = None,
    blueprint_reference: AgentBlueprintReference | None = None,
    draft: bool | None = None,
    **kwargs: Any,
) -> AgentVersionDetails
```

**Arguments**

| Argument | Meaning |
| --- | --- |
| `agent_name` | Stable name of the agent that owns the new version. |
| `definition` | What the version runs. Common subclasses are `PromptAgentDefinition`, `HostedAgentDefinition`, `WorkflowAgentDefinition`, and `ExternalAgentDefinition`. |
| `content_type` | MIME type for the request body. Leave it as `application/json` for the typed form. |
| `metadata` | Optional searchable string key/value data. |
| `description` | Optional human-readable description. |
| `blueprint_reference` | Optional managed identity blueprint reference for the agent. Use the concrete reference subclass rather than the base class. |
| `draft` | Preview flag. `True` records a candidate version that is not treated as the default latest release. |
| `**kwargs` | Optional Azure Core request settings. |

**Returns:** `AgentVersionDetails`, including the generated version identifier.

**Simple meaning:** Save a new snapshot of an agent. If the name does not exist,
this also establishes the named agent.

```python
from azure.ai.projects.models import PromptAgentDefinition

created = client.agents.create_version(
    agent_name="support-agent",
    definition=PromptAgentDefinition(
        model=os.environ["AZURE_DEPLOYMENT_NAME"],
        instructions="Answer support questions clearly and briefly.",
    ),
    description="Initial support-agent version",
    metadata={"owner": "support"},
)

print(created.name, created.version)
```

**Notes**

- Changing a prompt, model, or tools normally means creating another version;
  `update_details` does not edit a version definition.
- Workflow agents and `draft=True` are preview features. Construct the project
  client with `allow_preview=True` when the selected definition requires it.
- A lower-level overload accepts `body: MutableMapping[str, Any] | IO[bytes]`
  instead of `definition` and the expanded fields. Prefer the typed form unless
  forwarding an already-serialized request.

### 2. `create_version_from_manifest`

**Recommended typed signature**

```python
create_version_from_manifest(
    agent_name: str,
    *,
    manifest_id: str,
    parameter_values: dict[str, Any],
    content_type: str = "application/json",
    metadata: dict[str, str] | None = None,
    description: str | None = None,
    **kwargs: Any,
) -> AgentVersionDetails
```

**Arguments**

| Argument | Meaning |
| --- | --- |
| `agent_name` | Agent that will own the imported version. |
| `manifest_id` | ID of an existing Foundry manifest. |
| `parameter_values` | Values for the manifest's declared inputs. Names and types must match that manifest. |
| `content_type` | MIME type for the request body. Leave it as `application/json` for the typed form. |
| `metadata` | Optional searchable string key/value data. |
| `description` | Optional description of the resulting version. |
| `**kwargs` | Optional Azure Core request settings. |

**Returns:** the created `AgentVersionDetails`.

**Simple meaning:** Take a reusable agent template, fill in its blanks, and save
the result as a version.

```python
created = client.agents.create_version_from_manifest(
    agent_name="support-agent",
    manifest_id="<manifest-id>",
    parameter_values={
        "model": os.environ["AZURE_DEPLOYMENT_NAME"],
        "department": "support",
    },
    description="Support agent materialized from a manifest",
)
```

**Notes**

- Replace the example keys with the exact input names declared by the manifest.
- The SDK also exposes a raw-body overload:
  `body: MutableMapping[str, Any] | IO[bytes]`. In the generated signature, the
  expanded required arguments use an internal sentinel when `body` is used.
- Microsoft publishes the method in the generated SDK reference but does not
  currently provide a matching end-to-end Python sample in the public sample
  folder. Confirm the manifest contract in the workflow that produced it.

### 3. `create_version_from_code`

**Signature**

```python
create_version_from_code(
    agent_name: str,
    *,
    definition: HostedAgentDefinition,
    code: IO[bytes],
    code_zip_sha256: str | None = None,
    description: str | None = None,
    metadata: dict[str, str] | None = None,
    **kwargs: Any,
) -> AgentVersionDetails
```

**Arguments**

| Argument | Meaning |
| --- | --- |
| `agent_name` | Agent that will own the hosted version. |
| `definition` | Hosted runtime settings, such as CPU, memory, entry point, environment variables, and protocol versions. |
| `code` | Seekable binary stream for a `.zip` file, up to 250 MB. The stream must have a `name` ending in `.zip`. |
| `code_zip_sha256` | Optional SHA-256 hex digest. The SDK calculates it when omitted. |
| `description` | Optional version description. |
| `metadata` | Optional searchable string key/value data. |
| `**kwargs` | Optional Azure Core request settings. |

**Returns:** the created hosted `AgentVersionDetails`.

**Simple meaning:** Upload application code and create a hosted agent version
that runs it.

```python
from pathlib import Path

from azure.ai.projects.models import (
    CodeConfiguration,
    CodeDependencyResolution,
    HostedAgentDefinition,
    ProtocolVersionRecord,
)

definition = HostedAgentDefinition(
    cpu="0.5",
    memory="1Gi",
    code_configuration=CodeConfiguration(
        runtime="python_3_14",
        entry_point=["python", "main.py"],
        dependency_resolution=CodeDependencyResolution.REMOTE_BUILD,
    ),
    protocol_versions=[
        ProtocolVersionRecord(protocol="responses", version="2.0.0")
    ],
)

with Path("hosted-agent.zip").open("rb") as code:
    created = client.agents.create_version_from_code(
        agent_name="hosted-support-agent",
        definition=definition,
        code=code,
    )
```

**Notes**

- This method is only for code-based hosted agents.
- The SDK rewinds and reads the stream to calculate the hash, so the stream must
  be seekable and opened in binary mode.
- The service uses the hash for integrity checking and change detection.

## Reading agents and versions

### 4. `get`

**Signature**

```python
get(agent_name: str, **kwargs: Any) -> AgentDetails
```

| Argument | Meaning |
| --- | --- |
| `agent_name` | Name of the agent to retrieve. |
| `**kwargs` | Optional Azure Core request settings. |

**Returns:** `AgentDetails` for the named agent.

**Simple meaning:** Look up the agent-level record, including endpoint details
and latest-version information.

```python
agent = client.agents.get(agent_name="support-agent")
print(agent.name, agent.state, agent.versions)
```

**Note:** Use `get_version` when the complete definition of one exact version is
needed.

### 5. `list`

**Signature**

```python
list(
    *,
    kind: str | AgentKind | None = None,
    limit: int | None = None,
    order: str | PageOrder | None = None,
    before: str | None = None,
    **kwargs: Any,
) -> ItemPaged[AgentDetails]
```

| Argument | Meaning |
| --- | --- |
| `kind` | Optional filter: `prompt`, `hosted`, `workflow`, or `external`. |
| `limit` | Page size from 1 to 100. The service default is 20. |
| `order` | Sort by creation time: `asc` or `desc`. |
| `before` | Cursor object ID used to request the preceding page. |
| `**kwargs` | Optional Azure Core request settings. |

**Returns:** a lazy `ItemPaged[AgentDetails]` iterable.

**Simple meaning:** Walk through the agents in this Foundry project.

```python
for agent in client.agents.list(kind="prompt", order="desc", limit=50):
    print(agent.name)
```

**Note:** `limit` controls the number returned per service page; iterating the
pager can retrieve additional pages.

### 6. `get_version`

**Signature**

```python
get_version(
    agent_name: str,
    agent_version: str,
    **kwargs: Any,
) -> AgentVersionDetails
```

| Argument | Meaning |
| --- | --- |
| `agent_name` | Name of the agent. |
| `agent_version` | Exact version identifier returned by a version API. |
| `**kwargs` | Optional Azure Core request settings. |

**Returns:** `AgentVersionDetails` for that exact version.

**Simple meaning:** Read one saved snapshot rather than whichever version is
latest.

```python
version = client.agents.get_version(
    agent_name="support-agent",
    agent_version=created.version,
)
print(version.definition)
```

### 7. `list_versions`

**Signature**

```python
list_versions(
    agent_name: str,
    *,
    limit: int | None = None,
    order: str | PageOrder | None = None,
    before: str | None = None,
    include_drafts: bool | None = None,
    **kwargs: Any,
) -> ItemPaged[AgentVersionDetails]
```

| Argument | Meaning |
| --- | --- |
| `agent_name` | Agent whose versions should be listed. |
| `limit` | Page size from 1 to 100. The service default is 20. |
| `order` | Sort by creation time: `asc` or `desc`. |
| `before` | Cursor object ID used to request the preceding page. |
| `include_drafts` | Preview flag that includes draft versions. Omitted or `False` returns released versions only. |
| `**kwargs` | Optional Azure Core request settings. |

**Returns:** a lazy `ItemPaged[AgentVersionDetails]` iterable.

**Simple meaning:** Show the saved history of one agent.

```python
versions = client.agents.list_versions(
    agent_name="support-agent",
    order="desc",
)

latest = next(iter(versions))
print(latest.version)
```

**Note:** Ordering descending and taking the first item is the normal way to
resolve the latest released version. Drafts are excluded by default.

## Endpoint state and routing

### 8. `update_details`

**Recommended typed signature**

```python
update_details(
    agent_name: str,
    *,
    content_type: str = "application/merge-patch+json",
    agent_endpoint: AgentEndpointConfig | None = None,
    agent_card: AgentCard | None = None,
    **kwargs: Any,
) -> AgentDetails
```

| Argument | Meaning |
| --- | --- |
| `agent_name` | Agent whose endpoint-level details should change. |
| `content_type` | MIME type for the merge-patch body. Keep the default for the typed form. |
| `agent_endpoint` | Optional routing, protocol, and authorization configuration. |
| `agent_card` | Optional discovery card describing the agent and its skills. |
| `**kwargs` | Optional Azure Core request settings. |

**Returns:** the updated `AgentDetails`.

**Simple meaning:** Change how the stable agent endpoint behaves without
changing a version's model, instructions, tools, or code.

```python
from azure.ai.projects.models import (
    AgentEndpointConfig,
    FixedRatioVersionSelectionRule,
    ProtocolConfiguration,
    ResponsesProtocolConfiguration,
    VersionSelector,
)

endpoint = AgentEndpointConfig(
    version_selector=VersionSelector(
        version_selection_rules=[
            FixedRatioVersionSelectionRule(
                agent_version=created.version,
                traffic_percentage=100,
            )
        ]
    ),
    protocol_configuration=ProtocolConfiguration(
        responses=ResponsesProtocolConfiguration()
    ),
)

updated = client.agents.update_details(
    agent_name="support-agent",
    agent_endpoint=endpoint,
)
```

**Notes**

- The service applies this as a merge patch.
- Endpoint routing can split traffic across versions when multiple selection
  rules are supplied.
- A raw-body overload accepts
  `body: MutableMapping[str, Any] | IO[bytes]` instead of the expanded fields.

### 9. `enable`

**Signature**

```python
enable(agent_name: str, **kwargs: Any) -> None
```

| Argument | Meaning |
| --- | --- |
| `agent_name` | Agent to enable. |
| `**kwargs` | Optional Azure Core request settings. |

**Simple meaning:** Let the endpoint accept new requests and sessions again.

```python
client.agents.enable(agent_name="support-agent")
```

**Note:** This operation is idempotent. Enabling an already-enabled agent still
succeeds.

### 10. `disable`

**Signature**

```python
disable(agent_name: str, **kwargs: Any) -> None
```

| Argument | Meaning |
| --- | --- |
| `agent_name` | Agent to disable. |
| `**kwargs` | Optional Azure Core request settings. |

**Simple meaning:** Stop new requests and sessions from starting.

```python
client.agents.disable(agent_name="support-agent")
```

**Notes**

- Existing active sessions are allowed to drain gracefully.
- This operation is idempotent. Disabling an already-disabled agent succeeds.
- Calling a disabled agent endpoint fails until it is enabled again.

## Deletion

### 11. `delete`

**Signature**

```python
delete(
    agent_name: str,
    *,
    force: bool | None = None,
    **kwargs: Any,
) -> DeleteAgentResponse
```

| Argument | Meaning |
| --- | --- |
| `agent_name` | Agent to delete. |
| `force` | For hosted agents, also delete active sessions instead of returning HTTP 409. The service default is `False`. |
| `**kwargs` | Optional Azure Core request settings. |

**Returns:** `DeleteAgentResponse`, whose `deleted` field reports the result.

**Simple meaning:** Remove the named agent and all of its versions.

```python
result = client.agents.delete(
    agent_name="support-agent",
    force=True,
)
print(result.deleted)
```

**Note:** `force` affects hosted agents only and can cascade-delete their
sessions. Use it deliberately.

### 12. `delete_version`

**Signature**

```python
delete_version(
    agent_name: str,
    agent_version: str,
    *,
    force: bool | None = None,
    **kwargs: Any,
) -> DeleteAgentVersionResponse
```

| Argument | Meaning |
| --- | --- |
| `agent_name` | Agent that owns the version. |
| `agent_version` | Exact version to delete. |
| `force` | For hosted agents, also delete sessions using this version instead of returning HTTP 409. The service default is `False`. |
| `**kwargs` | Optional Azure Core request settings. |

**Returns:** `DeleteAgentVersionResponse`, whose `deleted` field reports the
result.

**Simple meaning:** Remove one saved snapshot and leave other versions alone.

```python
result = client.agents.delete_version(
    agent_name="support-agent",
    agent_version=created.version,
    force=True,
)
print(result.deleted)
```

**Note:** Check endpoint routing before deleting a version that may currently
receive traffic.

## Hosted code

### 13. `download_code`

**Signature**

```python
download_code(
    agent_name: str,
    *,
    agent_version: str | None = None,
    **kwargs: Any,
) -> Iterator[bytes]
```

| Argument | Meaning |
| --- | --- |
| `agent_name` | Code-based hosted agent to download from. |
| `agent_version` | Optional exact version. Omit it to use the latest version. |
| `**kwargs` | Optional Azure Core request settings. |

**Returns:** an iterator of byte chunks containing the original zip.

**Simple meaning:** Get back the source zip previously uploaded for a hosted
agent version.

```python
from pathlib import Path

chunks = client.agents.download_code(
    agent_name="hosted-support-agent",
    agent_version=created.version,
)
Path("downloaded-agent.zip").write_bytes(b"".join(chunks))
```

**Notes**

- This applies only to code-based hosted agents.
- The downloaded bytes have the SHA-256 digest recorded in the version's
  `code_configuration.content_hash`.
- Stream the chunks directly to a file instead of joining them when the zip can
  be large.

## Hosted-agent sessions

The methods in this section work with hosted agents only.

### 14. `create_session`

**Recommended typed signature**

```python
create_session(
    agent_name: str,
    *,
    version_indicator: VersionIndicator,
    content_type: str = "application/json",
    agent_session_id: str | None = None,
    **kwargs: Any,
) -> AgentSessionResource
```

| Argument | Meaning |
| --- | --- |
| `agent_name` | Hosted agent for which to start a session. |
| `version_indicator` | Selects the backing version. The current concrete type is `VersionRefIndicator`. |
| `content_type` | MIME type for the request body. Leave it as `application/json` for the typed form. |
| `agent_session_id` | Optional caller-chosen ID, unique within the agent endpoint. The service generates one when omitted. |
| `**kwargs` | Optional Azure Core request settings. |

**Returns:** the created `AgentSessionResource`.

**Simple meaning:** Start an isolated running workspace for one hosted-agent
version.

```python
from azure.ai.projects.models import VersionRefIndicator

session = client.agents.create_session(
    agent_name="hosted-support-agent",
    version_indicator=VersionRefIndicator(
        agent_version=created.version,
    ),
)
print(session.agent_session_id, session.status)
```

**Notes**

- Session-mutating operations enforce ownership using the caller's identity.
- A raw-body overload accepts
  `body: MutableMapping[str, Any] | IO[bytes]` instead of expanded fields.

### 15. `get_session`

**Signature**

```python
get_session(
    agent_name: str,
    session_id: str,
    **kwargs: Any,
) -> AgentSessionResource
```

| Argument | Meaning |
| --- | --- |
| `agent_name` | Hosted agent that owns the session. |
| `session_id` | Session identifier, normally `agent_session_id` from the create response. |
| `**kwargs` | Optional Azure Core request settings. |

**Returns:** the matching `AgentSessionResource`.

**Simple meaning:** Check one session's identity, version, and current status.

```python
session = client.agents.get_session(
    agent_name="hosted-support-agent",
    session_id=session_id,
)
print(session.status)
```

### 16. `list_sessions`

**Signature**

```python
list_sessions(
    agent_name: str,
    *,
    limit: int | None = None,
    order: str | PageOrder | None = None,
    before: str | None = None,
    **kwargs: Any,
) -> ItemPaged[AgentSessionResource]
```

| Argument | Meaning |
| --- | --- |
| `agent_name` | Hosted agent whose sessions should be listed. |
| `limit` | Page size from 1 to 100. The service default is 20. |
| `order` | Sort by creation time: `asc` or `desc`. |
| `before` | Cursor object ID used to request the preceding page. |
| `**kwargs` | Optional Azure Core request settings. |

**Returns:** a lazy `ItemPaged[AgentSessionResource]` iterable.

**Simple meaning:** Show the sessions belonging to one hosted-agent endpoint.

```python
for session in client.agents.list_sessions(
    agent_name="hosted-support-agent",
    order="desc",
):
    print(session.agent_session_id, session.status)
```

### 17. `stop_session`

**Signature**

```python
stop_session(
    agent_name: str,
    session_id: str,
    **kwargs: Any,
) -> None
```

| Argument | Meaning |
| --- | --- |
| `agent_name` | Hosted agent that owns the session. |
| `session_id` | Session to stop. |
| `**kwargs` | Optional Azure Core request settings. |

**Simple meaning:** Terminate the running session but keep its session resource
until it is deleted.

```python
client.agents.stop_session(
    agent_name="hosted-support-agent",
    session_id=session_id,
)
```

**Note:** A successful request returns HTTP 204 No Content.

### 18. `delete_session`

**Signature**

```python
delete_session(
    agent_name: str,
    session_id: str,
    **kwargs: Any,
) -> None
```

| Argument | Meaning |
| --- | --- |
| `agent_name` | Hosted agent that owns the session. |
| `session_id` | Session to delete. |
| `**kwargs` | Optional Azure Core request settings. |

**Simple meaning:** Remove the session and its sandbox.

```python
client.agents.delete_session(
    agent_name="hosted-support-agent",
    session_id=session_id,
)
```

**Note:** The operation is synchronous and returns HTTP 204 whether the session
was deleted or was already absent.

## Hosted-agent session logs

### 19. `get_session_log_stream`

**Published SDK signature**

```python
get_session_log_stream(
    agent_name: str,
    agent_version: str,
    session_id: str,
    **kwargs: Any,
) -> SessionLogEvent
```

| Argument | Meaning |
| --- | --- |
| `agent_name` | Hosted agent whose logs should be read. |
| `agent_version` | Version backing the session. |
| `session_id` | Session whose stdout and stderr should be read. |
| `**kwargs` | Optional Azure Core request settings. |

**Simple meaning:** Open a live feed of console output from the hosted session.

```python
stream = client.agents.get_session_log_stream(
    agent_name="hosted-support-agent",
    agent_version=agent_version,
    session_id=session_id,
)

for chunk in stream:
    print(chunk.decode("utf-8", errors="replace"), end="")
```

**Important notes**

- The generated `azure-ai-projects` 2.3.0 and 2.4.0 annotations and Microsoft
    Learn return type are `SessionLogEvent`.
- The official synchronous SDK sample treats the returned object as an iterable
  of byte chunks containing a Server-Sent Events (SSE) stream. The example
  above follows that observed public sample behavior.
- Each SSE frame has `event: log` and one or more `data:` lines. Microsoft says
  the data should be treated as opaque text even though it is currently often
  JSON-formatted.
- The connection remains open until the client or server closes it. Production
  consumers should parse complete SSE frames and handle reconnection.

## Hosted-agent session files

Session file paths are relative to the session home directory, even when an
example starts a path with `/`.

### 20. `list_session_files`

**Signature**

```python
list_session_files(
    agent_name: str,
    session_id: str,
    *,
    path: str | None = None,
    limit: int | None = None,
    order: str | PageOrder | None = None,
    before: str | None = None,
    **kwargs: Any,
) -> ItemPaged[SessionDirectoryEntry]
```

| Argument | Meaning |
| --- | --- |
| `agent_name` | Hosted agent that owns the session. |
| `session_id` | Session whose sandbox should be listed. |
| `path` | Optional directory path. Omit it for the session home directory. |
| `limit` | Page size from 1 to 100. The service default is 20. |
| `order` | Sort by creation time: `asc` or `desc`. |
| `before` | Cursor object ID used to request the preceding page. |
| `**kwargs` | Optional Azure Core request settings. |

**Returns:** a lazy `ItemPaged[SessionDirectoryEntry]` iterable.

**Simple meaning:** List the immediate files and folders in one sandbox
directory.

```python
entries = client.agents.list_session_files(
    agent_name="hosted-support-agent",
    session_id=session_id,
    path="/data",
)

for entry in entries:
    print(entry.name, entry.size, entry.is_directory)
```

**Note:** The method lists only immediate children; it does not recursively walk
subdirectories.

### 21. `upload_session_file`

**Signature**

```python
upload_session_file(
    agent_name: str,
    session_id: str,
    content: bytes,
    *,
    path: str,
    **kwargs: Any,
) -> SessionFileWriteResult
```

| Argument | Meaning |
| --- | --- |
| `agent_name` | Hosted agent that owns the session. |
| `session_id` | Destination session. |
| `content` | Complete binary file content, up to 50 MB. |
| `path` | Destination path relative to the session home directory. |
| `**kwargs` | Optional Azure Core request settings. |

**Returns:** `SessionFileWriteResult` describing the completed write.

**Simple meaning:** Copy a local file into the running session's sandbox.

```python
from pathlib import Path

result = client.agents.upload_session_file(
    agent_name="hosted-support-agent",
    session_id=session_id,
    content=Path("input.csv").read_bytes(),
    path="/data/input.csv",
)
print(result)
```

**Note:** This API accepts one `bytes` value rather than a streaming upload and
rejects payloads larger than 50 MB.

### 22. `download_session_file`

**Signature**

```python
download_session_file(
    agent_name: str,
    session_id: str,
    *,
    path: str,
    **kwargs: Any,
) -> Iterator[bytes]
```

| Argument | Meaning |
| --- | --- |
| `agent_name` | Hosted agent that owns the session. |
| `session_id` | Source session. |
| `path` | File path relative to the session home directory. |
| `**kwargs` | Optional Azure Core request settings. |

**Returns:** an iterator of downloaded byte chunks.

**Simple meaning:** Copy a sandbox file back to the client.

```python
from pathlib import Path

chunks = client.agents.download_session_file(
    agent_name="hosted-support-agent",
    session_id=session_id,
    path="/data/output.csv",
)
Path("output.csv").write_bytes(b"".join(chunks))
```

**Note:** For large files, write each chunk as it arrives instead of joining all
chunks in memory.

### 23. `delete_session_file`

**Signature**

```python
delete_session_file(
    agent_name: str,
    session_id: str,
    *,
    path: str,
    recursive: bool | None = None,
    **kwargs: Any,
) -> None
```

| Argument | Meaning |
| --- | --- |
| `agent_name` | Hosted agent that owns the session. |
| `session_id` | Session containing the target. |
| `path` | File or directory path relative to the session home directory. |
| `recursive` | Delete directory contents recursively. The service default is `False`. |
| `**kwargs` | Optional Azure Core request settings. |

**Simple meaning:** Remove a file or directory from the session sandbox.

```python
client.agents.delete_session_file(
    agent_name="hosted-support-agent",
    session_id=session_id,
    path="/data",
    recursive=True,
)
```

**Note:** Deleting a non-empty directory with `recursive=False` returns HTTP 409
Conflict.

## Common operation sequences

### Prompt agent

1. Call `create_version` with `PromptAgentDefinition`.
2. Optionally call `update_details` to route the named endpoint to that version.
3. Call the agent through `client.get_openai_client()`.
4. Create another version for definition changes.
5. Delete old versions with `delete_version` when they are no longer routed.

### Code-based hosted agent

1. Call `create_version_from_code`.
2. Wait until the hosted version becomes active.
3. Call `update_details` to route traffic to it.
4. Call `create_session` when an explicit hosted sandbox is needed.
5. Use the session log and file methods while it is active.
6. Call `stop_session` or `delete_session` during cleanup.
7. Call `delete_version(..., force=True)` only when cascading session deletion is
   intended.

## Microsoft sources

- [AIProjectClient Python reference](https://learn.microsoft.com/python/api/azure-ai-projects/azure.ai.projects.aiprojectclient)
- [AgentsOperations Python reference](https://learn.microsoft.com/python/api/azure-ai-projects/azure.ai.projects.operations.agentsoperations)
- [Azure AI Projects Python SDK source](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/ai/azure-ai-projects)
- [Agent SDK samples](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/ai/azure-ai-projects/samples/agents)
- [Hosted-agent SDK samples](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/ai/azure-ai-projects/samples/hosted_agents)
- [Microsoft Foundry REST API reference](https://learn.microsoft.com/rest/api/aifoundry/)
