"""Evaluation logic for Cosmopilot.

Two functions:

* ``run`` — runs the whole evaluation suite: registers the reusable OpenAI-graded
  evals in the Foundry project, then runs every ready-made ``azure-ai-evaluation``
  built-in evaluator (quality, safety, and agent) over the dataset.
* ``upload_dataset`` — registers (uploads) the eval dataset in the Foundry project.
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
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

PREFIX = "cosmopilot"

DATASET_NAME = f"{PREFIX}-eval-dataset"
DATASET_VERSION = "1"

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


def run():
    """Run the whole evaluation suite (registers evals, then runs all evaluators)."""
    endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
    model = os.environ.get("AZURE_DEPLOYMENT_NAME", "gpt-4o-mini")
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")

    credential = DefaultAzureCredential()
    client = AIProjectClient(endpoint=endpoint, credential=credential)
    openai_client = client.get_openai_client()

    # -----------------------------------------------------------------------
    # Register (create) the reusable OpenAI-graded evals in the Foundry project.
    # -----------------------------------------------------------------------
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

    # -----------------------------------------------------------------------
    # Built-in azure-ai-evaluation evaluators (run over a JSONL dataset).
    #
    # AI-assisted evaluators need a judge model (evaluator_model_config); safety
    # evaluators call the Azure AI Content Safety service and need the project +
    # a credential instead.
    #
    # NOTE: These built-in evaluators are portal/preview-only and are NOT exposed
    # as importable classes in the azure-ai-evaluation SDK (v1.18), so they can't
    # be constructed here — configure them from the Foundry portal instead:
    #   Rubric, Task Completion, Customer Satisfaction, Task Navigation Efficiency,
    #   Tool Selection, Tool Input Accuracy, Tool Output Utilization,
    #   Tool Call Success, Quality Grader, Prohibited Actions, Sensitive Data Leakage.
    # -----------------------------------------------------------------------
    evaluator_model_config = {
        "azure_endpoint": endpoint,
        "azure_deployment": model,
        "api_version": os.environ.get("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
    }
    azure_ai_project = endpoint

    # Quality / textual-similarity / RAG. Fields: query, response, context, ground_truth.
    quality_evaluators = {
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

    # Risk and safety. Fields: query, response (content is sent to Content Safety).
    safety_evaluators = {
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

    # Agent. Require agent traces: tool_calls + tool_definitions plus query/response.
    agent_evaluators = {
        "intent_resolution": IntentResolutionEvaluator(evaluator_model_config),
        "task_adherence": TaskAdherenceEvaluator(evaluator_model_config),
        "tool_call_accuracy": ToolCallAccuracyEvaluator(evaluator_model_config),
    }

    # evaluate() expects a JSONL file with query/response/context/ground_truth
    # fields, so convert the CSV dataset into that layout first.
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


def upload_dataset(name=DATASET_NAME, version=DATASET_VERSION):
    """Register (upload) the eval dataset in the Foundry project.

    Converts the Q&A CSV into the JSONL layout, uploads it as a Foundry dataset,
    and returns the resulting dataset version (which carries an ``id``).
    """
    endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")

    credential = DefaultAzureCredential()
    client = AIProjectClient(endpoint=endpoint, credential=credential)

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
                        "context": _row["answer"],
                    }
                )
                + "\n"
            )

    dataset = client.datasets.upload_file(
        name=name,
        version=version,
        file_path=dataset_jsonl,
    )
    print(f"Uploaded dataset {name}:{version} -> {dataset.id}")
    return dataset


if __name__ == "__main__":
    import sys

    command = sys.argv[1] if len(sys.argv) > 1 else "run"

    if command == "upload":
        upload_dataset()
    elif command == "run":
        run()
    elif command == "all":
        upload_dataset()
        run()
    else:
        raise SystemExit(f"Unknown command {command!r}. Use one of: upload | run | all")
