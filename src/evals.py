"""Evaluation logic for Cosmopilot.

Two distinct concerns live here:

* ``register_evals`` — creates (registers) reusable, OpenAI-graded evals in the
  Foundry project via ``openai_client.evals.create``. These are persistent eval
  objects that ``tests/run_eval.py`` can later look up by name and run.
* ``run_builtin_evaluations`` — one-shot runs of the ready-made ``azure-ai-evaluation``
  built-in evaluators over a JSONL dataset via ``evaluate``.
"""

import csv
import json
import os

from azure.ai.evaluation import (
    BleuScoreEvaluator,
    CodeVulnerabilityEvaluator,
    CoherenceEvaluator,
    ContentSafetyEvaluator,
    DocumentRetrievalEvaluator,
    F1ScoreEvaluator,
    FluencyEvaluator,
    GleuScoreEvaluator,
    GroundednessEvaluator,
    GroundednessProEvaluator,
    HateUnfairnessEvaluator,
    IndirectAttackEvaluator,
    IntentResolutionEvaluator,
    MeteorScoreEvaluator,
    ProtectedMaterialEvaluator,
    RelevanceEvaluator,
    ResponseCompletenessEvaluator,
    RetrievalEvaluator,
    RougeScoreEvaluator,
    RougeType,
    SelfHarmEvaluator,
    SexualEvaluator,
    SimilarityEvaluator,
    TaskAdherenceEvaluator,
    ToolCallAccuracyEvaluator,
    UngroundedAttributesEvaluator,
    ViolenceEvaluator,
    evaluate,
)

PREFIX = "cosmopilot"

custom_data_source_config = {
    "type": "custom",
    "item_schema": {
        "type": "object",
        "properties": {
            "question": {"type": "string"},
            "answer": {"type": "string"},
        },
        "required": ["question", "answer"],
    },
    "include_sample_schema": True,
}

logs_data_source_config = {
    "type": "logs",
    "metadata": {
        "usecase": "cosmos-assistant",
    },
}

# NOTE: The public OpenAI SDK type also lists "cosine", but the Azure Foundry
# eval service rejects it (400 UserError), so it's intentionally excluded here.
TEXT_SIMILARITY_METRICS = [
    "fuzzy_match",
    "bleu",
    "gleu",
    "meteor",
    "rouge_1",
    "rouge_2",
    "rouge_3",
    "rouge_4",
    "rouge_5",
    "rouge_l",
]


def register_evals(openai_client, model):
    """Create (register) the reusable OpenAI-graded evals in the Foundry project."""
    openai_client.evals.create(
        name=f"{PREFIX}-relevant",
        data_source_config=custom_data_source_config,
        testing_criteria=[
            {
                "type": "label_model",
                "name": "relevance-grader",
                "model": model,
                "input": [
                    {
                        "role": "developer",
                        "content": (
                            "Label whether the answer is relevant to the user's "
                            "question about Azure Cosmos DB operations. "
                            "Respond with 'relevant' or 'irrelevant'."
                        ),
                    },
                    {
                        "role": "user",
                        "content": "Question: {{item.question}}\nAnswer: {{sample.output_text}}",
                    },
                ],
                "labels": ["relevant", "irrelevant"],
                "passing_labels": ["relevant"],
            }
        ],
    )

    openai_client.evals.create(
        name=f"{PREFIX}-text_similarity",
        data_source_config=custom_data_source_config,
        testing_criteria=[
            {
                "type": "text_similarity",
                "name": f"answer-similarity-{metric}",
                "input": "{{sample.output_text}}",
                "reference": "{{item.answer}}",
                "evaluation_metric": metric,
                "pass_threshold": 0.8,
            }
            for metric in TEXT_SIMILARITY_METRICS
        ],
    )

    openai_client.evals.create(
        name=f"{PREFIX}-string_check",
        data_source_config=custom_data_source_config,
        testing_criteria=[
            {
                "type": "string_check",
                "name": "answer-exact-match",
                "input": "{{sample.output_text}}",
                "reference": "{{item.answer}}",
                "operation": "eq",
            }
        ],
    )

    openai_client.evals.create(
        name=f"{PREFIX}-score_model",
        data_source_config=custom_data_source_config,
        testing_criteria=[
            {
                "type": "score_model",
                "name": "answer-quality-scorer",
                "model": model,
                "input": [
                    {
                        "role": "developer",
                        "content": (
                            "Score how well the answer resolves the user's question "
                            "about Azure Cosmos DB operations, from 0 (useless) to 1 "
                            "(fully correct and complete). Respond with only the number."
                        ),
                    },
                    {
                        "role": "user",
                        "content": "Question: {{item.question}}\nAnswer: {{sample.output_text}}",
                    },
                ],
                "range": [0, 1],
                "pass_threshold": 0.7,
            }
        ],
    )


