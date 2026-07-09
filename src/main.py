import csv
import json
import os

from azure.ai.evaluation import (
    CoherenceEvaluator,
    FluencyEvaluator,
    GroundednessEvaluator,
    RelevanceEvaluator,
    SimilarityEvaluator,
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

foundry_evaluators = {
    "groundedness": GroundednessEvaluator(evaluator_model_config),
    "relevance": RelevanceEvaluator(evaluator_model_config),
    "coherence": CoherenceEvaluator(evaluator_model_config),
    "fluency": FluencyEvaluator(evaluator_model_config),
    "similarity": SimilarityEvaluator(evaluator_model_config),
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

evaluate(
    data=DATASET_JSONL,
    evaluators=foundry_evaluators,
    azure_ai_project=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
)
