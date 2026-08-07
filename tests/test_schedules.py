from uuid import uuid4

import pytest
from azure.ai.projects.models import (
	DailyRecurrenceSchedule,
	EvaluationScheduleTask,
	RecurrenceTrigger,
	Schedule,
)

from evaluations import evals, schedules


@pytest.mark.integration
def test_create_schedule(request):
	schedule_id = f"pytest-schedule-{uuid4().hex[:8]}"
	evaluation = evals.register_eval(
		name=f"pytest-eval-{uuid4().hex[:8]}",
		data_source_config={
			"type": "custom",
			"item_schema": {
				"type": "object",
				"properties": {
					"actual": {"type": "string"},
					"expected": {"type": "string"},
				},
				"required": ["actual", "expected"],
			},
			"include_sample_schema": False,
		},
		testing_criteria=[
			{
				"type": "string_check",
				"name": "exact-match",
				"input": "{{item.actual}}",
				"reference": "{{item.expected}}",
				"operation": "eq",
			}
		],
	)
	request.addfinalizer(lambda: evals.delete_eval(eval_id=evaluation.id))

	created_schedule = schedules.create_or_update(
		schedule_id=schedule_id,
		schedule=Schedule(
			display_name="Temporary schedule created by pytest.",
			enabled=False,
			trigger=RecurrenceTrigger(
				interval=1,
				schedule=DailyRecurrenceSchedule(hours=[0]),
			),
			task=EvaluationScheduleTask(
				eval_id=evaluation.id,
				eval_run={
					"name": f"{schedule_id}-run",
					"data_source": {
						"type": "jsonl",
						"source": {
							"type": "file_content",
							"content": [
								{
									"item": {
										"actual": "test",
										"expected": "test",
									}
								}
							],
						},
					},
				},
			),
		),
	)
	request.addfinalizer(lambda: schedules.delete(schedule_id=schedule_id))

	assert created_schedule is not None


@pytest.mark.integration
def test_get_schedule(request):
	schedule_id = f"pytest-schedule-{uuid4().hex[:8]}"
	evaluation = evals.register_eval(
		name=f"pytest-eval-{uuid4().hex[:8]}",
		data_source_config={
			"type": "custom",
			"item_schema": {
				"type": "object",
				"properties": {
					"actual": {"type": "string"},
					"expected": {"type": "string"},
				},
				"required": ["actual", "expected"],
			},
			"include_sample_schema": False,
		},
		testing_criteria=[
			{
				"type": "string_check",
				"name": "exact-match",
				"input": "{{item.actual}}",
				"reference": "{{item.expected}}",
				"operation": "eq",
			}
		],
	)
	request.addfinalizer(lambda: evals.delete_eval(eval_id=evaluation.id))

	schedules.create_or_update(
		schedule_id=schedule_id,
		schedule=Schedule(
			display_name="Temporary schedule created by pytest.",
			enabled=False,
			trigger=RecurrenceTrigger(
				interval=1,
				schedule=DailyRecurrenceSchedule(hours=[0]),
			),
			task=EvaluationScheduleTask(
				eval_id=evaluation.id,
				eval_run={
					"name": f"{schedule_id}-run",
					"data_source": {
						"type": "jsonl",
						"source": {
							"type": "file_content",
							"content": [
								{
									"item": {
										"actual": "test",
										"expected": "test",
									}
								}
							],
						},
					},
				},
			),
		),
	)
	request.addfinalizer(lambda: schedules.delete(schedule_id=schedule_id))

	retrieved_schedule = schedules.get(schedule_id=schedule_id)

	assert retrieved_schedule is not None


@pytest.mark.integration
def test_list_schedules():
	listed_schedules = schedules.list_schedules()

	assert isinstance(listed_schedules, list)


