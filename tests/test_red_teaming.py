import os
from uuid import uuid4

import pytest
from azure.ai.projects.models import (
    AttackStrategy,
    AzureOpenAIModelConfiguration,
    RedTeam,
    RiskCategory,
)

import red_teaming


@pytest.mark.integration
def test_create_red_team():
    created_red_team = red_teaming.create(
        red_team=RedTeam(
            display_name=f"pytest-red-team-{uuid4().hex[:8]}",
            target=AzureOpenAIModelConfiguration(
                model_deployment_name=os.environ["AZURE_DEPLOYMENT_NAME"],
            ),
            num_turns=1,
            attack_strategies=[AttackStrategy.EASY],
            risk_categories=[RiskCategory.VIOLENCE],
            simulation_only=True,
        )
    )

    assert created_red_team is not None


@pytest.mark.integration
def test_get_red_team():
    created_red_team = red_teaming.create(
        red_team=RedTeam(
            display_name=f"pytest-red-team-{uuid4().hex[:8]}",
            target=AzureOpenAIModelConfiguration(
                model_deployment_name=os.environ["AZURE_DEPLOYMENT_NAME"],
            ),
            num_turns=1,
            attack_strategies=[AttackStrategy.EASY],
            risk_categories=[RiskCategory.VIOLENCE],
            simulation_only=True,
        )
    )

    retrieved_red_team = red_teaming.get(name=created_red_team.name)

    assert retrieved_red_team.name == created_red_team.name


@pytest.mark.integration
def test_list_red_teams():
    listed_red_teams = red_teaming.list_red_teams()

    assert isinstance(listed_red_teams, list)