import os
from uuid import uuid4

import pytest
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    AzureOpenAIModelConfiguration,
    RedTeam,
    RiskCategory,
)
from azure.identity import DefaultAzureCredential


@pytest.mark.integration
def test_create():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        created_red_team = client.beta.red_teams.create(
            red_team=RedTeam(
                display_name=f"pytest-red-team-{uuid4().hex[:8]}",
                num_turns=1,
                simulation_only=True,
                risk_categories=[RiskCategory.VIOLENCE],
                target=AzureOpenAIModelConfiguration(
                    model_deployment_name=os.environ["AZURE_DEPLOYMENT_NAME"],
                ),
            ),
        )

        assert created_red_team is not None


@pytest.mark.integration
def test_get():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        created_red_team = client.beta.red_teams.create(
            red_team=RedTeam(
                display_name=f"pytest-red-team-{uuid4().hex[:8]}",
                num_turns=1,
                simulation_only=True,
                risk_categories=[RiskCategory.VIOLENCE],
                target=AzureOpenAIModelConfiguration(
                    model_deployment_name=os.environ["AZURE_DEPLOYMENT_NAME"],
                ),
            ),
        )

        retrieved_red_team = client.beta.red_teams.get(name=created_red_team.name)

        assert retrieved_red_team is not None


@pytest.mark.integration
def test_list():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        listed_red_teams = list(client.beta.red_teams.list())

        assert isinstance(listed_red_teams, list)
