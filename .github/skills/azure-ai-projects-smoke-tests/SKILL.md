---
name: azure-ai-projects-smoke-tests
description: "Use when adding or editing any file under tests/. Defines the smoke-test template for azure-ai-projects client namespaces: a fixed table of test files, one integration test per public method, client reinstantiated per test."
---

# azure-ai-projects smoke tests

Everything under `tests/` is a smoke test for the `azure-ai-projects` SDK. A smoke
test proves one public method is reachable and returns something; it is not a
behavioral or contract test.

## Structure of `tests/`

This table is the whole layout. A file covers every public method of every
namespace listed beside it, and there are no other files:

| File | Namespaces covered |
| --- | --- |
| `tests/test_agent_insight_monitors.py` | `client.beta.agent_insight_monitors` |
| `tests/test_agents.py` | `client.agents`, `client.beta.agents` |
| `tests/test_client.py` | `AIProjectClient` itself |
| `tests/test_connections.py` | `client.connections` |
| `tests/test_datasets.py` | `client.datasets`, `client.beta.datasets` |
| `tests/test_deployments.py` | `client.deployments` |
| `tests/test_evaluation_rules.py` | `client.evaluation_rules` |
| `tests/test_evaluation_taxonomies.py` | `client.beta.evaluation_taxonomies` |
| `tests/test_evaluators.py` | `client.beta.evaluators` |
| `tests/test_indexes.py` | `client.indexes` |
| `tests/test_insights.py` | `client.beta.insights` |
| `tests/test_memory_stores.py` | `client.beta.memory_stores` |
| `tests/test_models.py` | `client.beta.models` |
| `tests/test_red_teams.py` | `client.beta.red_teams` |
| `tests/test_routines.py` | `client.beta.routines` |
| `tests/test_schedules.py` | `client.beta.schedules` |
| `tests/test_skills.py` | `client.beta.skills` |
| `tests/test_telemetry.py` | `client.telemetry` |
| `tests/test_toolboxes.py` | `client.toolboxes` |
| `tests/test_voice_agents.py` | `client.beta.voice_agents` and every sub-namespace of it — `conversations`, `realtime`, `telephony` |

A namespace that exposes no public methods of its own, such as
`client.beta.voice_agents`, contributes nothing; its children supply the methods.

`client.beta.<name>` shares a file with `client.<name>` where both exist, so a
file's test functions come from more than one namespace. Test names stay
unqualified — `test_<public method name>` — because no two namespaces sharing a
file expose the same method name. If a future SDK release introduces such a
clash, raise it rather than inventing a qualified name.

Public methods on `AIProjectClient` itself, such as `get_openai_client`, belong
in `tests/test_client.py`. `close` and `send_request` are transport plumbing, not
part of the surface under test — skip them wherever they appear.

A new namespace in a future SDK release needs a row here before it gets a file.

## Coverage

Write one test function for every public method on `client.<module name>`. The
installed package is the inventory — introspect it rather than trusting a
document that may describe a different release:

```bash
python -c "import azure.ai.projects.operations as o; print([m for m in dir(o.ConnectionsOperations) if not m.startswith('_')])"
```

[`docs/azure-ai-projects.md`](../../../docs/azure-ai-projects.md) tabulates the
same surface and is quicker to read, but it is a document, not the package.
Where the two disagree, the package wins. A namespace is fully covered when
every public method has a matching test function.


## Required shape

```python
@pytest.mark.integration
def test_<public method name>():
```

The decorator is always `@pytest.mark.integration`; these tests call live Azure
services. The function name is `test_` plus the SDK method name verbatim:
`client.connections.get_default` becomes `test_get_default`.

The test signature takes no parameters. Fixtures, including `request`, are not
available.

## Rules

1. The file contains imports and decorated test functions only. No module-level
   constants, no helper functions, no fixtures, no classes, no `conftest.py`
   additions, no `parametrize`.
2. Reinstantiate `DefaultAzureCredential` and `AIProjectClient` inside every test
   function. Never share a client across tests.
3. Each test is self-contained. It creates the resources it needs, exercises one
   method, and deletes what it created. No test may depend on another test's
   state, order, or leftovers.
4. Read the endpoint from `os.environ["AZURE_AI_PROJECT_ENDPOINT"]`. Never
   hard-code endpoints or credentials.
