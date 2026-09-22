import os
from uuid import uuid4

import pytest
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    DailyRecurrenceSchedule,
    EvaluationScheduleTask,
    RecurrenceTrigger,
    Schedule,
)
from azure.core.exceptions import ResourceNotFoundError
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
        schedule_id = f"pytest-schedule-{uuid4().hex[:8]}"
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
            created_schedule = client.beta.schedules.create_or_update(
                schedule_id=schedule_id,
                schedule=Schedule(
                    display_name="Temporary schedule created by pytest.",
                    enabled=False,
                    trigger=RecurrenceTrigger(
                        interval=1,
                        time_zone="UTC",
                        schedule=DailyRecurrenceSchedule(hours=[0]),
                    ),
                    task=EvaluationScheduleTask(
                        eval_id=evaluation.id,
                        eval_run={
                            "name": "pytest-eval-run",
                            "data_source": {
                                "type": "jsonl",
                                "source": {
                                    "type": "file_content",
                                    "content": [{"item": {"actual": "test"}}],
                                },
                            },
                        },
                    ),
                ),
            )

            assert created_schedule is not None
        finally:
            client.beta.schedules.delete(schedule_id=schedule_id)
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
        schedule_id = f"pytest-schedule-{uuid4().hex[:8]}"
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
        client.beta.schedules.create_or_update(
            schedule_id=schedule_id,
            schedule=Schedule(
                display_name="Temporary schedule created by pytest.",
                enabled=False,
                trigger=RecurrenceTrigger(
                    interval=1,
                    time_zone="UTC",
                    schedule=DailyRecurrenceSchedule(hours=[0]),
                ),
                task=EvaluationScheduleTask(
                    eval_id=evaluation.id,
                    eval_run={
                        "name": "pytest-eval-run",
                        "data_source": {
                            "type": "jsonl",
                            "source": {
                                "type": "file_content",
                                "content": [{"item": {"actual": "test"}}],
                            },
                        },
                    },
                ),
            ),
        )

        try:
            deleted_schedule = client.beta.schedules.delete(schedule_id=schedule_id)

            assert deleted_schedule is None
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
        schedule_id = f"pytest-schedule-{uuid4().hex[:8]}"
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
        client.beta.schedules.create_or_update(
            schedule_id=schedule_id,
            schedule=Schedule(
                display_name="Temporary schedule created by pytest.",
                enabled=False,
                trigger=RecurrenceTrigger(
                    interval=1,
                    time_zone="UTC",
                    schedule=DailyRecurrenceSchedule(hours=[0]),
                ),
                task=EvaluationScheduleTask(
                    eval_id=evaluation.id,
                    eval_run={
                        "name": "pytest-eval-run",
                        "data_source": {
                            "type": "jsonl",
                            "source": {
                                "type": "file_content",
                                "content": [{"item": {"actual": "test"}}],
                            },
                        },
                    },
                ),
            ),
        )

        try:
            retrieved_schedule = client.beta.schedules.get(schedule_id=schedule_id)

            assert retrieved_schedule is not None
        finally:
            client.beta.schedules.delete(schedule_id=schedule_id)
            openai_client.evals.delete(eval_id=evaluation.id)


@pytest.mark.integration
def test_get_run():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        schedule_id = f"pytest-schedule-{uuid4().hex[:8]}"
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
        client.beta.schedules.create_or_update(
            schedule_id=schedule_id,
            schedule=Schedule(
                display_name="Temporary schedule created by pytest.",
                enabled=False,
                trigger=RecurrenceTrigger(
                    interval=1,
                    time_zone="UTC",
                    schedule=DailyRecurrenceSchedule(hours=[0]),
                ),
                task=EvaluationScheduleTask(
                    eval_id=evaluation.id,
                    eval_run={
                        "name": "pytest-eval-run",
                        "data_source": {
                            "type": "jsonl",
                            "source": {
                                "type": "file_content",
                                "content": [{"item": {"actual": "test"}}],
                            },
                        },
                    },
                ),
            ),
        )

        try:
            with pytest.raises(ResourceNotFoundError):
                client.beta.schedules.get_run(
                    schedule_id=schedule_id,
                    run_id=f"pytest-run-{uuid4().hex[:8]}",
                )
        finally:
            client.beta.schedules.delete(schedule_id=schedule_id)
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
        listed_schedules = list(client.beta.schedules.list())

        assert isinstance(listed_schedules, list)


@pytest.mark.integration
def test_list_runs():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        schedule_id = f"pytest-schedule-{uuid4().hex[:8]}"
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
        client.beta.schedules.create_or_update(
            schedule_id=schedule_id,
            schedule=Schedule(
                display_name="Temporary schedule created by pytest.",
                enabled=False,
                trigger=RecurrenceTrigger(
                    interval=1,
                    time_zone="UTC",
                    schedule=DailyRecurrenceSchedule(hours=[0]),
                ),
                task=EvaluationScheduleTask(
                    eval_id=evaluation.id,
                    eval_run={
                        "name": "pytest-eval-run",
                        "data_source": {
                            "type": "jsonl",
                            "source": {
                                "type": "file_content",
                                "content": [{"item": {"actual": "test"}}],
                            },
                        },
                    },
                ),
            ),
        )

        try:
            schedule_runs = list(
                client.beta.schedules.list_runs(schedule_id=schedule_id)
            )

            assert isinstance(schedule_runs, list)
        finally:
            client.beta.schedules.delete(schedule_id=schedule_id)
            openai_client.evals.delete(eval_id=evaluation.id)
