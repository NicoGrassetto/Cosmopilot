"""Public client.agents integration tests for azure-ai-projects==2.7.0.

References:
https://learn.microsoft.com/python/api/azure-ai-projects/azure.ai.projects.operations.agentsoperations
https://github.com/Azure/azure-sdk-for-python/tree/azure-ai-projects_2.7.0/sdk/ai/azure-ai-projects

All tests call real services. There are no pytest fixtures or private SDK calls.
Each test owns its credential, client, resources, assertions, and cleanup.
Use a disposable preview-enabled project, never a production project.
Environment: AZURE_AI_PROJECT_ENDPOINT and AZURE_DEPLOYMENT_NAME.
Additional prerequisites for the corresponding cases:
- AGENTS_TEST_CODE_ZIP: working, readiness-capable hosted app zip (at most 10 MiB).
- AGENTS_TEST_HOSTED_DEFINITION_JSON: its HostedAgentDefinition JSON, including
  cpu, memory, code_configuration, and protocol_versions. No embedded secrets.
- AGENTS_TEST_BLUEPRINT_ID: dedicated pre-provisioned test identity blueprint.
- AGENTS_TEST_MANIFEST_ID, AGENTS_TEST_MANIFEST_PARAMETERS_JSON, and
  AGENTS_TEST_MANIFEST_DEFINITION_JSON: a harmless prompt-agent manifest, its
  non-empty input object, and expected materialized definition fields.
- AGENTS_TEST_BOT_SERVICE_ARM_ID and AGENTS_TEST_BOT_APP_ID: dedicated test bot
  ARM resource ID and public application ID, for Teams package generation.

Export the selected azd environment before live execution. Tests do not load .env.
With the root .venv interpreter and PYTHONPATH=src, collect without service calls:
    python -m pytest --collect-only -q tests/test_agents.py
Only after explicitly authorizing live execution:
    python -m pytest -m integration tests/test_agents.py
Missing prerequisites fail rather than skip. Live execution can incur cost.

API inventory: each method below has exactly one test_<method> function.
Names before ';' are positional-or-keyword; names after it are keyword-only.
Optional parameters default to None, unless another default is shown.
All methods accept **kwargs; arbitrary Azure Core pipeline options are outside
the finite method-parameter inventory. The JSON/IO overloads below replace the
expanded body keywords with a positional body (JSON mapping or IO[bytes]).
content_type defaults to application/json, except update_details (merge-patch)
and upload_session_file (application/octet-stream). The inherited public
digital_worker_type keyword is forwarded by create_version through **kwargs.

| Method | Parameters | Cases / assertions | Coverage Gaps |
| --- | --- | --- | --- |
| create_version | agent_name; definition, metadata?, description?, blueprint_reference?, draft?, digital_worker_type?, content_type | expanded/JSON/IO; persisted fields; draft; blueprint; metadata boundary | none |
| create_version_from_code | agent_name; definition, code, code_zip_sha256?, description?, metadata? | computed/explicit hash; persisted fields | none |
| create_version_from_manifest | agent_name; manifest_id, parameter_values, metadata?, description?, content_type | expanded/JSON/IO; materialized inputs | manifest prerequisites |
| get | agent_name | exact name and latest version | none |
| get_version | agent_name, agent_version | exact immutable definition | none |
| list | ; kind?, limit?, order?, before? | default/filtered; page limits; order; cursor | none |
| list_versions | agent_name; limit?, order?, before?, include_drafts? | draft filtering; pages; order; cursor | none |
| update_details | agent_name; agent_endpoint?, agent_card?, content_type | expanded/JSON/IO; persisted routing/card | none |
| enable | agent_name | enabled state and idempotence | none |
| disable | agent_name | disabled state and idempotence | none |
| delete | agent_name; force? | deletion; active-session conflict; force cascade | none |
| delete_version | agent_name, agent_version; force? | exact version; active-session conflict; force cascade | none |
| download_code | agent_name; agent_version? | latest/explicit version; exact bytes/hash | none |
| create_session | agent_name; version_indicator, agent_session_id?, content_type | expanded/JSON/IO; generated/explicit ID | none |
| get_session | agent_name, session_id | exact session and version | none |
| list_sessions | agent_name; limit?, order?, before? | pages; order; cursor | none |
| stop_session | agent_name, session_id | idle state and stopped_at | none |
| delete_session | agent_name, session_id | absent resource and idempotence | none |
| get_session_log_stream | agent_name, agent_version, session_id | bounded SSE frame; response closed | SDK annotation says model but implementation streams bytes |
| upload_session_file | agent_name, session_id, content; path, content_type | bytes/IO; path/length/content | none |
| download_session_file | agent_name, session_id; path | exact binary content | none |
| list_session_files | agent_name, session_id; path?, limit?, order?, before? | root/directory; pages; cursor | none |
| delete_session_file | agent_name, session_id; path, recursive? | file/directory deletion; non-empty conflict | none |
| get_microsoft365_publish_defaults | agent_name; publish_as_digital_worker? | omitted/false/true defaults | none |
| get_microsoft365_package | agent_name; publish_scope, PUBLISH_OPTIONS, content_type | expanded/JSON/IO; manifest/icons; invalid autopilot combination | successful autopilot permission grants/message delivery untested |
| publish_to_microsoft365 | agent_name; publish_scope, PUBLISH_OPTIONS, content_type | expanded/JSON/IO; nonexistent-agent rejection | no successful tenant publication or permission-grant validation |

PUBLISH_OPTIONS (all optional, default None): agent_display_name,
bot_service_arm_id, publish_as_autopilot, access_boundaries,
optional_permission_scopes, can_respond_without_mention, app_version,
short_description, full_description, developer_name, developer_website_url,
privacy_url, terms_of_use_url, color_icon_base64, outline_icon_base64.
No successful publishing is attempted: client.agents has no inverse operation
to remove a published Teams app or undo blueprint permission grants.
Service behavior and cleanup remain unverified until a live run is authorized.
"""

import json
import os
from base64 import b64decode, b64encode
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from struct import pack
from tempfile import TemporaryDirectory
from time import monotonic, sleep
from typing import Any, cast
from uuid import uuid4
from zipfile import ZipFile, is_zipfile
from zlib import compress, crc32

import pytest
from azure.ai.projects import AIProjectClient, models
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
from azure.core.rest import HttpResponse
from azure.identity import DefaultAzureCredential

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("case", ["minimal", "explicit-sha256"])
def test_create_version_from_code(case):
    """Upload a named zip stream and verify computed/explicit hashes and optional metadata."""
    name = f"pytest-agents-{uuid4().hex[:16]}"
    path = Path(os.environ["AGENTS_TEST_CODE_ZIP"])
    assert path.suffix.lower() == ".zip" and is_zipfile(path)
    assert 0 < path.stat().st_size <= 10 * 1024 * 1024
    definition = models.HostedAgentDefinition(json.loads(os.environ["AGENTS_TEST_HOSTED_DEFINITION_JSON"]))
    assert definition.code_configuration is not None and definition.container_configuration is None
    digest = sha256(path.read_bytes()).hexdigest()
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=credential, allow_preview=True
        ) as client,
    ):
        try:
            with path.open("rb") as code:
                if case == "minimal":
                    created = client.agents.create_version_from_code(
                        agent_name=name, definition=definition, code=code
                    )
                else:
                    created = client.agents.create_version_from_code(
                        agent_name=name, definition=definition, code=code,
                        code_zip_sha256=digest, description="Explicit digest regression",
                        metadata={"suite": "agents", "case": case},
                    )
            retrieved = client.agents.get_version(agent_name=name, agent_version=created.version)
            assert retrieved.id == created.id and retrieved.name == name
            assert isinstance(retrieved.definition, models.HostedAgentDefinition)
            assert retrieved.definition.cpu == definition.cpu
            assert retrieved.definition.memory == definition.memory
            assert retrieved.definition.code_configuration is not None
            assert retrieved.definition.code_configuration.content_hash == digest
            assert retrieved.definition.code_configuration.runtime == definition.code_configuration.runtime
            assert retrieved.definition.code_configuration.entry_point == definition.code_configuration.entry_point
            if case != "minimal":
                assert retrieved.description == "Explicit digest regression"
                assert retrieved.metadata == {"suite": "agents", "case": case}
        finally:
            try:
                client.agents.delete(agent_name=name, force=True)
            except ResourceNotFoundError:
                pass
            with pytest.raises(ResourceNotFoundError):
                client.agents.get(agent_name=name)