5. Do the work inside the `with` block. `ItemPaged` results are lazy, so
   materialize them with `list(...)`; `begin_*` methods return a poller, so call
   `.result()`; `Iterator[bytes]` results must be consumed there too.
6. Pass `allow_preview=True` to `AIProjectClient` for preview features reached
   through a stable namespace. Calls through `client.beta.*` already opt in and
   do not need it.
7. Give created resources a unique name, `f"pytest-<kind>-{uuid4().hex[:8]}"`, so
   parallel or repeated runs never collide.
8. Clean up in a `finally` block when the test creates a resource, so a failed
   assertion still deletes it. A test whose subject *is* the delete method needs
   no `finally`.
9. Assert that the call succeeded and nothing more: `is not None`,
   `isinstance(..., list)`, or `is None` for deletes. Do not assert on service
   data that the project owner can change.
10. Never skip a failing service call or weaken cleanup to make a test pass.
11. When a method has no reachable happy path, probe it instead: call it with a
    `pytest-`-prefixed identifier that cannot exist and assert the service
    answers `ResourceNotFoundError`. See "Methods with no reachable happy path".

## Methods with no reachable happy path

Some methods cannot be exercised for real from a test: they need a running
hosted agent session, an uploaded model weight file, a provisioned phone number,
or a long-running billable job. Do not skip them and do not delete them from the
file.

Call the method with an identifier that cannot exist and assert the service
rejects it:

```python
@pytest.mark.integration
def test_stop_session():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            client.agents.stop_session(
                agent_name="weather-agent",
                session_id=f"pytest-session-{uuid4().hex[:8]}",
            )
```

This is still a smoke test: it proves the method exists, accepts those
arguments, produces a well-formed request, reaches the service, and that the SDK
maps the response onto the documented exception. It is the last resort, not the
default — use the real call wherever a resource can be created cheaply.

`ResourceNotFoundError` is the expected answer for an unknown identifier. Do not
broaden it to `HttpResponseError` to absorb whatever the service returns; a
`400` or `403` where a `404` was expected is a real finding, and the test should
fail and surface it.

## Template

```python
import os
from uuid import uuid4

import pytest
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential


@pytest.mark.integration
def test_list():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        listed_connections = list(client.connections.list())

        assert isinstance(listed_connections, list)


@pytest.mark.integration
def test_get():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        connection = client.connections.get(name="aisearch")

        assert connection is not None
```

Create-and-clean-up variant, for a namespace whose methods mutate the project:

```python
@pytest.mark.integration
def test_create():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        index_name = f"pytest-index-{uuid4().hex[:8]}"

        try:
            created_index = client.indexes.create_or_update(
                name=index_name,
                version="1",
                index=AzureAISearchIndex(
                    connection_name="aisearch",
                    index_name=index_name,
                ),
            )

            assert created_index is not None
        finally:
            client.indexes.delete(name=index_name, version="1")
```

A test for a method that needs an existing resource creates that resource itself,
in the same `with` block, before calling the method under test:

```python
@pytest.mark.integration
def test_delete():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        index_name = f"pytest-index-{uuid4().hex[:8]}"
        client.indexes.create_or_update(
            name=index_name,
            version="1",
            index=AzureAISearchIndex(
                connection_name="aisearch",
                index_name=index_name,
            ),
        )

        deleted_index = client.indexes.delete(name=index_name, version="1")

        assert deleted_index is None
```

## Project prerequisites

Tests may assume the Foundry project already contains the fixtures the weekly
workflow guarantees: the `aisearch` connection, the `weather-agent`, and the
deployment named by `AZURE_DEPLOYMENT_NAME`. Read any other required value from
the environment rather than hard-coding it.

## Running

```bash
PYTHONPATH=src python -m pytest tests/test_<module name>.py
```

Live runs need the azd environment injected:

```bash
azd exec -- env PYTHONPATH=src python -m pytest -m integration tests/test_<module name>.py
```

## Before finishing

- Every public method on every namespace the file covers has one test function.
- The file is one of the rows in the structure table, and no other file exists.
- Every test function name matches its SDK method name.
- Every test constructs its own credential and client.
- The file's top level holds only imports and test functions.
- Every created resource is deleted by the test that created it.
- Every probe test expects `ResourceNotFoundError`, not a broader exception.
