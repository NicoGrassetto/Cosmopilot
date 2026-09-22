import os

import pytest
from azure.ai.projects import AIProjectClient
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
        deployment = client.deployments.get(
            name=os.environ["AZURE_DEPLOYMENT_NAME"],
        )

        assert deployment is not None


@pytest.mark.integration
def test_list():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        listed_deployments = list(client.deployments.list())

        assert isinstance(listed_deployments, list)