@pytest.mark.parametrize("case", ["latest", "explicit-version"])
def test_download_code(case):
    """Distinguish latest and explicitly selected zip versions by their exact bytes and SHA-256."""
    name = f"pytest-agents-{uuid4().hex[:16]}"
    original = Path(os.environ["AGENTS_TEST_CODE_ZIP"])
    assert original.suffix.lower() == ".zip" and is_zipfile(original)
    assert 0 < original.stat().st_size <= 10 * 1024 * 1024
    definition = models.HostedAgentDefinition(json.loads(os.environ["AGENTS_TEST_HOSTED_DEFINITION_JSON"]))
    with (
        TemporaryDirectory() as directory,
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=credential, allow_preview=True
        ) as client,
    ):
        changed = Path(directory) / "changed-code.zip"
        changed.write_bytes(original.read_bytes())
        with ZipFile(changed, "a") as archive:
            archive.writestr(f"pytest-{uuid4().hex}.txt", "Second regression version\n")
        try:
            with original.open("rb") as code:
                first = client.agents.create_version_from_code(agent_name=name, definition=definition, code=code)
            with changed.open("rb") as code:
                second = client.agents.create_version_from_code(agent_name=name, definition=definition, code=code)
            if case == "latest":
                content = b"".join(client.agents.download_code(agent_name=name))
                expected_path, expected_version = changed, second
            else:
                content = b"".join(client.agents.download_code(agent_name=name, agent_version=first.version))
                expected_path, expected_version = original, first
            assert content == expected_path.read_bytes()
            assert isinstance(expected_version.definition, models.HostedAgentDefinition)
            assert expected_version.definition.code_configuration is not None
            assert sha256(content).hexdigest() == expected_version.definition.code_configuration.content_hash
            assert original.read_bytes() != changed.read_bytes()
        finally:
            try:
                client.agents.delete(agent_name=name, force=True)
            except ResourceNotFoundError:
                pass
            with pytest.raises(ResourceNotFoundError):
                client.agents.get(agent_name=name)


@pytest.mark.parametrize("case", ["minimal", "active-session-force-false", "active-session-force-true"])
def test_delete(case):
    """Delete an owned agent, rejecting active hosted sessions unless force is explicitly true."""
    name = f"pytest-agents-{uuid4().hex[:16]}"
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=credential, allow_preview=True,
            connection_timeout=10, read_timeout=60, retry_total=2,
        ) as client,
    ):
        try:
            if case == "minimal":
                client.agents.create_version(
                    agent_name=name,
                    definition=models.PromptAgentDefinition(model=os.environ["AZURE_DEPLOYMENT_NAME"]),
                )
                deleted = client.agents.delete(agent_name=name)
            else:
                path = Path(os.environ["AGENTS_TEST_CODE_ZIP"])
                assert path.suffix.lower() == ".zip" and is_zipfile(path)
                assert 0 < path.stat().st_size <= 10 * 1024 * 1024
                definition = models.HostedAgentDefinition(json.loads(os.environ["AGENTS_TEST_HOSTED_DEFINITION_JSON"]))
                with path.open("rb") as code:
                    hosted = client.agents.create_version_from_code(agent_name=name, definition=definition, code=code)
                deadline = monotonic() + 300
                while hosted.status != "active":
                    assert hosted.status != "failed" and monotonic() < deadline, "Hosted agent did not become active."
                    sleep(2)
                    hosted = client.agents.get_version(agent_name=name, agent_version=hosted.version)
                session = client.agents.create_session(
                    agent_name=name, version_indicator=models.VersionRefIndicator(agent_version=hosted.version)
                )
                deadline = monotonic() + 300
                while session.status != "active":
                    assert session.status != "failed" and monotonic() < deadline, "Session did not become active."
                    sleep(2)
                    session = client.agents.get_session(agent_name=name, session_id=session.agent_session_id)
                if case == "active-session-force-false":
                    with pytest.raises(HttpResponseError) as raised:
                        client.agents.delete(agent_name=name, force=False)
                    assert raised.value.status_code == 409
                    assert client.agents.get_session(agent_name=name, session_id=session.agent_session_id).agent_session_id == session.agent_session_id
                    return
                deleted = client.agents.delete(agent_name=name, force=True)
                with pytest.raises(ResourceNotFoundError):
                    client.agents.get_session(agent_name=name, session_id=session.agent_session_id)
            assert deleted.name == name and deleted.deleted is True
            with pytest.raises(ResourceNotFoundError):
                client.agents.get(agent_name=name)
        finally:
            try:
                client.agents.delete(agent_name=name, force=True)
            except ResourceNotFoundError:
                pass
            with pytest.raises(ResourceNotFoundError):
                client.agents.get(agent_name=name)


@pytest.mark.parametrize("case", ["minimal", "active-session-force-false", "active-session-force-true"])
def test_delete_version(case):
    """Delete an exact version; verify version isolation, active-session conflicts, and force cascading."""
    name = f"pytest-agents-{uuid4().hex[:16]}"
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=credential, allow_preview=True,
            connection_timeout=10, read_timeout=60, retry_total=2,
        ) as client,
    ):
        try:
            if case == "minimal":
                definition = models.PromptAgentDefinition(model=os.environ["AZURE_DEPLOYMENT_NAME"])
                retained = client.agents.create_version(agent_name=name, definition=definition)
                created = client.agents.create_version(agent_name=name, definition=definition)
                deleted = client.agents.delete_version(agent_name=name, agent_version=created.version)
                assert client.agents.get_version(agent_name=name, agent_version=retained.version).id == retained.id
            else:
                path = Path(os.environ["AGENTS_TEST_CODE_ZIP"])
                assert path.suffix.lower() == ".zip" and is_zipfile(path)
                assert 0 < path.stat().st_size <= 10 * 1024 * 1024
                hosted_definition = models.HostedAgentDefinition(json.loads(os.environ["AGENTS_TEST_HOSTED_DEFINITION_JSON"]))
                with path.open("rb") as code:
                    created = client.agents.create_version_from_code(agent_name=name, definition=hosted_definition, code=code)
                deadline = monotonic() + 300
                while created.status != "active":
                    assert created.status != "failed" and monotonic() < deadline, "Hosted agent did not become active."
                    sleep(2)
                    created = client.agents.get_version(agent_name=name, agent_version=created.version)
                session = client.agents.create_session(
                    agent_name=name, version_indicator=models.VersionRefIndicator(agent_version=created.version)
                )
                deadline = monotonic() + 300
                while session.status != "active":
                    assert session.status != "failed" and monotonic() < deadline, "Session did not become active."
                    sleep(2)
                    session = client.agents.get_session(agent_name=name, session_id=session.agent_session_id)
                if case == "active-session-force-false":
                    with pytest.raises(HttpResponseError) as raised:
                        client.agents.delete_version(agent_name=name, agent_version=created.version, force=False)
                    assert raised.value.status_code == 409
                    assert client.agents.get_version(agent_name=name, agent_version=created.version).id == created.id
                    assert client.agents.get_session(agent_name=name, session_id=session.agent_session_id).agent_session_id == session.agent_session_id
                    return
                deleted = client.agents.delete_version(agent_name=name, agent_version=created.version, force=True)
                with pytest.raises(ResourceNotFoundError):
                    client.agents.get_session(agent_name=name, session_id=session.agent_session_id)
            assert deleted.name == name and deleted.version == created.version and deleted.deleted is True
            with pytest.raises(ResourceNotFoundError):
                client.agents.get_version(agent_name=name, agent_version=created.version)
        finally:
            try:
                client.agents.delete(agent_name=name, force=True)
            except ResourceNotFoundError:
                pass
            with pytest.raises(ResourceNotFoundError):
                client.agents.get(agent_name=name)


