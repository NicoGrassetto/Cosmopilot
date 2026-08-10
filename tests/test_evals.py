from uuid import uuid4

import pytest
from azure.ai.projects.models import (
    CodeBasedEvaluatorDefinition,
    EvaluatorMetric,
    EvaluatorVersion,
)

from evaluations import evals


@pytest.mark.integration
def test_create_evaluator_version(request):
    evaluator_name = f"pytest-evaluator-{uuid4().hex[:8]}"

    created_evaluator = evals.create_evaluator_version(
        name=evaluator_name,
        evaluator_version=EvaluatorVersion(
            evaluator_type="custom",
            categories=["quality"],
            description="Temporary evaluator created by pytest.",
            definition=CodeBasedEvaluatorDefinition(
                code_text=(
                    "def grade(sample: dict, item: dict) -> float:\n"
                    "    return 1.0\n"
                ),
                init_parameters={"type": "object", "properties": {}},
                data_schema={
                    "type": "object",
                    "properties": {"response": {"type": "string"}},
                    "required": ["response"],
                },
                metrics={
                    "score": EvaluatorMetric(
                        type="continuous",
                        desirable_direction="increase",
                        min_value=0.0,
                        max_value=1.0,
                        threshold=0.5,
                        is_primary=True,
                    )
                },
            ),
        ),
    )
    request.addfinalizer(
        lambda: evals.delete_evaluator_version(
            name=evaluator_name,
            version=created_evaluator.version,
        )
    )

    assert created_evaluator is not None


@pytest.mark.integration
def test_get_evaluator_version(request):
    evaluator_name = f"pytest-evaluator-{uuid4().hex[:8]}"

    created_evaluator = evals.create_evaluator_version(
        name=evaluator_name,
        evaluator_version=EvaluatorVersion(
            evaluator_type="custom",
            categories=["quality"],
            description="Temporary evaluator created by pytest.",
            definition=CodeBasedEvaluatorDefinition(
                code_text=(
                    "def grade(sample: dict, item: dict) -> float:\n"
                    "    return 1.0\n"
                ),
                init_parameters={"type": "object", "properties": {}},
                data_schema={
                    "type": "object",
                    "properties": {"response": {"type": "string"}},
                    "required": ["response"],
                },
                metrics={
                    "score": EvaluatorMetric(
                        type="continuous",
                        desirable_direction="increase",
                        min_value=0.0,
                        max_value=1.0,
                        threshold=0.5,
                        is_primary=True,
                    )
                },
            ),
        ),
    )
    request.addfinalizer(
        lambda: evals.delete_evaluator_version(
            name=evaluator_name,
            version=created_evaluator.version,
        )
    )

    retrieved_evaluator = evals.get_evaluator_version(
        name=evaluator_name,
        version=created_evaluator.version,
    )

    assert retrieved_evaluator is not None


@pytest.mark.integration
def test_list_evaluators():
    listed_evaluators = evals.list_evaluators()

    assert isinstance(listed_evaluators, list)


@pytest.mark.integration
def test_list_evaluator_versions(request):
    evaluator_name = f"pytest-evaluator-{uuid4().hex[:8]}"

    created_evaluator = evals.create_evaluator_version(
        name=evaluator_name,
        evaluator_version=EvaluatorVersion(
            evaluator_type="custom",
            categories=["quality"],
            description="Temporary evaluator created by pytest.",
            definition=CodeBasedEvaluatorDefinition(
                code_text=(
                    "def grade(sample: dict, item: dict) -> float:\n"
                    "    return 1.0\n"
                ),
                init_parameters={"type": "object", "properties": {}},
                data_schema={
                    "type": "object",
                    "properties": {"response": {"type": "string"}},
                    "required": ["response"],
                },
                metrics={
                    "score": EvaluatorMetric(
                        type="continuous",
                        desirable_direction="increase",
                        min_value=0.0,
                        max_value=1.0,
                        threshold=0.5,
                        is_primary=True,
                    )
                },
            ),
        ),
    )
    request.addfinalizer(
        lambda: evals.delete_evaluator_version(
            name=evaluator_name,
            version=created_evaluator.version,
        )
    )

    versions = evals.list_evaluator_versions(name=evaluator_name)

    assert versions


@pytest.mark.integration
def test_update_evaluator_version(request):
    evaluator_name = f"pytest-evaluator-{uuid4().hex[:8]}"

    created_evaluator = evals.create_evaluator_version(
        name=evaluator_name,
        evaluator_version=EvaluatorVersion(
            evaluator_type="custom",
            categories=["quality"],
            description="Temporary evaluator created by pytest.",
            definition=CodeBasedEvaluatorDefinition(
                code_text=(
                    "def grade(sample: dict, item: dict) -> float:\n"
                    "    return 1.0\n"
                ),
                init_parameters={"type": "object", "properties": {}},
                data_schema={
                    "type": "object",
                    "properties": {"response": {"type": "string"}},
                    "required": ["response"],
                },
                metrics={
                    "score": EvaluatorMetric(
                        type="continuous",
                        desirable_direction="increase",
                        min_value=0.0,
                        max_value=1.0,
                        threshold=0.5,
                        is_primary=True,
                    )
                },
            ),
        ),
    )
    request.addfinalizer(
        lambda: evals.delete_evaluator_version(
            name=evaluator_name,
            version=created_evaluator.version,
        )
    )

    updated_evaluator = evals.update_evaluator_version(
        name=evaluator_name,
        version=created_evaluator.version,
        evaluator_version=EvaluatorVersion(
            evaluator_type="custom",
            categories=["quality"],
            description="Updated temporary evaluator created by pytest.",
            definition=CodeBasedEvaluatorDefinition(
                code_text=(
                    "def grade(sample: dict, item: dict) -> float:\n"
                    "    return 1.0\n"
                ),
                init_parameters={"type": "object", "properties": {}},
                data_schema={
                    "type": "object",
                    "properties": {"response": {"type": "string"}},
                    "required": ["response"],
                },
                metrics={
                    "score": EvaluatorMetric(
                        type="continuous",
                        desirable_direction="increase",
                        min_value=0.0,
                        max_value=1.0,
                        threshold=0.5,
                        is_primary=True,
                    )
                },
            ),
        ),
    )

    assert updated_evaluator is not None


@pytest.mark.integration
def test_delete_evaluator_version():
    evaluator_name = f"pytest-evaluator-{uuid4().hex[:8]}"

    created_evaluator = evals.create_evaluator_version(
        name=evaluator_name,
        evaluator_version=EvaluatorVersion(
            evaluator_type="custom",
            categories=["quality"],
            description="Temporary evaluator created by pytest.",
            definition=CodeBasedEvaluatorDefinition(
                code_text=(
                    "def grade(sample: dict, item: dict) -> float:\n"
                    "    return 1.0\n"
                ),
                init_parameters={"type": "object", "properties": {}},
                data_schema={
                    "type": "object",
                    "properties": {"response": {"type": "string"}},
                    "required": ["response"],
                },
                metrics={
                    "score": EvaluatorMetric(
                        type="continuous",
                        desirable_direction="increase",
                        min_value=0.0,
                        max_value=1.0,
                        threshold=0.5,
                        is_primary=True,
                    )
                },
            ),
        ),
    )

    deleted_evaluator = evals.delete_evaluator_version(
        name=evaluator_name,
        version=created_evaluator.version,
    )

    assert deleted_evaluator is None