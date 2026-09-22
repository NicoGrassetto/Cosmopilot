import os
from uuid import uuid4

import pytest
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    AgentInsightMonitorCreate,
    AgentInsightMonitorUpdate,
    AgentInsightRunCreate,
    AgentInsightStatus,
    AgentInsightUpdate,
)
from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential


@pytest.mark.integration
def test_begin_create_run():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        monitor = client.beta.agent_insight_monitors.create(
            monitor=AgentInsightMonitorCreate(
                agent_name="weather-agent",
                model_deployment_name=os.environ["AZURE_DEPLOYMENT_NAME"],
                enabled=False,
            ),
        )

        try:
            run_result = client.beta.agent_insight_monitors.begin_create_run(
                monitor_id=monitor.id,
                run=AgentInsightRunCreate(lookback_hours=1),
            ).result()

            assert run_result is not None
        finally:
            client.beta.agent_insight_monitors.delete(monitor_id=monitor.id)


@pytest.mark.integration
def test_cancel_run():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        monitor = client.beta.agent_insight_monitors.create(
            monitor=AgentInsightMonitorCreate(
                agent_name="weather-agent",
                model_deployment_name=os.environ["AZURE_DEPLOYMENT_NAME"],
                enabled=False,
            ),
        )
        run = client.beta.agent_insight_monitors.begin_create_run(
            monitor_id=monitor.id,
            run=AgentInsightRunCreate(lookback_hours=1),
        )

        try:
            cancelled_run = client.beta.agent_insight_monitors.cancel_run(
                monitor_id=monitor.id,
                run_id=run.details["run_id"],
            )

            assert cancelled_run is not None
        finally:
            client.beta.agent_insight_monitors.delete(monitor_id=monitor.id)


@pytest.mark.integration
def test_create():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        monitor = client.beta.agent_insight_monitors.create(
            monitor=AgentInsightMonitorCreate(
                agent_name="weather-agent",
                model_deployment_name=os.environ["AZURE_DEPLOYMENT_NAME"],
                enabled=False,
            ),
        )

        try:
            assert monitor is not None
        finally:
            client.beta.agent_insight_monitors.delete(monitor_id=monitor.id)


@pytest.mark.integration
def test_delete():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        monitor = client.beta.agent_insight_monitors.create(
            monitor=AgentInsightMonitorCreate(
                agent_name="weather-agent",
                model_deployment_name=os.environ["AZURE_DEPLOYMENT_NAME"],
                enabled=False,
            ),
        )

        deleted_monitor = client.beta.agent_insight_monitors.delete(
            monitor_id=monitor.id,
        )

        assert deleted_monitor is None


@pytest.mark.integration
def test_get():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        monitor = client.beta.agent_insight_monitors.create(
            monitor=AgentInsightMonitorCreate(
                agent_name="weather-agent",
                model_deployment_name=os.environ["AZURE_DEPLOYMENT_NAME"],
                enabled=False,
            ),
        )

        try:
            retrieved_monitor = client.beta.agent_insight_monitors.get(
                monitor_id=monitor.id,
            )

            assert retrieved_monitor is not None
        finally:
            client.beta.agent_insight_monitors.delete(monitor_id=monitor.id)


@pytest.mark.integration
def test_get_insight():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        monitor = client.beta.agent_insight_monitors.create(
            monitor=AgentInsightMonitorCreate(
                agent_name="weather-agent",
                model_deployment_name=os.environ["AZURE_DEPLOYMENT_NAME"],
                enabled=False,
            ),
        )

        try:
            with pytest.raises(ResourceNotFoundError):
                client.beta.agent_insight_monitors.get_insight(
                    monitor_id=monitor.id,
                    insight_id=f"pytest-insight-{uuid4().hex[:8]}",
                )
        finally:
            client.beta.agent_insight_monitors.delete(monitor_id=monitor.id)


