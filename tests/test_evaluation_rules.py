import os
from uuid import uuid4

import pytest
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    ContinuousEvaluationRuleAction,
    EvaluationRule,
    EvaluationRuleEventType,
)
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
        rule_id = f"pytest-rule-{uuid4().hex[:8]}"
        openai_client = client.get_openai_client()
        evaluation = openai_client.evals.create(
            name=f"pytest-eval-{uuid4().hex[:8]}",
            data_source_config={
                "type": "custom",
                "item_schema": {
                    "type": "object",
                    "properties": {"actual": {"type": "string"}},
                    "required": ["actual"],
                },
                "include_sample_schema": False,
            },
            testing_criteria=[
                {
                    "type": "string_check",
                    "name": "exact-match",
                    "input": "{{item.actual}}",
                    "reference": "test",
                    "operation": "eq",
                }
            ],
        )

        try:
            created_rule = client.evaluation_rules.create_or_update(
                id=rule_id,
                evaluation_rule=EvaluationRule(
                    display_name="Temporary evaluation rule created by pytest.",
                    enabled=False,
                    event_type=EvaluationRuleEventType.RESPONSE_COMPLETED,
                    action=ContinuousEvaluationRuleAction(eval_id=evaluation.id),
                ),
            )

            assert created_rule is not None
        finally:
            client.evaluation_rules.delete(id=rule_id)
            openai_client.evals.delete(eval_id=evaluation.id)


@pytest.mark.integration
def test_delete():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        rule_id = f"pytest-rule-{uuid4().hex[:8]}"
        openai_client = client.get_openai_client()
        evaluation = openai_client.evals.create(
            name=f"pytest-eval-{uuid4().hex[:8]}",
            data_source_config={
                "type": "custom",
                "item_schema": {
                    "type": "object",
                    "properties": {"actual": {"type": "string"}},
                    "required": ["actual"],
                },
                "include_sample_schema": False,
            },
            testing_criteria=[
                {
                    "type": "string_check",
                    "name": "exact-match",
                    "input": "{{item.actual}}",
                    "reference": "test",
                    "operation": "eq",
                }
            ],
        )
        client.evaluation_rules.create_or_update(
            id=rule_id,
            evaluation_rule=EvaluationRule(
                display_name="Temporary evaluation rule created by pytest.",
                enabled=False,
                event_type=EvaluationRuleEventType.RESPONSE_COMPLETED,
                action=ContinuousEvaluationRuleAction(eval_id=evaluation.id),
            ),
        )

        try:
            deleted_rule = client.evaluation_rules.delete(id=rule_id)

            assert deleted_rule is None
        finally:
            openai_client.evals.delete(eval_id=evaluation.id)


@pytest.mark.integration
def test_get():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        rule_id = f"pytest-rule-{uuid4().hex[:8]}"
        openai_client = client.get_openai_client()
        evaluation = openai_client.evals.create(
            name=f"pytest-eval-{uuid4().hex[:8]}",
            data_source_config={
                "type": "custom",
                "item_schema": {
                    "type": "object",
                    "properties": {"actual": {"type": "string"}},
                    "required": ["actual"],
                },
                "include_sample_schema": False,
            },
            testing_criteria=[
                {
                    "type": "string_check",
                    "name": "exact-match",
                    "input": "{{item.actual}}",
                    "reference": "test",
                    "operation": "eq",
                }
            ],
        )
        client.evaluation_rules.create_or_update(
            id=rule_id,
            evaluation_rule=EvaluationRule(
                display_name="Temporary evaluation rule created by pytest.",
                enabled=False,
                event_type=EvaluationRuleEventType.RESPONSE_COMPLETED,
                action=ContinuousEvaluationRuleAction(eval_id=evaluation.id),
            ),
        )

        try:
            retrieved_rule = client.evaluation_rules.get(id=rule_id)

            assert retrieved_rule is not None
        finally:
            client.evaluation_rules.delete(id=rule_id)
            openai_client.evals.delete(eval_id=evaluation.id)


@pytest.mark.integration
def test_list():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        listed_rules = list(client.evaluation_rules.list())

        assert isinstance(listed_rules, list)