def _build_quality_evaluators(evaluator_model_config, credential, azure_ai_project):
    """Quality / textual-similarity / RAG evaluators.

    Compatible dataset fields: query, response, context, ground_truth.
    """
    return {
        "coherence": CoherenceEvaluator(evaluator_model_config),
        "fluency": FluencyEvaluator(evaluator_model_config),
        "similarity": SimilarityEvaluator(evaluator_model_config),
        "f1_score": F1ScoreEvaluator(),
        "bleu": BleuScoreEvaluator(),
        "gleu": GleuScoreEvaluator(),
        "meteor": MeteorScoreEvaluator(),
        "rouge": RougeScoreEvaluator(RougeType.ROUGE_L),
        "retrieval": RetrievalEvaluator(evaluator_model_config),
        "groundedness": GroundednessEvaluator(evaluator_model_config),
        "groundedness_pro": GroundednessProEvaluator(credential, azure_ai_project),
        "relevance": RelevanceEvaluator(evaluator_model_config),
        "response_completeness": ResponseCompletenessEvaluator(evaluator_model_config),
        # DocumentRetrievalEvaluator needs a retrieval-specific dataset
        # (retrieval_ground_truth + retrieved_documents), so run it separately.
        "document_retrieval": DocumentRetrievalEvaluator(),
    }


def _build_safety_evaluators(credential, azure_ai_project):
    """Risk and safety evaluators.

    Compatible dataset fields: query, response (content is sent to Content Safety).
    """
    return {
        "content_safety": ContentSafetyEvaluator(credential, azure_ai_project),
        "hate_unfairness": HateUnfairnessEvaluator(credential, azure_ai_project),
        "sexual": SexualEvaluator(credential, azure_ai_project),
        "violence": ViolenceEvaluator(credential, azure_ai_project),
        "self_harm": SelfHarmEvaluator(credential, azure_ai_project),
        "protected_material": ProtectedMaterialEvaluator(credential, azure_ai_project),
        "indirect_attack": IndirectAttackEvaluator(credential, azure_ai_project),
        "code_vulnerability": CodeVulnerabilityEvaluator(credential, azure_ai_project),
        "ungrounded_attributes": UngroundedAttributesEvaluator(credential, azure_ai_project),
    }


def _build_agent_evaluators(evaluator_model_config):
    """Agent evaluators.

    Require a dataset with agent traces: tool_calls + tool_definitions in addition
    to query/response. Run against an agent-run dataset, not the simple Q&A CSV.
    """
    return {
        "intent_resolution": IntentResolutionEvaluator(evaluator_model_config),
        "task_adherence": TaskAdherenceEvaluator(evaluator_model_config),
        "tool_call_accuracy": ToolCallAccuracyEvaluator(evaluator_model_config),
    }


def _prepare_dataset(data_dir):
    """Convert the Q&A CSV into the JSONL layout ``evaluate`` expects.

    Returns the path to the generated JSONL file (query/response/context/ground_truth).
    """
    dataset_csv = os.path.join(data_dir, "eval_dataset.csv")
    dataset_jsonl = os.path.join(data_dir, "eval_dataset.jsonl")

    with open(dataset_csv, newline="") as _src, open(dataset_jsonl, "w") as _dst:
        for _row in csv.DictReader(_src):
            _dst.write(
                json.dumps(
                    {
                        "query": _row["question"],
                        "response": _row["answer"],
                        "ground_truth": _row["answer"],
                        # The dataset has no separate source context, so the
                        # reference answer stands in as the grounding context.
                        "context": _row["answer"],
                    }
                )
                + "\n"
            )

    return dataset_jsonl


def run_builtin_evaluations(credential, model, endpoint, data_dir):
    """Run the ready-made ``azure-ai-evaluation`` built-in evaluators over the dataset."""
    # AI-assisted evaluators need a judge model (evaluator_model_config).
    evaluator_model_config = {
        "azure_endpoint": endpoint,
        "azure_deployment": model,
        "api_version": os.environ.get("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
    }

    # Safety evaluators call the Azure AI Content Safety service and need the
    # project + a credential instead of a judge-model config.
    azure_ai_project = endpoint

    # NOTE: The following built-in evaluators are portal/preview-only and are NOT
    # exposed as importable classes in the azure-ai-evaluation SDK (v1.18), so they
    # can't be constructed here. Configure them from the Foundry portal instead:
    #   Rubric, Task Completion, Customer Satisfaction, Task Navigation Efficiency,
    #   Tool Selection, Tool Input Accuracy, Tool Output Utilization,
    #   Tool Call Success, Quality Grader, Prohibited Actions, Sensitive Data Leakage.

    quality_evaluators = _build_quality_evaluators(
        evaluator_model_config, credential, azure_ai_project
    )
    safety_evaluators = _build_safety_evaluators(credential, azure_ai_project)
    agent_evaluators = _build_agent_evaluators(evaluator_model_config)

    dataset_jsonl = _prepare_dataset(data_dir)

    # Each run uses only evaluators compatible with the dataset it points at.
    # All evaluators in a single evaluate() call must accept the same input fields.
    evaluate(
        data=dataset_jsonl,
        evaluators=quality_evaluators,
        azure_ai_project=azure_ai_project,
    )

    evaluate(
        data=dataset_jsonl,
        evaluators=safety_evaluators,
        azure_ai_project=azure_ai_project,
    )

    # The agent run needs an agent-trace dataset (with tool_calls / tool_definitions).
    # Point agent_dataset_jsonl at that dataset before enabling this run.
    agent_dataset_jsonl = os.path.join(data_dir, "agent_eval_dataset.jsonl")
    if os.path.exists(agent_dataset_jsonl):
        evaluate(
            data=agent_dataset_jsonl,
            evaluators=agent_evaluators,
            azure_ai_project=azure_ai_project,
        )
