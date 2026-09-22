import os
from uuid import uuid4

import pytest
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import WebSearchToolboxTool
from azure.identity import DefaultAzureCredential


@pytest.mark.integration
def test_create_version():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        toolbox_name = f"pytest-toolbox-{uuid4().hex[:8]}"

        try:
            created_toolbox_version = client.toolboxes.create_version(
                name=toolbox_name,
                tools=[WebSearchToolboxTool()],
                description="Temporary toolbox created by pytest.",
            )

            assert created_toolbox_version is not None
        finally:
            client.toolboxes.delete(name=toolbox_name)


@pytest.mark.integration
def test_delete():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        toolbox_name = f"pytest-toolbox-{uuid4().hex[:8]}"
        client.toolboxes.create_version(
            name=toolbox_name,
            tools=[WebSearchToolboxTool()],
            description="Temporary toolbox created by pytest.",
        )

        deleted_toolbox = client.toolboxes.delete(name=toolbox_name)

        assert deleted_toolbox is None


@pytest.mark.integration
def test_delete_version():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        toolbox_name = f"pytest-toolbox-{uuid4().hex[:8]}"
        client.toolboxes.create_version(
            name=toolbox_name,
            tools=[WebSearchToolboxTool()],
            description="Temporary toolbox created by pytest.",
        )
        second_toolbox_version = client.toolboxes.create_version(
            name=toolbox_name,
            tools=[WebSearchToolboxTool()],
            description="Temporary toolbox updated by pytest.",
        )

        try:
            deleted_toolbox_version = client.toolboxes.delete_version(
                name=toolbox_name,
                version=second_toolbox_version.version,
            )

            assert deleted_toolbox_version is None
        finally:
            client.toolboxes.delete(name=toolbox_name)


@pytest.mark.integration
def test_get():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        toolbox_name = f"pytest-toolbox-{uuid4().hex[:8]}"
        client.toolboxes.create_version(
            name=toolbox_name,
            tools=[WebSearchToolboxTool()],
            description="Temporary toolbox created by pytest.",
        )

        try:
            retrieved_toolbox = client.toolboxes.get(name=toolbox_name)

            assert retrieved_toolbox is not None
        finally:
            client.toolboxes.delete(name=toolbox_name)


@pytest.mark.integration
def test_get_version():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        toolbox_name = f"pytest-toolbox-{uuid4().hex[:8]}"
        created_toolbox_version = client.toolboxes.create_version(
            name=toolbox_name,
            tools=[WebSearchToolboxTool()],
            description="Temporary toolbox created by pytest.",
        )

        try:
            retrieved_toolbox_version = client.toolboxes.get_version(
                name=toolbox_name,
                version=created_toolbox_version.version,
            )

            assert retrieved_toolbox_version is not None
        finally:
            client.toolboxes.delete(name=toolbox_name)


@pytest.mark.integration
def test_invoke_latest_toolbox_mcp():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        toolbox_name = f"pytest-toolbox-{uuid4().hex[:8]}"
        client.toolboxes.create_version(
            name=toolbox_name,
            tools=[WebSearchToolboxTool()],
            description="Temporary toolbox created by pytest.",
        )

        try:
            invocation_result = client.toolboxes.invoke_latest_toolbox_mcp(
                name=toolbox_name,
                request={"jsonrpc": "2.0", "id": "1", "method": "tools/list"},
            )

            assert invocation_result is not None
        finally:
            client.toolboxes.delete(name=toolbox_name)


@pytest.mark.integration
def test_list():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        listed_toolboxes = list(client.toolboxes.list())

        assert isinstance(listed_toolboxes, list)


@pytest.mark.integration
def test_list_versions():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        toolbox_name = f"pytest-toolbox-{uuid4().hex[:8]}"
        client.toolboxes.create_version(
            name=toolbox_name,
            tools=[WebSearchToolboxTool()],
            description="Temporary toolbox created by pytest.",
        )

        try:
            toolbox_versions = list(client.toolboxes.list_versions(name=toolbox_name))

            assert isinstance(toolbox_versions, list)
        finally:
            client.toolboxes.delete(name=toolbox_name)


@pytest.mark.integration
def test_update():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        toolbox_name = f"pytest-toolbox-{uuid4().hex[:8]}"
        created_toolbox_version = client.toolboxes.create_version(
            name=toolbox_name,
            tools=[WebSearchToolboxTool()],
            description="Temporary toolbox created by pytest.",
        )

        try:
            updated_toolbox = client.toolboxes.update(
                name=toolbox_name,
                default_version=created_toolbox_version.version,
            )

            assert updated_toolbox is not None
        finally:
            client.toolboxes.delete(name=toolbox_name)
