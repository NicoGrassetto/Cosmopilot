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
from azure.ai.projects import FoundryClient
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
client = FoundryClient(
    endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
    credential=credential,
)

openai_client = client.get_openai_client()

model = os.environ.get("AZURE_DEPLOYMENT_NAME", "gpt-4o-mini")

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

TEXT_SIMILARITY_METRICS = [
    "cosine",
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

# ---------------------------------------------------------------------------
# Foundry built-in evaluators (azure-ai-evaluation SDK).
#
# Unlike the openai_client.evals.create() graders above, these are ready-made,
# AI-assisted evaluators. They need a judge model (evaluator_model_config) and
# run directly over a JSONL dataset via evaluate().
# ---------------------------------------------------------------------------
evaluator_model_config = {
    "azure_endpoint": os.environ["AZURE_AI_PROJECT_ENDPOINT"],
    "azure_deployment": model,
    "api_version": os.environ.get("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
}

# Safety evaluators call the Azure AI Content Safety service and need the
# project + a credential instead of a judge-model config.
azure_ai_project = os.environ["AZURE_AI_PROJECT_ENDPOINT"]

# NOTE: The following built-in evaluators are portal/preview-only and are NOT
# exposed as importable classes in the azure-ai-evaluation SDK (v1.18), so they
# can't be constructed here. Configure them from the Foundry portal instead:
#   Rubric, Task Completion, Customer Satisfaction, Task Navigation Efficiency,
#   Tool Selection, Tool Input Accuracy, Tool Output Utilization,
#   Tool Call Success, Quality Grader, Prohibited Actions, Sensitive Data Leakage.

# --- Quality / textual-similarity / RAG ------------------------------------
# Compatible dataset fields: query, response, context, ground_truth.
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

# --- Risk and safety --------------------------------------------------------
# Compatible dataset fields: query, response (content is sent to Content Safety).
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

# --- Agent ------------------------------------------------------------------
# Require a dataset with agent traces: tool_calls + tool_definitions in addition
# to query/response. Run against an agent-run dataset, not the simple Q&A CSV.
agent_evaluators = {
    "intent_resolution": IntentResolutionEvaluator(evaluator_model_config),
    "task_adherence": TaskAdherenceEvaluator(evaluator_model_config),
    "tool_call_accuracy": ToolCallAccuracyEvaluator(evaluator_model_config),
}

# evaluate() expects a JSONL file with query/response/context/ground_truth
# fields, so convert the CSV dataset into that layout first.
_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DATASET_CSV = os.path.join(_DATA_DIR, "eval_dataset.csv")
DATASET_JSONL = os.path.join(_DATA_DIR, "eval_dataset.jsonl")

with open(DATASET_CSV, newline="") as _src, open(DATASET_JSONL, "w") as _dst:
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
    data=DATASET_JSONL,
    evaluators=quality_evaluators,
    azure_ai_project=azure_ai_project,
)

evaluate(
    data=DATASET_JSONL,
    evaluators=safety_evaluators,
    azure_ai_project=azure_ai_project,
)

# The agent run needs an agent-trace dataset (with tool_calls / tool_definitions).
# Point AGENT_DATASET_JSONL at that dataset before enabling this run.
AGENT_DATASET_JSONL = os.path.join(_DATA_DIR, "agent_eval_dataset.jsonl")
if os.path.exists(AGENT_DATASET_JSONL):
    evaluate(
        data=AGENT_DATASET_JSONL,
        evaluators=agent_evaluators,
        azure_ai_project=azure_ai_project,
    )