@pytest.mark.parametrize("case", ["minimal", "expanded", "json", "stream"])
def test_create_session(case):
    """Create generated or caller-named sessions using expanded, JSON, and binary JSON bodies."""
    name = f"pytest-agents-{uuid4().hex[:16]}"
    path = Path(os.environ["AGENTS_TEST_CODE_ZIP"])
    assert path.suffix.lower() == ".zip" and is_zipfile(path)
    assert 0 < path.stat().st_size <= 10 * 1024 * 1024
    definition = models.HostedAgentDefinition(json.loads(os.environ["AGENTS_TEST_HOSTED_DEFINITION_JSON"]))
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=credential, allow_preview=True,
            connection_timeout=10, read_timeout=60, retry_total=2,
        ) as client,
    ):
        try:
            with path.open("rb") as code:
                hosted = client.agents.create_version_from_code(agent_name=name, definition=definition, code=code)
            deadline = monotonic() + 300
            while hosted.status != "active":
                assert hosted.status != "failed" and monotonic() < deadline, "Hosted agent did not become active."
                sleep(2)
                hosted = client.agents.get_version(agent_name=name, agent_version=hosted.version)
            indicator = models.VersionRefIndicator(agent_version=hosted.version)
            session_id = str(uuid4())
            if case == "minimal":
                session = client.agents.create_session(agent_name=name, version_indicator=indicator)
                session_id = session.agent_session_id
            elif case == "expanded":
                session = client.agents.create_session(
                    agent_name=name, version_indicator=indicator, agent_session_id=session_id,
                    content_type="application/json; charset=utf-8",
                )
            else:
                payload = {"version_indicator": indicator.as_dict(), "agent_session_id": session_id}
                with BytesIO(json.dumps(payload).encode("utf-8")) as body:
                    session = client.agents.create_session(
                        agent_name=name, body=payload if case == "json" else body,
                        content_type="application/json; charset=utf-8",
                    )
            assert session.agent_session_id == session_id and session_id
            assert session.version_indicator.as_dict() == indicator.as_dict()
            deadline = monotonic() + 300
            while session.status != "active":
                assert session.status != "failed" and monotonic() < deadline, "Session did not become active."
                sleep(2)
                session = client.agents.get_session(agent_name=name, session_id=session_id)
            assert session.version_indicator.as_dict() == indicator.as_dict()
            assert session.expires_at > session.created_at
        finally:
            try:
                client.agents.delete(agent_name=name, force=True)
            except ResourceNotFoundError:
                pass
            with pytest.raises(ResourceNotFoundError):
                client.agents.get(agent_name=name)


def test_get_session():
    """Retrieve the exact session and its persisted version indicator."""
    name = f"pytest-agents-{uuid4().hex[:16]}"
    path = Path(os.environ["AGENTS_TEST_CODE_ZIP"])
    assert path.suffix.lower() == ".zip" and is_zipfile(path)
    assert 0 < path.stat().st_size <= 10 * 1024 * 1024
    definition = models.HostedAgentDefinition(json.loads(os.environ["AGENTS_TEST_HOSTED_DEFINITION_JSON"]))
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=credential, allow_preview=True,
            connection_timeout=10, read_timeout=60, retry_total=2,
        ) as client,
    ):
        try:
            with path.open("rb") as code:
                hosted = client.agents.create_version_from_code(agent_name=name, definition=definition, code=code)
            deadline = monotonic() + 300
            while hosted.status != "active":
                assert hosted.status != "failed" and monotonic() < deadline, "Hosted agent did not become active."
                sleep(2)
                hosted = client.agents.get_version(agent_name=name, agent_version=hosted.version)
            created = client.agents.create_session(
                agent_name=name, version_indicator=models.VersionRefIndicator(agent_version=hosted.version)
            )
            retrieved = client.agents.get_session(agent_name=name, session_id=created.agent_session_id)
            assert retrieved.agent_session_id == created.agent_session_id
            assert retrieved.version_indicator.as_dict() == created.version_indicator.as_dict()
            assert retrieved.status in {"creating", "active", "idle"}
        finally:
            try:
                client.agents.delete(agent_name=name, force=True)
            except ResourceNotFoundError:
                pass
            with pytest.raises(ResourceNotFoundError):
                client.agents.get(agent_name=name)


@pytest.mark.parametrize("case", ["minimal", "asc", "desc", "before"])
def test_list_sessions(case):
    """List an owned agent's sessions with paging, ordering, and cursor assertions."""
    name = f"pytest-agents-{uuid4().hex[:16]}"
    path = Path(os.environ["AGENTS_TEST_CODE_ZIP"])
    assert path.suffix.lower() == ".zip" and is_zipfile(path)
    assert 0 < path.stat().st_size <= 10 * 1024 * 1024
    definition = models.HostedAgentDefinition(json.loads(os.environ["AGENTS_TEST_HOSTED_DEFINITION_JSON"]))
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=credential, allow_preview=True,
            connection_timeout=10, read_timeout=60, retry_total=2,
        ) as client,
    ):
        try:
            with path.open("rb") as code:
                hosted = client.agents.create_version_from_code(agent_name=name, definition=definition, code=code)
            deadline = monotonic() + 300
            while hosted.status != "active":
                assert hosted.status != "failed" and monotonic() < deadline, "Hosted agent did not become active."
                sleep(2)
                hosted = client.agents.get_version(agent_name=name, agent_version=hosted.version)
            sessions = []
            for index in range(2):
                session = client.agents.create_session(
                    agent_name=name,
                    version_indicator=models.VersionRefIndicator(agent_version=hosted.version),
                    agent_session_id=str(uuid4()),
                )
                sessions.append(session.agent_session_id)
            order = models.PageOrder.DESC if case == "desc" else "asc"
            if case == "minimal":
                pager = client.agents.list_sessions(agent_name=name)
            else:
                pager = client.agents.list_sessions(agent_name=name, limit=1, order=order)
            listed = []
            for page_number, page in enumerate(pager.by_page(), start=1):
                assert page_number <= 10
                items = list(page)
                if case != "minimal":
                    assert len(items) <= 1
                listed.extend(items)
            assert {item.agent_session_id for item in listed} == set(sessions)
            if case != "minimal":
                timestamps = [item.created_at for item in listed]
                assert timestamps == sorted(timestamps, reverse=order == "desc")
            if case == "before":
                previous = list(client.agents.list_sessions(
                    agent_name=name, limit=1, order="asc", before=listed[-1].agent_session_id
                ))
                assert [item.agent_session_id for item in previous] == [item.agent_session_id for item in listed[:-1]]
        finally:
            try:
                client.agents.delete(agent_name=name, force=True)
            except ResourceNotFoundError:
                pass
            with pytest.raises(ResourceNotFoundError):
                client.agents.get(agent_name=name)


def test_stop_session():
    """Stop a running session and wait for the persisted idle state and stop timestamp."""
    name = f"pytest-agents-{uuid4().hex[:16]}"
    path = Path(os.environ["AGENTS_TEST_CODE_ZIP"])
    assert path.suffix.lower() == ".zip" and is_zipfile(path)
    assert 0 < path.stat().st_size <= 10 * 1024 * 1024
    definition = models.HostedAgentDefinition(json.loads(os.environ["AGENTS_TEST_HOSTED_DEFINITION_JSON"]))
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=credential, allow_preview=True,
            connection_timeout=10, read_timeout=60, retry_total=2,
        ) as client,
    ):
        try:
            with path.open("rb") as code:
                hosted = client.agents.create_version_from_code(agent_name=name, definition=definition, code=code)
            deadline = monotonic() + 300
            while hosted.status != "active":
                assert hosted.status != "failed" and monotonic() < deadline, "Hosted agent did not become active."
                sleep(2)
                hosted = client.agents.get_version(agent_name=name, agent_version=hosted.version)
            session = client.agents.create_session(
                agent_name=name, version_indicator=models.VersionRefIndicator(agent_version=hosted.version)
            )
            deadline = monotonic() + 300
            while session.status != "active":
                assert session.status != "failed" and monotonic() < deadline, "Session did not become active."
                sleep(2)
                session = client.agents.get_session(agent_name=name, session_id=session.agent_session_id)
            result = client.agents.stop_session(agent_name=name, session_id=session.agent_session_id)
            assert result is None
            deadline = monotonic() + 300
            while session.status != "idle" or session.stopped_at is None:
                assert session.status != "failed" and monotonic() < deadline, "Session did not stop."
                sleep(2)
                session = client.agents.get_session(agent_name=name, session_id=session.agent_session_id)
            assert session.stopped_at >= session.created_at
        finally:
            try:
                client.agents.delete(agent_name=name, force=True)
            except ResourceNotFoundError:
                pass
            with pytest.raises(ResourceNotFoundError):
                client.agents.get(agent_name=name)