@pytest.mark.integration
def test_update_schedule(request):
	schedule_id = f"pytest-schedule-{uuid4().hex[:8]}"
	evaluation = evals.register_eval(
		name=f"pytest-eval-{uuid4().hex[:8]}",
		data_source_config={
			"type": "custom",
			"item_schema": {
				"type": "object",
				"properties": {
					"actual": {"type": "string"},
					"expected": {"type": "string"},
				},
				"required": ["actual", "expected"],
			},
			"include_sample_schema": False,
		},
		testing_criteria=[
			{
				"type": "string_check",
				"name": "exact-match",
				"input": "{{item.actual}}",
				"reference": "{{item.expected}}",
				"operation": "eq",
			}
		],
	)
	request.addfinalizer(lambda: evals.delete_eval(eval_id=evaluation.id))

	schedules.create_or_update(
		schedule_id=schedule_id,
		schedule=Schedule(
			display_name="Temporary schedule created by pytest.",
			enabled=False,
			trigger=RecurrenceTrigger(
				interval=1,
				schedule=DailyRecurrenceSchedule(hours=[0]),
			),
			task=EvaluationScheduleTask(
				eval_id=evaluation.id,
				eval_run={
					"name": f"{schedule_id}-run",
					"data_source": {
						"type": "jsonl",
						"source": {
							"type": "file_content",
							"content": [
								{
									"item": {
										"actual": "test",
										"expected": "test",
									}
								}
							],
						},
					},
				},
			),
		),
	)
	request.addfinalizer(lambda: schedules.delete(schedule_id=schedule_id))

	updated_schedule = schedules.create_or_update(
		schedule_id=schedule_id,
		schedule=Schedule(
			display_name="Updated temporary schedule created by pytest.",
			enabled=False,
			trigger=RecurrenceTrigger(
				interval=1,
				schedule=DailyRecurrenceSchedule(hours=[0]),
			),
			task=EvaluationScheduleTask(
				eval_id=evaluation.id,
				eval_run={
					"name": f"{schedule_id}-run",
					"data_source": {
						"type": "jsonl",
						"source": {
							"type": "file_content",
							"content": [
								{
									"item": {
										"actual": "test",
										"expected": "test",
									}
								}
							],
						},
					},
				},
			),
		),
	)

	assert updated_schedule is not None


@pytest.mark.integration
def test_delete_schedule(request):
	schedule_id = f"pytest-schedule-{uuid4().hex[:8]}"
	evaluation = evals.register_eval(
		name=f"pytest-eval-{uuid4().hex[:8]}",
		data_source_config={
			"type": "custom",
			"item_schema": {
				"type": "object",
				"properties": {
					"actual": {"type": "string"},
					"expected": {"type": "string"},
				},
				"required": ["actual", "expected"],
			},
			"include_sample_schema": False,
		},
		testing_criteria=[
			{
				"type": "string_check",
				"name": "exact-match",
				"input": "{{item.actual}}",
				"reference": "{{item.expected}}",
				"operation": "eq",
			}
		],
	)
	request.addfinalizer(lambda: evals.delete_eval(eval_id=evaluation.id))

	schedules.create_or_update(
		schedule_id=schedule_id,
		schedule=Schedule(
			display_name="Temporary schedule created by pytest.",
			enabled=False,
			trigger=RecurrenceTrigger(
				interval=1,
				schedule=DailyRecurrenceSchedule(hours=[0]),
			),
			task=EvaluationScheduleTask(
				eval_id=evaluation.id,
				eval_run={
					"name": f"{schedule_id}-run",
					"data_source": {
						"type": "jsonl",
						"source": {
							"type": "file_content",
							"content": [
								{
									"item": {
										"actual": "test",
										"expected": "test",
									}
								}
							],
						},
					},
				},
			),
		),
	)

	deleted_schedule = schedules.delete(schedule_id=schedule_id)

	assert deleted_schedule is None


@pytest.mark.integration
def test_list_runs(request):
	schedule_id = f"pytest-schedule-{uuid4().hex[:8]}"
	evaluation = evals.register_eval(
		name=f"pytest-eval-{uuid4().hex[:8]}",
		data_source_config={
			"type": "custom",
			"item_schema": {
				"type": "object",
				"properties": {
					"actual": {"type": "string"},
					"expected": {"type": "string"},
				},
				"required": ["actual", "expected"],
			},
			"include_sample_schema": False,
		},
		testing_criteria=[
			{
				"type": "string_check",
				"name": "exact-match",
				"input": "{{item.actual}}",
				"reference": "{{item.expected}}",
				"operation": "eq",
			}
		],
	)
	request.addfinalizer(lambda: evals.delete_eval(eval_id=evaluation.id))

	schedules.create_or_update(
		schedule_id=schedule_id,
		schedule=Schedule(
			display_name="Temporary schedule created by pytest.",
			enabled=False,
			trigger=RecurrenceTrigger(
				interval=1,
				schedule=DailyRecurrenceSchedule(hours=[0]),
			),
			task=EvaluationScheduleTask(
				eval_id=evaluation.id,
				eval_run={
					"name": f"{schedule_id}-run",
					"data_source": {
						"type": "jsonl",
						"source": {
							"type": "file_content",
							"content": [
								{
									"item": {
										"actual": "test",
										"expected": "test",
									}
								}
							],
						},
					},
				},
			),
		),
	)
	request.addfinalizer(lambda: schedules.delete(schedule_id=schedule_id))

	runs = schedules.list_runs(schedule_id=schedule_id)

	assert isinstance(runs, list)