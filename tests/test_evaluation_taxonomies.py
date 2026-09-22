import os
from uuid import uuid4

import pytest
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    AgentTaxonomyInput,
    AzureAIAgentTarget,
    EvaluationTaxonomy,
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
        taxonomy_name = f"pytest-taxonomy-{uuid4().hex[:8]}"

        try:
            created_taxonomy = client.beta.evaluation_taxonomies.create(
                name=taxonomy_name,
                taxonomy=EvaluationTaxonomy(
                    description="Temporary taxonomy created by pytest.",
                    taxonomy_input=AgentTaxonomyInput(
                        target=AzureAIAgentTarget(name="weather-agent"),
                        risk_categories=[RiskCategory.VIOLENCE],
                    ),
                ),
            )

            assert created_taxonomy is not None
        finally:
            client.beta.evaluation_taxonomies.delete(name=taxonomy_name)


@pytest.mark.integration
def test_delete():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        taxonomy_name = f"pytest-taxonomy-{uuid4().hex[:8]}"
        client.beta.evaluation_taxonomies.create(
            name=taxonomy_name,
            taxonomy=EvaluationTaxonomy(
                description="Temporary taxonomy created by pytest.",
                taxonomy_input=AgentTaxonomyInput(
                    target=AzureAIAgentTarget(name="weather-agent"),
                    risk_categories=[RiskCategory.VIOLENCE],
                ),
            ),
        )

        deleted_taxonomy = client.beta.evaluation_taxonomies.delete(name=taxonomy_name)

        assert deleted_taxonomy is None


@pytest.mark.integration
def test_get():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        taxonomy_name = f"pytest-taxonomy-{uuid4().hex[:8]}"
        client.beta.evaluation_taxonomies.create(
            name=taxonomy_name,
            taxonomy=EvaluationTaxonomy(
                description="Temporary taxonomy created by pytest.",
                taxonomy_input=AgentTaxonomyInput(
                    target=AzureAIAgentTarget(name="weather-agent"),
                    risk_categories=[RiskCategory.VIOLENCE],
                ),
            ),
        )

        try:
            retrieved_taxonomy = client.beta.evaluation_taxonomies.get(
                name=taxonomy_name,
            )

            assert retrieved_taxonomy is not None
        finally:
            client.beta.evaluation_taxonomies.delete(name=taxonomy_name)


@pytest.mark.integration
def test_list():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        listed_taxonomies = list(client.beta.evaluation_taxonomies.list())

        assert isinstance(listed_taxonomies, list)


@pytest.mark.integration
def test_update():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        taxonomy_name = f"pytest-taxonomy-{uuid4().hex[:8]}"
        client.beta.evaluation_taxonomies.create(
            name=taxonomy_name,
            taxonomy=EvaluationTaxonomy(
                description="Temporary taxonomy created by pytest.",
                taxonomy_input=AgentTaxonomyInput(
                    target=AzureAIAgentTarget(name="weather-agent"),
                    risk_categories=[RiskCategory.VIOLENCE],
                ),
            ),
        )

        try:
            updated_taxonomy = client.beta.evaluation_taxonomies.update(
                name=taxonomy_name,
                taxonomy=EvaluationTaxonomy(
                    description="Temporary taxonomy updated by pytest.",
                    taxonomy_input=AgentTaxonomyInput(
                        target=AzureAIAgentTarget(name="weather-agent"),
                        risk_categories=[RiskCategory.VIOLENCE],
                    ),
                ),
            )

            assert updated_taxonomy is not None
        finally:
            client.beta.evaluation_taxonomies.delete(name=taxonomy_name)