def test_delete_session():
    """Delete a session and confirm both absence and the documented repeat-delete behavior."""
    name = f"pytest-agents-{uuid4().hex[:16]}"
    path = Path(os.environ["AGENTS_TEST_CODE_ZIP"])
    assert path.suffix.lower() == ".zip" and is_zipfile(path)
    assert 0 < path.stat().st_size <= 10 * 1024 * 1024
    definition = models.HostedAgentDefinition(json.loads(os.environ["AGENTS_TEST_HOSTED_DEFINITION_JSON"]))
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=credential, allow_preview=True,
            connection_timeout=10, read_timeout=60, retry_total=2,
        ) as client,
    ):
        try:
            with path.open("rb") as code:
                hosted = client.agents.create_version_from_code(agent_name=name, definition=definition, code=code)
            deadline = monotonic() + 300
            while hosted.status != "active":
                assert hosted.status != "failed" and monotonic() < deadline, "Hosted agent did not become active."
                sleep(2)
                hosted = client.agents.get_version(agent_name=name, agent_version=hosted.version)
            session = client.agents.create_session(
                agent_name=name, version_indicator=models.VersionRefIndicator(agent_version=hosted.version)
            )
            deadline = monotonic() + 300
            while session.status != "active":
                assert session.status != "failed" and monotonic() < deadline, "Session did not become active."
                sleep(2)
                session = client.agents.get_session(agent_name=name, session_id=session.agent_session_id)
            for attempt in range(2):
                result = client.agents.delete_session(agent_name=name, session_id=session.agent_session_id)
                assert result is None
                with pytest.raises(ResourceNotFoundError):
                    client.agents.get_session(agent_name=name, session_id=session.agent_session_id)
        finally:
            try:
                client.agents.delete(agent_name=name, force=True)
            except ResourceNotFoundError:
                pass
            with pytest.raises(ResourceNotFoundError):
                client.agents.get(agent_name=name)


def test_get_session_log_stream():
    """Read and close one bounded SSE log frame using the SDK's actual byte-stream contract."""
    name = f"pytest-agents-{uuid4().hex[:16]}"
    path = Path(os.environ["AGENTS_TEST_CODE_ZIP"])
    assert path.suffix.lower() == ".zip" and is_zipfile(path)
    assert 0 < path.stat().st_size <= 10 * 1024 * 1024
    definition = models.HostedAgentDefinition(json.loads(os.environ["AGENTS_TEST_HOSTED_DEFINITION_JSON"]))
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=credential, allow_preview=True,
            connection_timeout=10, read_timeout=75, retry_total=0, connection_data_block_size=1,
        ) as client,
    ):
        try:
            with path.open("rb") as code:
                hosted = client.agents.create_version_from_code(agent_name=name, definition=definition, code=code)
            deadline = monotonic() + 300
            while hosted.status != "active":
                assert hosted.status != "failed" and monotonic() < deadline, "Hosted agent did not become active."
                sleep(2)
                hosted = client.agents.get_version(agent_name=name, agent_version=hosted.version)
            session = client.agents.create_session(
                agent_name=name, version_indicator=models.VersionRefIndicator(agent_version=hosted.version)
            )
            deadline = monotonic() + 300
            while session.status != "active":
                assert session.status != "failed" and monotonic() < deadline, "Session did not become active."
                sleep(2)
                session = client.agents.get_session(agent_name=name, session_id=session.agent_session_id)
            response = cast(HttpResponse, client.agents.get_session_log_stream(
                agent_name=name, agent_version=hosted.version, session_id=session.agent_session_id,
                cls=lambda pipeline, data, headers: pipeline.http_response,
            ))
            try:
                assert response.status_code == 200
                assert response.headers["Content-Type"].startswith("text/event-stream")
                deadline = monotonic() + 90
                content = bytearray()
                frame = b""
                for chunk in response.iter_bytes():
                    content.extend(chunk)
                    assert len(content) <= 65536 and monotonic() < deadline, "No bounded log frame received."
                    frame = bytes(content).replace(b"\r\n", b"\n")
                    if b"event: log\n" in frame and b"data:" in frame and b"\n\n" in frame:
                        break
                else:
                    pytest.fail("Stream ended without a log frame.")
                assert any(line.startswith("data:") and line[5:].strip() for line in frame.decode("utf-8").splitlines())
            finally:
                response.close()
        finally:
            try:
                client.agents.delete(agent_name=name, force=True)
            except ResourceNotFoundError:
                pass
            with pytest.raises(ResourceNotFoundError):
                client.agents.get(agent_name=name)


@pytest.mark.parametrize("case", ["minimal", "bytes", "stream"])
def test_upload_session_file(case):
    """Upload bytes and IO streams, checking the stored path, byte count, and content."""
    name = f"pytest-agents-{uuid4().hex[:16]}"
    path = Path(os.environ["AGENTS_TEST_CODE_ZIP"])
    assert path.suffix.lower() == ".zip" and is_zipfile(path)
    assert 0 < path.stat().st_size <= 10 * 1024 * 1024
    definition = models.HostedAgentDefinition(json.loads(os.environ["AGENTS_TEST_HOSTED_DEFINITION_JSON"]))
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=credential, allow_preview=True,
            connection_timeout=10, read_timeout=60, retry_total=2,
        ) as client,
    ):
        try:
            with path.open("rb") as code:
                hosted = client.agents.create_version_from_code(agent_name=name, definition=definition, code=code)
            deadline = monotonic() + 300
            while hosted.status != "active":
                assert hosted.status != "failed" and monotonic() < deadline, "Hosted agent did not become active."
                sleep(2)
                hosted = client.agents.get_version(agent_name=name, agent_version=hosted.version)
            session = client.agents.create_session(
                agent_name=name, version_indicator=models.VersionRefIndicator(agent_version=hosted.version)
            )
            deadline = monotonic() + 300
            while session.status != "active":
                assert session.status != "failed" and monotonic() < deadline, "Session did not become active."
                sleep(2)
                session = client.agents.get_session(agent_name=name, session_id=session.agent_session_id)
            content = b"SDK file regression\n"
            filename = f"pytest-{uuid4().hex}.txt"
            if case == "minimal":
                uploaded = client.agents.upload_session_file(
                    agent_name=name, session_id=session.agent_session_id, content=content, path=filename
                )
            else:
                with BytesIO(content) as stream:
                    uploaded = client.agents.upload_session_file(
                        agent_name=name, session_id=session.agent_session_id,
                        content=content if case == "bytes" else stream, path=filename,
                        content_type="text/plain; charset=utf-8",
                    )
            assert uploaded.path == filename and uploaded.bytes_written == len(content)
            assert b"".join(client.agents.download_session_file(
                agent_name=name, session_id=session.agent_session_id, path=filename
            )) == content
        finally:
            try:
                client.agents.delete(agent_name=name, force=True)
            except ResourceNotFoundError:
                pass
            with pytest.raises(ResourceNotFoundError):
                client.agents.get(agent_name=name)


