import os

import pytest
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential


@pytest.mark.integration
def test_get_application_insights_connection_string():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        connection_string = (
            client.telemetry.get_application_insights_connection_string()
        )

        assert connection_string is not None
