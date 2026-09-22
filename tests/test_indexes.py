import os
from uuid import uuid4

import pytest
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import AzureAISearchIndex
from azure.identity import DefaultAzureCredential


@pytest.mark.integration
def test_create_or_update():
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


@pytest.mark.integration
def test_get():
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

        try:
            retrieved_index = client.indexes.get(name=index_name, version="1")

            assert retrieved_index is not None
        finally:
            client.indexes.delete(name=index_name, version="1")


@pytest.mark.integration
def test_list():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        listed_indexes = list(client.indexes.list())

        assert isinstance(listed_indexes, list)


@pytest.mark.integration
def test_list_versions():
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

        try:
            versions = list(client.indexes.list_versions(name=index_name))

            assert isinstance(versions, list)
        finally:
            client.indexes.delete(name=index_name, version="1")