def test_download_session_file():
    """Download a complete binary file, preserving non-text bytes across the service round trip."""
    name = f"pytest-agents-{uuid4().hex[:16]}"
    path = Path(os.environ["AGENTS_TEST_CODE_ZIP"])
    assert path.suffix.lower() == ".zip" and is_zipfile(path)
    assert 0 < path.stat().st_size <= 10 * 1024 * 1024
    definition = models.HostedAgentDefinition(json.loads(os.environ["AGENTS_TEST_HOSTED_DEFINITION_JSON"]))
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=credential, allow_preview=True,
            connection_timeout=10, read_timeout=60, retry_total=2,
        ) as client,
    ):
        try:
            with path.open("rb") as code:
                hosted = client.agents.create_version_from_code(agent_name=name, definition=definition, code=code)
            deadline = monotonic() + 300
            while hosted.status != "active":
                assert hosted.status != "failed" and monotonic() < deadline, "Hosted agent did not become active."
                sleep(2)
                hosted = client.agents.get_version(agent_name=name, agent_version=hosted.version)
            session = client.agents.create_session(
                agent_name=name, version_indicator=models.VersionRefIndicator(agent_version=hosted.version)
            )
            deadline = monotonic() + 300
            while session.status != "active":
                assert session.status != "failed" and monotonic() < deadline, "Session did not become active."
                sleep(2)
                session = client.agents.get_session(agent_name=name, session_id=session.agent_session_id)
            content = bytes(range(256)) * 64
            filename = f"pytest-{uuid4().hex}.bin"
            client.agents.upload_session_file(
                agent_name=name, session_id=session.agent_session_id, content=content, path=filename
            )
            downloaded = b"".join(client.agents.download_session_file(
                agent_name=name, session_id=session.agent_session_id, path=filename
            ))
            assert downloaded == content
        finally:
            try:
                client.agents.delete(agent_name=name, force=True)
            except ResourceNotFoundError:
                pass
            with pytest.raises(ResourceNotFoundError):
                client.agents.get(agent_name=name)


@pytest.mark.parametrize("case", ["minimal", "asc", "desc", "before"])
def test_list_session_files(case):
    """Check root/directory listing, page limits, ordering, and a service-provided cursor."""
    name = f"pytest-agents-{uuid4().hex[:16]}"
    path = Path(os.environ["AGENTS_TEST_CODE_ZIP"])
    assert path.suffix.lower() == ".zip" and is_zipfile(path)
    assert 0 < path.stat().st_size <= 10 * 1024 * 1024
    definition = models.HostedAgentDefinition(json.loads(os.environ["AGENTS_TEST_HOSTED_DEFINITION_JSON"]))
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=credential, allow_preview=True,
            connection_timeout=10, read_timeout=60, retry_total=2,
        ) as client,
    ):
        try:
            with path.open("rb") as code:
                hosted = client.agents.create_version_from_code(agent_name=name, definition=definition, code=code)
            deadline = monotonic() + 300
            while hosted.status != "active":
                assert hosted.status != "failed" and monotonic() < deadline, "Hosted agent did not become active."
                sleep(2)
                hosted = client.agents.get_version(agent_name=name, agent_version=hosted.version)
            session = client.agents.create_session(
                agent_name=name, version_indicator=models.VersionRefIndicator(agent_version=hosted.version)
            )
            deadline = monotonic() + 300
            while session.status != "active":
                assert session.status != "failed" and monotonic() < deadline, "Session did not become active."
                sleep(2)
                session = client.agents.get_session(agent_name=name, session_id=session.agent_session_id)
            directory = f"pytest-{uuid4().hex}"
            filenames = {"first.txt", "second.txt"}
            for filename in sorted(filenames):
                client.agents.upload_session_file(
                    agent_name=name, session_id=session.agent_session_id,
                    content=filename.encode("utf-8"), path=f"{directory}/{filename}",
                )
            if case == "minimal":
                listed = list(client.agents.list_session_files(agent_name=name, session_id=session.agent_session_id))
                assert any(item.name == directory and item.is_directory for item in listed)
                return
            order = models.PageOrder.DESC if case == "desc" else "asc"
            pages = client.agents.list_session_files(
                agent_name=name, session_id=session.agent_session_id, path=directory, limit=1, order=order
            ).by_page()
            listed = []
            first_cursor = None
            for page_number, page in enumerate(pages, start=1):
                assert page_number <= 10
                items = list(page)
                assert len(items) <= 1
                listed.extend(items)
                if page_number == 1:
                    first_cursor = pages.continuation_token
            assert {item.name for item in listed} == filenames
            assert all(not item.is_directory and item.size == len(item.name.encode("utf-8")) for item in listed)
            timestamps = [item.modified_time for item in listed]
            assert timestamps == sorted(timestamps, reverse=order == "desc")
            if case == "before":
                assert first_cursor, "Expected a cursor after the first of two one-item pages."
                previous = list(client.agents.list_session_files(
                    agent_name=name, session_id=session.agent_session_id,
                    path=directory, limit=1, order="asc", before=first_cursor,
                ))
                assert previous == []
        finally:
            try:
                client.agents.delete(agent_name=name, force=True)
            except ResourceNotFoundError:
                pass
            with pytest.raises(ResourceNotFoundError):
                client.agents.get(agent_name=name)


@pytest.mark.parametrize("case", ["minimal", "recursive", "non-recursive"])
def test_delete_session_file(case):
    """Delete files/directories and ensure non-recursive deletion cannot remove a non-empty directory."""
    name = f"pytest-agents-{uuid4().hex[:16]}"
    path = Path(os.environ["AGENTS_TEST_CODE_ZIP"])
    assert path.suffix.lower() == ".zip" and is_zipfile(path)
    assert 0 < path.stat().st_size <= 10 * 1024 * 1024
    definition = models.HostedAgentDefinition(json.loads(os.environ["AGENTS_TEST_HOSTED_DEFINITION_JSON"]))
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=credential, allow_preview=True,
            connection_timeout=10, read_timeout=60, retry_total=2,
        ) as client,
    ):
        try:
            with path.open("rb") as code:
                hosted = client.agents.create_version_from_code(agent_name=name, definition=definition, code=code)
            deadline = monotonic() + 300
            while hosted.status != "active":
                assert hosted.status != "failed" and monotonic() < deadline, "Hosted agent did not become active."
                sleep(2)
                hosted = client.agents.get_version(agent_name=name, agent_version=hosted.version)
            session = client.agents.create_session(
                agent_name=name, version_indicator=models.VersionRefIndicator(agent_version=hosted.version)
            )
            deadline = monotonic() + 300
            while session.status != "active":
                assert session.status != "failed" and monotonic() < deadline, "Session did not become active."
                sleep(2)
                session = client.agents.get_session(agent_name=name, session_id=session.agent_session_id)
            directory = f"pytest-{uuid4().hex}"
            filename = f"{directory}/nested.txt"
            client.agents.upload_session_file(
                agent_name=name, session_id=session.agent_session_id, content=b"preserve me", path=filename
            )
            if case == "non-recursive":
                with pytest.raises(HttpResponseError) as raised:
                    client.agents.delete_session_file(
                        agent_name=name, session_id=session.agent_session_id, path=directory, recursive=False
                    )
                assert raised.value.status_code == 409
                assert b"".join(client.agents.download_session_file(
                    agent_name=name, session_id=session.agent_session_id, path=filename
                )) == b"preserve me"
                return
            if case == "minimal":
                result = client.agents.delete_session_file(
                    agent_name=name, session_id=session.agent_session_id, path=filename
                )
            else:
                result = client.agents.delete_session_file(
                    agent_name=name, session_id=session.agent_session_id, path=directory, recursive=True
                )
            assert result is None
            with pytest.raises(ResourceNotFoundError):
                b"".join(client.agents.download_session_file(
                    agent_name=name, session_id=session.agent_session_id, path=filename
                ))
        finally:
            try:
                client.agents.delete(agent_name=name, force=True)
            except ResourceNotFoundError:
                pass
            with pytest.raises(ResourceNotFoundError):
                client.agents.get(agent_name=name)


