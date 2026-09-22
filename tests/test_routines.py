import os
from uuid import uuid4

import pytest
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    InvokeAgentResponsesApiDispatchPayload,
    InvokeAgentResponsesApiRoutineAction,
    ScheduleRoutineTrigger,
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
        routine_name = f"pytest-routine-{uuid4().hex[:8]}"

        try:
            created_routine = client.beta.routines.create_or_update(
                routine_name=routine_name,
                description="Temporary routine created by pytest.",
                enabled=False,
                triggers={
                    "annual-test": ScheduleRoutineTrigger(
                        cron_expression="0 0 1 1 *",
                        time_zone="UTC",
                    )
                },
                action=InvokeAgentResponsesApiRoutineAction(
                    agent_name="weather-agent",
                    input="Return a concise test response.",
                ),
            )

            assert created_routine is not None
        finally:
            client.beta.routines.delete(routine_name=routine_name)


@pytest.mark.integration
def test_delete():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        routine_name = f"pytest-routine-{uuid4().hex[:8]}"
        client.beta.routines.create_or_update(
            routine_name=routine_name,
            description="Temporary routine created by pytest.",
            enabled=False,
            triggers={
                "annual-test": ScheduleRoutineTrigger(
                    cron_expression="0 0 1 1 *",
                    time_zone="UTC",
                )
            },
            action=InvokeAgentResponsesApiRoutineAction(
                agent_name="weather-agent",
                input="Return a concise test response.",
            ),
        )

        deleted_routine = client.beta.routines.delete(routine_name=routine_name)

        assert deleted_routine is None


@pytest.mark.integration
def test_disable():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        routine_name = f"pytest-routine-{uuid4().hex[:8]}"
        client.beta.routines.create_or_update(
            routine_name=routine_name,
            description="Temporary routine created by pytest.",
            enabled=True,
            triggers={
                "annual-test": ScheduleRoutineTrigger(
                    cron_expression="0 0 1 1 *",
                    time_zone="UTC",
                )
            },
            action=InvokeAgentResponsesApiRoutineAction(
                agent_name="weather-agent",
                input="Return a concise test response.",
            ),
        )

        try:
            disabled_routine = client.beta.routines.disable(routine_name=routine_name)

            assert disabled_routine is not None
        finally:
            client.beta.routines.delete(routine_name=routine_name)


@pytest.mark.integration
def test_dispatch():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        routine_name = f"pytest-routine-{uuid4().hex[:8]}"
        client.beta.routines.create_or_update(
            routine_name=routine_name,
            description="Temporary routine created by pytest.",
            enabled=True,
            triggers={
                "annual-test": ScheduleRoutineTrigger(
                    cron_expression="0 0 1 1 *",
                    time_zone="UTC",
                )
            },
            action=InvokeAgentResponsesApiRoutineAction(
                agent_name="weather-agent",
                input="Return a concise test response.",
            ),
        )

        try:
            dispatched_routine = client.beta.routines.dispatch(
                routine_name=routine_name,
                payload=InvokeAgentResponsesApiDispatchPayload(
                    input="Return a concise test response.",
                ),
            )

            assert dispatched_routine is not None
        finally:
            client.beta.routines.delete(routine_name=routine_name)


@pytest.mark.integration
def test_enable():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        routine_name = f"pytest-routine-{uuid4().hex[:8]}"
        client.beta.routines.create_or_update(
            routine_name=routine_name,
            description="Temporary routine created by pytest.",
            enabled=False,
            triggers={
                "annual-test": ScheduleRoutineTrigger(
                    cron_expression="0 0 1 1 *",
                    time_zone="UTC",
                )
            },
            action=InvokeAgentResponsesApiRoutineAction(
                agent_name="weather-agent",
                input="Return a concise test response.",
            ),
        )

        try:
            enabled_routine = client.beta.routines.enable(routine_name=routine_name)

            assert enabled_routine is not None
        finally:
            client.beta.routines.delete(routine_name=routine_name)


@pytest.mark.integration
def test_get():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        routine_name = f"pytest-routine-{uuid4().hex[:8]}"
        client.beta.routines.create_or_update(
            routine_name=routine_name,
            description="Temporary routine created by pytest.",
            enabled=False,
            triggers={
                "annual-test": ScheduleRoutineTrigger(
                    cron_expression="0 0 1 1 *",
                    time_zone="UTC",
                )
            },
            action=InvokeAgentResponsesApiRoutineAction(
                agent_name="weather-agent",
                input="Return a concise test response.",
            ),
        )

        try:
            retrieved_routine = client.beta.routines.get(routine_name=routine_name)

            assert retrieved_routine is not None
        finally:
            client.beta.routines.delete(routine_name=routine_name)


@pytest.mark.integration
def test_list():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        listed_routines = list(client.beta.routines.list())

        assert isinstance(listed_routines, list)


@pytest.mark.integration
def test_list_runs():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        routine_name = f"pytest-routine-{uuid4().hex[:8]}"
        client.beta.routines.create_or_update(
            routine_name=routine_name,
            description="Temporary routine created by pytest.",
            enabled=False,
            triggers={
                "annual-test": ScheduleRoutineTrigger(
                    cron_expression="0 0 1 1 *",
                    time_zone="UTC",
                )
            },
            action=InvokeAgentResponsesApiRoutineAction(
                agent_name="weather-agent",
                input="Return a concise test response.",
            ),
        )

        try:
            routine_runs = list(client.beta.routines.list_runs(routine_name=routine_name))

            assert isinstance(routine_runs, list)
        finally:
            client.beta.routines.delete(routine_name=routine_name)
