import os

import pytest
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import ConnectionType
from azure.identity import DefaultAzureCredential


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


@pytest.mark.integration
def test_get_default():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        connection = client.connections.get_default(
            connection_type=ConnectionType.AZURE_AI_SEARCH,
        )

        assert connection is not None


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