@pytest.mark.parametrize("case", ["minimal", "regular", "digital-worker"])
def test_get_microsoft365_publish_defaults(case):
    """Read regular and digital-worker publish defaults without publishing an application."""
    name = f"pytest-agents-{uuid4().hex[:16]}"
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=credential, allow_preview=True
        ) as client,
    ):
        try:
            client.agents.create_version(
                agent_name=name,
                definition=models.PromptAgentDefinition(model=os.environ["AZURE_DEPLOYMENT_NAME"]),
            )
            if case == "minimal":
                defaults = client.agents.get_microsoft365_publish_defaults(agent_name=name)
            else:
                defaults = client.agents.get_microsoft365_publish_defaults(
                    agent_name=name, publish_as_digital_worker=case == "digital-worker"
                )
            assert defaults.agent_name == name
            assert defaults.agent_display_name == name
            assert not defaults.title_id and not defaults.teams_app_id
        finally:
            try:
                client.agents.delete(agent_name=name, force=True)
            except ResourceNotFoundError:
                pass
            with pytest.raises(ResourceNotFoundError):
                client.agents.get(agent_name=name)


@pytest.mark.parametrize("case", ["minimal", "expanded", "json", "stream", "autopilot-conflict"])
def test_get_microsoft365_package(case):
    """Generate a Teams package through all overloads; inspect its manifest and PNGs without publishing."""
    name = f"pytest-agents-{uuid4().hex[:16]}"
    bot_id = os.environ["AGENTS_TEST_BOT_SERVICE_ARM_ID"]
    options: dict[str, Any] = {
        "publish_scope": "Personal",
        "agent_display_name": "SDK Regression Agent",
        "bot_service_arm_id": bot_id,
        "publish_as_autopilot": False,
        "can_respond_without_mention": True,
        "app_version": "1.2.3",
        "short_description": "SDK regression agent",
        "full_description": "Temporary application package generated by SDK integration tests.",
        "developer_name": "Cosmopilot SDK Tests",
        "developer_website_url": "https://example.com",
        "privacy_url": "https://example.com/privacy",
        "terms_of_use_url": "https://example.com/terms",
    }
    for size, option in ((192, "color_icon_base64"), (32, "outline_icon_base64")):
        rows = []
        for row in range(size):
            pixels = []
            for column in range(size):
                if size == 192:
                    pixels.append(b"\x1f\x87\x73\xff")
                else:
                    pixels.append(b"\xff\xff\xff\xff" if 8 <= row < 24 and 8 <= column < 24 else b"\x00\x00\x00\x00")
            rows.append(b"\x00" + b"".join(pixels))
        png = bytearray(b"\x89PNG\r\n\x1a\n")
        for kind, data in (
            (b"IHDR", pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)),
            (b"IDAT", compress(b"".join(rows))),
            (b"IEND", b""),
        ):
            png.extend(pack(">I", len(data)) + kind + data + pack(">I", crc32(kind + data) & 0xFFFFFFFF))
        options[option] = b64encode(png).decode("ascii")
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=credential, allow_preview=True
        ) as client,
    ):
        try:
            client.agents.create_version(
                agent_name=name,
                definition=models.PromptAgentDefinition(model=os.environ["AZURE_DEPLOYMENT_NAME"]),
            )
            if case == "autopilot-conflict":
                options["publish_as_autopilot"] = True
                options["access_boundaries"] = [models.ActivityProtocolAccessBoundary.READ1_ON1_DEVELOPERS]
                options["optional_permission_scopes"] = [models.Microsoft365PermissionScopes(
                    resource_app_id="00000003-0000-0000-c000-000000000000", scopes=["User.Read"]
                )]
                with pytest.raises(HttpResponseError) as raised:
                    b"".join(client.agents.get_microsoft365_package(
                        agent_name=name, content_type="application/json; charset=utf-8", **options
                    ))
                assert raised.value.status_code == 400
                return
            if case == "minimal":
                content = b"".join(client.agents.get_microsoft365_package(
                    agent_name=name, publish_scope="Personal", bot_service_arm_id=bot_id
                ))
            elif case == "expanded":
                content = b"".join(client.agents.get_microsoft365_package(
                    agent_name=name, content_type="application/json; charset=utf-8", **options
                ))
            else:
                wire_names = {
                    "publish_scope": "publishScope", "agent_display_name": "agentDisplayName",
                    "bot_service_arm_id": "botServiceArmId", "publish_as_autopilot": "publishAsAutopilot",
                    "can_respond_without_mention": "canRespondWithoutMention", "app_version": "appVersion",
                    "short_description": "shortDescription", "full_description": "fullDescription",
                    "developer_name": "developerName", "developer_website_url": "developerWebsiteUrl",
                    "privacy_url": "privacyUrl", "terms_of_use_url": "termsOfUseUrl",
                    "color_icon_base64": "colorIconBase64", "outline_icon_base64": "outlineIconBase64",
                }
                payload = {wire_names[key]: value for key, value in options.items()}
                with BytesIO(json.dumps(payload).encode("utf-8")) as body:
                    content = b"".join(client.agents.get_microsoft365_package(
                        agent_name=name, body=payload if case == "json" else body,
                        content_type="application/json; charset=utf-8",
                    ))
            with ZipFile(BytesIO(content)) as archive:
                manifest = json.loads(archive.read("manifest.json"))
                assert any(bot["botId"] == os.environ["AGENTS_TEST_BOT_APP_ID"] for bot in manifest["bots"])
                if case == "minimal":
                    assert manifest["name"]["short"] == name
                else:
                    assert manifest["name"]["short"] == options["agent_display_name"]
                    assert manifest["version"] == options["app_version"]
                    assert manifest["description"]["short"] == options["short_description"]
                    assert manifest["description"]["full"] == options["full_description"]
                    for field, key in (
                        ("name", "developer_name"), ("websiteUrl", "developer_website_url"),
                        ("privacyUrl", "privacy_url"), ("termsOfUseUrl", "terms_of_use_url"),
                    ):
                        assert manifest["developer"][field] == options[key]
                    assert archive.read(manifest["icons"]["color"]) == b64decode(options["color_icon_base64"])
                    assert archive.read(manifest["icons"]["outline"]) == b64decode(options["outline_icon_base64"])
        finally:
            try:
                client.agents.delete(agent_name=name, force=True)
            except ResourceNotFoundError:
                pass
            with pytest.raises(ResourceNotFoundError):
                client.agents.get(agent_name=name)


