import os

import pytest
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential


@pytest.mark.integration
def test_get_openai_client():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        openai_client = client.get_openai_client()

        assert openai_client is not None