@pytest.mark.integration
def test_get_run():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        monitor = client.beta.agent_insight_monitors.create(
            monitor=AgentInsightMonitorCreate(
                agent_name="weather-agent",
                model_deployment_name=os.environ["AZURE_DEPLOYMENT_NAME"],
                enabled=False,
            ),
        )
        run = client.beta.agent_insight_monitors.begin_create_run(
            monitor_id=monitor.id,
            run=AgentInsightRunCreate(lookback_hours=1),
        )

        try:
            retrieved_run = client.beta.agent_insight_monitors.get_run(
                monitor_id=monitor.id,
                run_id=run.details["run_id"],
            )

            assert retrieved_run is not None
        finally:
            client.beta.agent_insight_monitors.delete(monitor_id=monitor.id)


@pytest.mark.integration
def test_list():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        listed_monitors = list(client.beta.agent_insight_monitors.list())

        assert isinstance(listed_monitors, list)


@pytest.mark.integration
def test_list_insights():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        monitor = client.beta.agent_insight_monitors.create(
            monitor=AgentInsightMonitorCreate(
                agent_name="weather-agent",
                model_deployment_name=os.environ["AZURE_DEPLOYMENT_NAME"],
                enabled=False,
            ),
        )

        try:
            listed_insights = list(
                client.beta.agent_insight_monitors.list_insights(
                    monitor_id=monitor.id,
                )
            )

            assert isinstance(listed_insights, list)
        finally:
            client.beta.agent_insight_monitors.delete(monitor_id=monitor.id)


@pytest.mark.integration
def test_list_runs():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        monitor = client.beta.agent_insight_monitors.create(
            monitor=AgentInsightMonitorCreate(
                agent_name="weather-agent",
                model_deployment_name=os.environ["AZURE_DEPLOYMENT_NAME"],
                enabled=False,
            ),
        )

        try:
            listed_runs = list(
                client.beta.agent_insight_monitors.list_runs(monitor_id=monitor.id)
            )

            assert isinstance(listed_runs, list)
        finally:
            client.beta.agent_insight_monitors.delete(monitor_id=monitor.id)


@pytest.mark.integration
def test_reset():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        monitor = client.beta.agent_insight_monitors.create(
            monitor=AgentInsightMonitorCreate(
                agent_name="weather-agent",
                model_deployment_name=os.environ["AZURE_DEPLOYMENT_NAME"],
                enabled=False,
            ),
        )

        try:
            reset_monitor = client.beta.agent_insight_monitors.reset(
                monitor_id=monitor.id,
            )

            assert reset_monitor is None
        finally:
            client.beta.agent_insight_monitors.delete(monitor_id=monitor.id)


@pytest.mark.integration
def test_update():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        monitor = client.beta.agent_insight_monitors.create(
            monitor=AgentInsightMonitorCreate(
                agent_name="weather-agent",
                model_deployment_name=os.environ["AZURE_DEPLOYMENT_NAME"],
                enabled=False,
            ),
        )

        try:
            updated_monitor = client.beta.agent_insight_monitors.update(
                monitor_id=monitor.id,
                monitor=AgentInsightMonitorUpdate(run_interval_hours=24),
            )

            assert updated_monitor is not None
        finally:
            client.beta.agent_insight_monitors.delete(monitor_id=monitor.id)


@pytest.mark.integration
def test_update_insight():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        monitor = client.beta.agent_insight_monitors.create(
            monitor=AgentInsightMonitorCreate(
                agent_name="weather-agent",
                model_deployment_name=os.environ["AZURE_DEPLOYMENT_NAME"],
                enabled=False,
            ),
        )

        try:
            with pytest.raises(ResourceNotFoundError):
                client.beta.agent_insight_monitors.update_insight(
                    monitor_id=monitor.id,
                    insight_id=f"pytest-insight-{uuid4().hex[:8]}",
                    update=AgentInsightUpdate(status=AgentInsightStatus.IGNORED),
                )
        finally:
            client.beta.agent_insight_monitors.delete(monitor_id=monitor.id)