@pytest.mark.parametrize("case", ["minimal", "expanded", "json", "stream", "autopilot"])
def test_publish_to_microsoft365(case):
    """Reject a nonexistent agent through every overload; actual tenant publication remains a coverage gap."""
    name = f"pytest-agents-{uuid4().hex[:16]}"
    options: dict[str, Any] = {
        "publish_scope": "Personal",
        "agent_display_name": "SDK Regression Agent",
        "publish_as_autopilot": case == "autopilot",
        "can_respond_without_mention": True,
        "app_version": "1.2.3",
        "short_description": "SDK regression agent",
        "full_description": "Temporary application package generated by SDK integration tests.",
        "developer_name": "Cosmopilot SDK Tests",
        "developer_website_url": "https://example.com",
        "privacy_url": "https://example.com/privacy",
        "terms_of_use_url": "https://example.com/terms",
    }
    if case == "autopilot":
        options["access_boundaries"] = [models.ActivityProtocolAccessBoundary.READ1_ON1_DEVELOPERS]
        options["optional_permission_scopes"] = [models.Microsoft365PermissionScopes(
            resource_app_id="00000003-0000-0000-c000-000000000000", scopes=["User.Read"]
        )]
    else:
        options["bot_service_arm_id"] = os.environ["AGENTS_TEST_BOT_SERVICE_ARM_ID"]
    for size, option in ((192, "color_icon_base64"), (32, "outline_icon_base64")):
        rows = []
        for row in range(size):
            pixels = []
            for column in range(size):
                if size == 192:
                    pixels.append(b"\x1f\x87\x73\xff")
                else:
                    pixels.append(b"\xff\xff\xff\xff" if 8 <= row < 24 and 8 <= column < 24 else b"\x00\x00\x00\x00")
            rows.append(b"\x00" + b"".join(pixels))
        png = bytearray(b"\x89PNG\r\n\x1a\n")
        for kind, data in (
            (b"IHDR", pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)),
            (b"IDAT", compress(b"".join(rows))),
            (b"IEND", b""),
        ):
            png.extend(pack(">I", len(data)) + kind + data + pack(">I", crc32(kind + data) & 0xFFFFFFFF))
        options[option] = b64encode(png).decode("ascii")
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=credential, allow_preview=True
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            client.agents.get(agent_name=name)
        with pytest.raises(ResourceNotFoundError) as raised:
            if case == "minimal":
                client.agents.publish_to_microsoft365(
                    agent_name=name, publish_scope="Personal",
                    bot_service_arm_id=options["bot_service_arm_id"],
                )
            elif case in {"expanded", "autopilot"}:
                client.agents.publish_to_microsoft365(
                    agent_name=name, content_type="application/json; charset=utf-8", **options
                )
            else:
                wire_names = {
                    "publish_scope": "publishScope", "agent_display_name": "agentDisplayName",
                    "bot_service_arm_id": "botServiceArmId", "publish_as_autopilot": "publishAsAutopilot",
                    "can_respond_without_mention": "canRespondWithoutMention", "app_version": "appVersion",
                    "short_description": "shortDescription", "full_description": "fullDescription",
                    "developer_name": "developerName", "developer_website_url": "developerWebsiteUrl",
                    "privacy_url": "privacyUrl", "terms_of_use_url": "termsOfUseUrl",
                    "color_icon_base64": "colorIconBase64", "outline_icon_base64": "outlineIconBase64",
                }
                payload = {wire_names[key]: value for key, value in options.items()}
                with BytesIO(json.dumps(payload).encode("utf-8")) as body:
                    client.agents.publish_to_microsoft365(
                        agent_name=name, body=payload if case == "json" else body,
                        content_type="application/json; charset=utf-8",
                    )
        assert raised.value.status_code == 404
        with pytest.raises(ResourceNotFoundError):
            client.agents.get(agent_name=name)


def test_get():
    """Retrieve an agent by its exact public name and verify its latest version."""
    name = f"pytest-agents-{uuid4().hex[:16]}"
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=credential) as client,
    ):
        try:
            created = client.agents.create_version(
                agent_name=name,
                definition=models.PromptAgentDefinition(model=os.environ["AZURE_DEPLOYMENT_NAME"]),
            )
            retrieved = client.agents.get(agent_name=name)

            assert retrieved.name == name
            assert retrieved.versions.latest.id == created.id
        finally:
            try:
                client.agents.delete(agent_name=name, force=True)
            except ResourceNotFoundError:
                pass
            with pytest.raises(ResourceNotFoundError):
                client.agents.get(agent_name=name)


def test_get_version():
    """Retrieve the exact immutable version and its definition."""
    name = f"pytest-agents-{uuid4().hex[:16]}"
    definition = models.PromptAgentDefinition(
        model=os.environ["AZURE_DEPLOYMENT_NAME"], instructions="Reply with ready."
    )
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=credential) as client,
    ):
        try:
            created = client.agents.create_version(agent_name=name, definition=definition)
            retrieved = client.agents.get_version(agent_name=name, agent_version=created.version)

            assert retrieved.id == created.id
            assert retrieved.name == name
            assert retrieved.version == created.version
            assert retrieved.definition.as_dict() == definition.as_dict()
        finally:
            try:
                client.agents.delete(agent_name=name, force=True)
            except ResourceNotFoundError:
                pass
            with pytest.raises(ResourceNotFoundError):
                client.agents.get(agent_name=name)


def test_disable():
    """Disable an owned agent and verify persisted state and idempotence."""
    name = f"pytest-agents-{uuid4().hex[:16]}"
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=credential, allow_preview=True
        ) as client,
    ):
        try:
            client.agents.create_version(
                agent_name=name,
                definition=models.PromptAgentDefinition(model=os.environ["AZURE_DEPLOYMENT_NAME"]),
            )
            for attempt in range(2):
                result = client.agents.disable(agent_name=name)
                assert result is None
                retrieved = client.agents.get(agent_name=name)
                assert retrieved.state == "disabled"
                assert retrieved.configuration_state == "disabled"
        finally:
            try:
                client.agents.delete(agent_name=name, force=True)
            except ResourceNotFoundError:
                pass
            with pytest.raises(ResourceNotFoundError):
                client.agents.get(agent_name=name)


def test_enable():
    """Re-enable a disabled agent and verify repeated enabling preserves its state."""
    name = f"pytest-agents-{uuid4().hex[:16]}"
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=credential, allow_preview=True
        ) as client,
    ):
        try:
            client.agents.create_version(
                agent_name=name,
                definition=models.PromptAgentDefinition(model=os.environ["AZURE_DEPLOYMENT_NAME"]),
            )
            client.agents.disable(agent_name=name)
            for attempt in range(2):
                result = client.agents.enable(agent_name=name)
                assert result is None
                retrieved = client.agents.get(agent_name=name)
                assert retrieved.state == "enabled"
                assert retrieved.configuration_state == "enabled"
        finally:
            try:
                client.agents.delete(agent_name=name, force=True)
            except ResourceNotFoundError:
                pass
            with pytest.raises(ResourceNotFoundError):
                client.agents.get(agent_name=name)


@pytest.mark.parametrize(
    "case", ["minimal", "expanded", "json", "stream", "draft", "blueprint", "digital-worker", "metadata-boundary"]
)
def test_create_version(case):
    """Exercise all creation overloads and verify optional fields in the persisted version."""
    name = f"pytest-agents-{uuid4().hex[:16]}"
    definition = models.PromptAgentDefinition(
        model=os.environ["AZURE_DEPLOYMENT_NAME"], instructions="Reply with ready."
    )
    metadata = {"suite": "agents", "case": case}
    if case == "metadata-boundary":
        metadata = {f"{index:064d}": "v" * 512 for index in range(16)}
    description = f"SDK regression {case}"
    blueprint = None
    if case in {"blueprint", "digital-worker"}:
        blueprint = models.ManagedAgentIdentityBlueprintReference(
            blueprint_id=os.environ["AGENTS_TEST_BLUEPRINT_ID"]
        )
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=credential, allow_preview=True
        ) as client,
    ):
        try:
            if case == "draft":
                client.agents.create_version(agent_name=name, definition=definition)
            if case == "minimal":
                created = client.agents.create_version(agent_name=name, definition=definition)
            elif case in {"json", "stream"}:
                payload = {"definition": definition.as_dict(), "metadata": metadata, "description": description}
                with BytesIO(json.dumps(payload).encode("utf-8")) as body:
                    created = client.agents.create_version(
                        agent_name=name,
                        body=payload if case == "json" else body,
                        content_type="application/json; charset=utf-8",
                    )
            else:
                options = {"digital_worker_type": "m365"} if case == "digital-worker" else {}
                created = client.agents.create_version(
                    agent_name=name,
                    definition=definition,
                    metadata=metadata,
                    description=description,
                    blueprint_reference=blueprint,
                    draft=case == "draft",
                    content_type="application/json; charset=utf-8",
                    **options,
                )
            retrieved = client.agents.get_version(agent_name=name, agent_version=created.version)
            assert retrieved.name == name
            assert retrieved.id == created.id
            assert retrieved.definition.as_dict() == definition.as_dict()
            if case != "minimal":
                assert retrieved.metadata == metadata
                assert retrieved.description == description
                assert bool(retrieved.draft) == (case == "draft")
            if blueprint is not None:
                assert retrieved.blueprint_reference is not None
                assert retrieved.blueprint_reference.as_dict() == blueprint.as_dict()
            if case == "digital-worker":
                assert client.agents.get(agent_name=name).digital_worker_type == "m365"
            if case == "draft":
                assert all(item.id != created.id for item in client.agents.list_versions(agent_name=name))
        finally:
            try:
                client.agents.delete(agent_name=name, force=True)
            except ResourceNotFoundError:
                pass
            with pytest.raises(ResourceNotFoundError):
                client.agents.get(agent_name=name)


