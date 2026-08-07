from uuid import uuid4

import pytest
from azure.ai.projects.models import (
	InvokeAgentResponsesApiRoutineAction,
	ScheduleRoutineTrigger,
)

from agents import routines


@pytest.mark.integration
def test_create_routine(request):
	routine_name = f"pytest-routine-{uuid4().hex[:8]}"

	created_routine = routines.create(
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
	request.addfinalizer(
		lambda: routines.delete(routine_name=routine_name)
	)

	assert created_routine is not None


@pytest.mark.integration
def test_get_routine(request):
	routine_name = f"pytest-routine-{uuid4().hex[:8]}"

	routines.create(
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
	request.addfinalizer(
		lambda: routines.delete(routine_name=routine_name)
	)

	retrieved_routine = routines.get(routine_name=routine_name)

	assert retrieved_routine is not None


@pytest.mark.integration
def test_list_routines():
	listed_routines = routines.list_routines()

	assert isinstance(listed_routines, list)


@pytest.mark.integration
def test_update_routine(request):
	routine_name = f"pytest-routine-{uuid4().hex[:8]}"

	routines.create(
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
	request.addfinalizer(
		lambda: routines.delete(routine_name=routine_name)
	)

	updated_routine = routines.update(
		routine_name=routine_name,
		description="Updated temporary routine created by pytest.",
		enabled=False,
		triggers={
			"annual-test": ScheduleRoutineTrigger(
				cron_expression="0 0 1 1 *",
				time_zone="UTC",
			)
		},
		action=InvokeAgentResponsesApiRoutineAction(
			agent_name="weather-agent",
			input="Return an updated concise test response.",
		),
	)

	assert updated_routine is not None


@pytest.mark.integration
def test_delete_routine():
	routine_name = f"pytest-routine-{uuid4().hex[:8]}"

	routines.create(
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

	deleted_routine = routines.delete(routine_name=routine_name)

	assert deleted_routine is None


@pytest.mark.integration
def test_disable_routine(request):
	routine_name = f"pytest-routine-{uuid4().hex[:8]}"

	routines.create(
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
	request.addfinalizer(
		lambda: routines.delete(routine_name=routine_name)
	)

	disabled_routine = routines.disable(routine_name=routine_name)

	assert disabled_routine is not None


@pytest.mark.integration
def test_enable_routine(request):
	routine_name = f"pytest-routine-{uuid4().hex[:8]}"

	routines.create(
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
	request.addfinalizer(
		lambda: routines.delete(routine_name=routine_name)
	)

	enabled_routine = routines.enable(routine_name=routine_name)

	assert enabled_routine is not None


@pytest.mark.integration
def test_list_runs(request):
	routine_name = f"pytest-routine-{uuid4().hex[:8]}"

	routines.create(
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
	request.addfinalizer(
		lambda: routines.delete(routine_name=routine_name)
	)

	runs = routines.list_runs(routine_name=routine_name)

	assert isinstance(runs, list)