@pytest.mark.parametrize("case", ["minimal", "expanded", "json", "stream"])
def test_create_version_from_manifest(case):
    """Import a manifest through each overload and verify its inputs are materialized."""
    name = f"pytest-agents-{uuid4().hex[:16]}"
    manifest_id = os.environ["AGENTS_TEST_MANIFEST_ID"]
    parameters = json.loads(os.environ["AGENTS_TEST_MANIFEST_PARAMETERS_JSON"])
    expected = json.loads(os.environ["AGENTS_TEST_MANIFEST_DEFINITION_JSON"])
    assert isinstance(parameters, dict) and parameters
    assert isinstance(expected, dict) and expected
    metadata = {"suite": "agents", "case": case}
    description = "Imported by SDK integration tests."
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=credential, allow_preview=True
        ) as client,
    ):
        try:
            if case == "minimal":
                created = client.agents.create_version_from_manifest(
                    agent_name=name, manifest_id=manifest_id, parameter_values=parameters
                )
            elif case == "expanded":
                created = client.agents.create_version_from_manifest(
                    agent_name=name,
                    manifest_id=manifest_id,
                    parameter_values=parameters,
                    metadata=metadata,
                    description=description,
                    content_type="application/json; charset=utf-8",
                )
            else:
                payload = {
                    "manifest_id": manifest_id,
                    "parameter_values": parameters,
                    "metadata": metadata,
                    "description": description,
                }
                with BytesIO(json.dumps(payload).encode("utf-8")) as body:
                    created = client.agents.create_version_from_manifest(
                        agent_name=name,
                        body=payload if case == "json" else body,
                        content_type="application/json; charset=utf-8",
                    )
            retrieved = client.agents.get_version(agent_name=name, agent_version=created.version)
            assert retrieved.id == created.id
            assert retrieved.name == name
            for field, value in expected.items():
                assert retrieved.definition.as_dict()[field] == value
            if case != "minimal":
                assert retrieved.metadata == metadata
                assert retrieved.description == description
        finally:
            try:
                client.agents.delete(agent_name=name, force=True)
            except ResourceNotFoundError:
                pass
            with pytest.raises(ResourceNotFoundError):
                client.agents.get(agent_name=name)


@pytest.mark.parametrize("case", ["minimal", "asc", "desc", "before", "maximum-limit"])
def test_list(case):
    """Check kind filtering, page-size boundaries, ordering, and the before cursor."""
    names = [f"pytest-agents-{uuid4().hex[:16]}" for index in range(2)]
    definition = models.PromptAgentDefinition(model=os.environ["AZURE_DEPLOYMENT_NAME"])
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=credential) as client,
    ):
        try:
            for name in names:
                client.agents.create_version(agent_name=name, definition=definition)
            order = models.PageOrder.DESC if case == "desc" else "asc"
            limit = 100 if case == "maximum-limit" else 1
            if case == "minimal":
                pager = client.agents.list()
            else:
                pager = client.agents.list(kind=models.AgentKind.PROMPT, limit=limit, order=order)
            listed = []
            for page_number, page in enumerate(pager.by_page(), start=1):
                assert page_number <= 100, "Use a disposable test project with fewer agents."
                items = list(page)
                if case != "minimal":
                    assert len(items) <= limit
                listed.extend(items)
            assert set(names) <= {item.name for item in listed}
            if case != "minimal":
                assert all(item.versions.latest.definition.kind == "prompt" for item in listed)
                own_times = [item.versions.latest.created_at for item in listed if item.name in names]
                assert own_times == sorted(own_times, reverse=order == "desc")
            if case == "before":
                previous = list(client.agents.list(kind="prompt", limit=100, order="asc", before=listed[-1].id))
                assert [item.id for item in previous] == [item.id for item in listed[:-1]]
        finally:
            for name in reversed(names):
                try:
                    client.agents.delete(agent_name=name, force=True)
                except ResourceNotFoundError:
                    pass
                with pytest.raises(ResourceNotFoundError):
                    client.agents.get(agent_name=name)


@pytest.mark.parametrize("case", ["minimal", "asc", "desc", "before", "include-drafts"])
def test_list_versions(case):
    """Check paginated version order, draft visibility, and release-only latest resolution."""
    name = f"pytest-agents-{uuid4().hex[:16]}"
    definition = models.PromptAgentDefinition(model=os.environ["AZURE_DEPLOYMENT_NAME"])
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=credential, allow_preview=True
        ) as client,
    ):
        try:
            first = client.agents.create_version(agent_name=name, definition=definition)
            second = client.agents.create_version(agent_name=name, definition=definition)
            draft = client.agents.create_version(agent_name=name, definition=definition, draft=True)
            order = models.PageOrder.DESC if case == "desc" else "asc"
            if case == "minimal":
                pager = client.agents.list_versions(agent_name=name)
            else:
                pager = client.agents.list_versions(
                    agent_name=name, limit=1, order=order, include_drafts=case == "include-drafts"
                )
            listed = []
            for page_number, page in enumerate(pager.by_page(), start=1):
                assert page_number <= 10
                items = list(page)
                if case != "minimal":
                    assert len(items) <= 1
                listed.extend(items)
            expected = {first.id, second.id, draft.id} if case == "include-drafts" else {first.id, second.id}
            assert {item.id for item in listed} == expected
            if case != "minimal":
                timestamps = [item.created_at for item in listed]
                assert timestamps == sorted(timestamps, reverse=order == "desc")
            if case == "before":
                previous = list(client.agents.list_versions(
                    agent_name=name, limit=1, order="asc", before=listed[-1].id, include_drafts=False
                ))
                assert [item.id for item in previous] == [item.id for item in listed[:-1]]
            assert client.agents.get(agent_name=name).versions.latest.id == second.id
        finally:
            try:
                client.agents.delete(agent_name=name, force=True)
            except ResourceNotFoundError:
                pass
            with pytest.raises(ResourceNotFoundError):
                client.agents.get(agent_name=name)


@pytest.mark.parametrize("case", ["minimal", "expanded", "json", "stream"])
def test_update_details(case):
    """Merge-patch endpoint routing and the agent card using every public body overload."""
    name = f"pytest-agents-{uuid4().hex[:16]}"
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=credential, allow_preview=True
        ) as client,
    ):
        try:
            created = client.agents.create_version(
                agent_name=name,
                definition=models.PromptAgentDefinition(model=os.environ["AZURE_DEPLOYMENT_NAME"]),
            )
            selector = models.VersionSelector(version_selection_rules=[
                models.FixedRatioVersionSelectionRule(agent_version=created.version, traffic_percentage=100)
            ])
            endpoint = models.AgentEndpointConfig(version_selector=selector)
            card = models.AgentCard(
                version="1.2.3", description="SDK test card",
                skills=[models.AgentCardSkill(id="ready", name="Readiness", tags=["regression"])],
            )
            if case == "minimal":
                updated = client.agents.update_details(agent_name=name)
            elif case == "expanded":
                updated = client.agents.update_details(
                    agent_name=name, agent_endpoint=endpoint, agent_card=card,
                    content_type="application/merge-patch+json; charset=utf-8",
                )
            else:
                payload = {"agent_endpoint": endpoint.as_dict(), "agent_card": card.as_dict()}
                with BytesIO(json.dumps(payload).encode("utf-8")) as body:
                    updated = client.agents.update_details(
                        agent_name=name, body=payload if case == "json" else body,
                        content_type="application/merge-patch+json; charset=utf-8",
                    )
            retrieved = client.agents.get(agent_name=name)
            assert updated.name == retrieved.name == name
            assert retrieved.versions.latest.id == created.id
            if case != "minimal":
                assert retrieved.agent_card is not None
                assert retrieved.agent_card.as_dict() == card.as_dict()
                assert retrieved.agent_endpoint is not None
                assert retrieved.agent_endpoint.version_selector is not None
                assert retrieved.agent_endpoint.version_selector.as_dict() == selector.as_dict()
        finally:
            try:
                client.agents.delete(agent_name=name, force=True)
            except ResourceNotFoundError:
                pass
            with pytest.raises(ResourceNotFoundError):
                client.agents.get(agent_name=name)