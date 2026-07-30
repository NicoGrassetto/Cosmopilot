# import csv
# import json
import os
# from typing import Any, cast

# from azure.ai.evaluation import (
#     BleuScoreEvaluator,
#     CodeVulnerabilityEvaluator,
#     CoherenceEvaluator,
#     ContentSafetyEvaluator,
#     DocumentRetrievalEvaluator,
#     F1ScoreEvaluator,
#     FluencyEvaluator,
#     GleuScoreEvaluator,
#     GroundednessEvaluator,
#     GroundednessProEvaluator,
#     HateUnfairnessEvaluator,
#     IndirectAttackEvaluator,
#     IntentResolutionEvaluator,
#     MeteorScoreEvaluator,
#     ProtectedMaterialEvaluator,
#     RelevanceEvaluator,
#     ResponseCompletenessEvaluator,
#     RetrievalEvaluator,
#     RougeScoreEvaluator,
#     RougeType,
#     SelfHarmEvaluator,
#     SexualEvaluator,
#     SimilarityEvaluator,
#     TaskAdherenceEvaluator,
#     ToolCallAccuracyEvaluator,
#     UngroundedAttributesEvaluator,
#     ViolenceEvaluator,
# )

# from azure.ai.evaluation import evaluate  # pyright: ignore
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FileDatasetVersion
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import TestingCriterionAzureAIEvaluator
# from openai.types.eval_create_params import (
#     DataSourceConfigCustom,
#     DataSourceConfigLogs,
#     TestingCriterionTextSimilarity,
# )

# PREFIX = "cosmopilot"

# DATASET_NAME = f"{PREFIX}-eval-dataset"
# # Dataset versions in Foundry are immutable, so CI overrides this per change
# # (e.g. with the commit SHA) to avoid version collisions on re-upload.
# DATASET_VERSION = os.environ.get("DATASET_VERSION", "1")

# custom_data_source_config: DataSourceConfigCustom = {
#     "type": "custom",
#     "item_schema": {
#         "type": "object",
#         "properties": {
#             "question": {"type": "string"},
#             "answer": {"type": "string"},
#         },
#         "required": ["question", "answer"],
#     },
#     "include_sample_schema": True,
# }

# logs_data_source_config: DataSourceConfigLogs = {
#     "type": "logs",
#     "metadata": {
#         "usecase": "cosmos-assistant",
#     },
# }
def upload_dataset(name: str, version: str, path: str) -> FileDatasetVersion:
    client = AIProjectClient(endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=DefaultAzureCredential())
    return client.datasets.upload_file(name=name, version=version, file_path=path)

def list_datasets() -> list[FileDatasetVersion]:
    client = AIProjectClient(endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=DefaultAzureCredential())
    return list(client.datasets.list())

def delete_dataset(name: str, version: str) -> None:
    client = AIProjectClient(endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=DefaultAzureCredential())
    client.datasets.delete(name=name, version=version)

def get_dataset(name: str, version: str) -> FileDatasetVersion:
    client = AIProjectClient(endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=DefaultAzureCredential())
    return client.datasets.get(name=name, version=version)

def register_eval(name: str, data_source_config: dict, testing_criteria: list):
    client = AIProjectClient(endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=DefaultAzureCredential())
    return client.get_openai_client().evals.create(name=name, data_source_config=data_source_config, testing_criteria=testing_criteria)

def list_evals():
    client = AIProjectClient(endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=DefaultAzureCredential())
    return list(client.get_openai_client().evals.list())

def delete_eval(eval_id: str):
    client = AIProjectClient(endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=DefaultAzureCredential())
    return client.get_openai_client().evals.delete(eval_id=eval_id)

def get_eval(eval_id: str):
    client = AIProjectClient(endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=DefaultAzureCredential())
    return client.get_openai_client().evals.retrieve(eval_id=eval_id)

# NOTE: The public OpenAI SDK type also lists "cosine", but the Azure Foundry
# eval service rejects it (400 UserError), so it's intentionally excluded here.
# TEXT_SIMILARITY_METRICS = [
#     "fuzzy_match",
#     "bleu",
#     "gleu",
#     "meteor",
#     "rouge_1",
#     "rouge_2",
#     "rouge_3",
#     "rouge_4",
#     "rouge_5",
#     "rouge_l",
# ]


# def run():
#     """Register the reusable evals and score the dataset with every evaluator.

#     Performs the full offline evaluation pass for Cosmopilot:

#     1. Registers four reusable, OpenAI-graded evals in the Foundry project
#        (``cosmopilot-relevant``, ``cosmopilot-text_similarity``,
#        ``cosmopilot-string_check``, and ``cosmopilot-score_model``).
#     2. Converts ``data/datasets/eval_dataset.csv`` into the JSONL layout expected
#        by ``azure.ai.evaluation.evaluate`` (``query``/``response``/
#        ``ground_truth``/``context`` fields).
#     3. Runs the built-in ``azure-ai-evaluation`` quality and safety evaluators over
#        that dataset, and -- only if ``data/datasets/agent_eval_dataset.jsonl``
#        exists -- the agent evaluators.
#     4. Uploads each evaluation run to the Foundry project under a friendly name
#        (``cosmopilot-quality``/``cosmopilot-safety``/``cosmopilot-agent``), writes a
#        local copy of the metrics and per-row scores to
#        ``data/datasets/eval_results/``, and prints the Foundry ``studio_url``
#        deep-link for each run.

#     The judge model and Foundry project are taken from the environment (see the
#     module docstring), and authentication uses ``DefaultAzureCredential``.

#     This function takes no arguments and returns ``None``; its effects are the
#     evals registered in Foundry, the generated JSONL file on disk, the local result
#     files under ``data/datasets/eval_results/``, and the named evaluation
#     runs/results reported to the project (whose portal links are printed to stdout).

#     Raises:
#         KeyError: If the ``AZURE_AI_PROJECT_ENDPOINT`` environment variable is not
#             set.
#         FileNotFoundError: If ``data/datasets/eval_dataset.csv`` is missing.
#         azure.core.exceptions.HttpResponseError: If registering an eval or running
#             an evaluator against the Foundry project fails (e.g. authentication,
#             quota, or an invalid judge-model deployment).

#     Example:
#         Score the dataset after signing in with ``az login``::

#             import os

#             os.environ["AZURE_AI_PROJECT_ENDPOINT"] = (
#                 "https://my-res.services.ai.azure.com/api/projects/my-proj"
#             )
#             os.environ["AZURE_DEPLOYMENT_NAME"] = "gpt-4o-mini"
#             run()

#         Or from the command line::

#             $ python src/evals.py run
#     """
#     endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
#     model = os.environ.get("AZURE_DEPLOYMENT_NAME", "gpt-4o-mini")
#     data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "datasets")

#     credential = DefaultAzureCredential()
#     client = AIProjectClient(endpoint=endpoint, credential=credential)
#     openai_client = client.get_openai_client()

#     # -----------------------------------------------------------------------
#     # Register (create) the reusable OpenAI-graded evals in the Foundry project.
#     # -----------------------------------------------------------------------
#     openai_client.evals.create(
#         name=f"{PREFIX}-relevant",
#         data_source_config=custom_data_source_config,
#         testing_criteria=[
#             {
#                 "type": "label_model",
#                 "name": "relevance-grader",
#                 "model": model,
#                 "input": [
#                     {
#                         "role": "developer",
#                         "content": (
#                             "Label whether the answer is relevant to the user's "
#                             "question about Azure Cosmos DB operations. "
#                             "Respond with 'relevant' or 'irrelevant'."
#                         ),
#                     },
#                     {
#                         "role": "user",
#                         "content": "Question: {{item.question}}\nAnswer: {{sample.output_text}}",
#                     },
#                 ],
#                 "labels": ["relevant", "irrelevant"],
#                 "passing_labels": ["relevant"],
#             }
#         ],
#     )

# openai_client.evals.create(
#     name=f"{PREFIX}-text_similarity",
#     data_source_config=custom_data_source_config,
#     testing_criteria=cast(
#         "list[TestingCriterionTextSimilarity]",
#         [
#             {
#                 "type": "text_similarity",
#                 "name": f"answer-similarity-{metric}",
#                 "input": "{{sample.output_text}}",
#                 "reference": "{{item.answer}}",
#                 "evaluation_metric": metric,
#                 "pass_threshold": 0.8,
#             }
#             for metric in TEXT_SIMILARITY_METRICS
#         ],
#     ),
# )

# openai_client.evals.create(
#     name=f"{PREFIX}-string_check",
#     data_source_config=custom_data_source_config,
#     testing_criteria=[
#         {
#             "type": "string_check",
#             "name": "answer-exact-match",
#             "input": "{{sample.output_text}}",
#             "reference": "{{item.answer}}",
#             "operation": "eq",
#         }
#     ],
# )

# openai_client.evals.create(
#     name=f"{PREFIX}-score_model",
#     data_source_config=custom_data_source_config,
#     testing_criteria=[
#         {
#             "type": "score_model",
#             "name": "answer-quality-scorer",
#             "model": model,
#             "input": [
#                 {
#                     "role": "developer",
#                     "content": (
#                         "Score how well the answer resolves the user's question "
#                         "about Azure Cosmos DB operations, from 0 (useless) to 1 "
#                         "(fully correct and complete). Respond with only the number."
#                     ),
#                 },
#                 {
#                     "role": "user",
#                     "content": "Question: {{item.question}}\nAnswer: {{sample.output_text}}",
#                 },
#             ],
#             "range": [0, 1],
#             "pass_threshold": 0.7,
#         }
#     ],
# )

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
# The AI-assisted evaluators reach the judge model through the Azure OpenAI
# data plane, which lives at the base AI Services endpoint. The
# ``/api/projects/<project>`` suffix on AZURE_AI_PROJECT_ENDPOINT is only for
# project-scoped services (e.g. Content Safety, below), so strip it here.
# judge_endpoint = endpoint.split("/api/projects/")[0]
# evaluator_model_config = {
#     "azure_endpoint": judge_endpoint,
#     "azure_deployment": model,
#     "api_version": os.environ.get("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
# }
# azure_ai_project = endpoint

# # Quality / textual-similarity / RAG. Fields: query, response, context, ground_truth.
# quality_evaluators: dict[str, Any] = {
#     # "coherence": CoherenceEvaluator(evaluator_model_config),
#     # "fluency": FluencyEvaluator(evaluator_model_config),
#     # "similarity": SimilarityEvaluator(evaluator_model_config),
#     # "f1_score": F1ScoreEvaluator(),
#     # "bleu": BleuScoreEvaluator(),
#     # "gleu": GleuScoreEvaluator(),
#     # "meteor": MeteorScoreEvaluator(),
#     # "rouge": RougeScoreEvaluator(RougeType.ROUGE_L),
#     "retrieval": RetrievalEvaluator(evaluator_model_config),
#     "groundedness": GroundednessEvaluator(evaluator_model_config),
#     # "groundedness_pro": GroundednessProEvaluator(credential, azure_ai_project),
#     # "relevance": RelevanceEvaluator(evaluator_model_config),
#     "response_completeness": ResponseCompletenessEvaluator(evaluator_model_config),
#     # DocumentRetrievalEvaluator needs a retrieval-specific dataset
#     # (retrieval_ground_truth + retrieved_documents), so run it separately.
#     "document_retrieval": DocumentRetrievalEvaluator(),
# }

# # Risk and safety. Fields: query, response (content is sent to Content Safety).
# safety_evaluators: dict[str, Any] = {
#     "content_safety": ContentSafetyEvaluator(credential, azure_ai_project),
#     "hate_unfairness": HateUnfairnessEvaluator(credential, azure_ai_project),
#     "sexual": SexualEvaluator(credential, azure_ai_project),
#     "violence": ViolenceEvaluator(credential, azure_ai_project),
#     "self_harm": SelfHarmEvaluator(credential, azure_ai_project),
#     "protected_material": ProtectedMaterialEvaluator(credential, azure_ai_project),
#     "indirect_attack": IndirectAttackEvaluator(credential, azure_ai_project),
#     "code_vulnerability": CodeVulnerabilityEvaluator(credential, azure_ai_project),
#     "ungrounded_attributes": UngroundedAttributesEvaluator(credential, azure_ai_project),
# }

# # Agent. Require agent traces: tool_calls + tool_definitions plus query/response.
# agent_evaluators: dict[str, Any] = {
#     "intent_resolution": IntentResolutionEvaluator(evaluator_model_config),
#     "task_adherence": TaskAdherenceEvaluator(evaluator_model_config),
#     "tool_call_accuracy": ToolCallAccuracyEvaluator(evaluator_model_config),
# }

# # evaluate() expects a JSONL file with query/response/context/ground_truth
# # fields, so convert the CSV dataset into that layout first.
# dataset_csv = os.path.join(data_dir, "eval_dataset.csv")
# dataset_jsonl = os.path.join(data_dir, "eval_dataset.jsonl")
# with open(dataset_csv, newline="") as _src, open(dataset_jsonl, "w") as _dst:
#     for _row in csv.DictReader(_src):
#         _dst.write(
#             json.dumps(
#                 {
#                     "query": _row["question"],
#                     "response": _row["answer"],
#                     "ground_truth": _row["answer"],
#                     # The dataset has no separate source context, so the
#                     # reference answer stands in as the grounding context.
#                     "context": _row["answer"],
#                 }
#             )
#             + "\n"
#         )

# Each run uses only evaluators compatible with the dataset it points at.
# All evaluators in a single evaluate() call must accept the same input fields.
# evaluate() uploads the run to the Foundry project and returns the aggregate
# metrics plus a ``studio_url`` deep-link. Capture both: name each run so it is
# findable in the portal, persist a local copy via ``output_path``, and print
# the links (they are otherwise auto-named with a GUID and easy to miss).
#     results_dir = os.path.join(data_dir, "eval_results")
#     os.makedirs(results_dir, exist_ok=True)
#     result_links: list[tuple[str, str]] = []

#     quality_result = cast(
#         "dict[str, Any]",
#         evaluate(
#             data=dataset_jsonl,
#             evaluators=quality_evaluators,
#             azure_ai_project=azure_ai_project,
#             evaluation_name=f"{PREFIX}-quality",
#             output_path=os.path.join(results_dir, "quality_results.json"),
#         ),
#     )
#     result_links.append(("quality", str(quality_result.get("studio_url") or "")))

#     safety_result = cast(
#         "dict[str, Any]",
#         evaluate(
#             data=dataset_jsonl,
#             evaluators=safety_evaluators,
#             azure_ai_project=azure_ai_project,
#             evaluation_name=f"{PREFIX}-safety",
#             output_path=os.path.join(results_dir, "safety_results.json"),
#         ),
#     )
#     result_links.append(("safety", str(safety_result.get("studio_url") or "")))

#     # The agent run needs an agent-trace dataset (with tool_calls / tool_definitions).
#     # Point agent_dataset_jsonl at that dataset before enabling this run.
#     agent_dataset_jsonl = os.path.join(data_dir, "agent_eval_dataset.jsonl")
#     if os.path.exists(agent_dataset_jsonl):
#         agent_result = cast(
#             "dict[str, Any]",
#             evaluate(
#                 data=agent_dataset_jsonl,
#                 evaluators=agent_evaluators,
#                 azure_ai_project=azure_ai_project,
#                 evaluation_name=f"{PREFIX}-agent",
#                 output_path=os.path.join(results_dir, "agent_results.json"),
#             ),
#         )
#         result_links.append(("agent", str(agent_result.get("studio_url") or "")))

#     print("\n" + "=" * 72)
#     print("Evaluation complete. Open the results in Azure AI Foundry:")
#     for label, url in result_links:
#         print(f"  {label:<8} {url or '(no studio_url returned)'}")
#     print(f"\nLocal result files (metrics + per-row scores): {results_dir}")
#     print("=" * 72)


#
#     """Upload the question/answer eval dataset to the Foundry project.

#     Converts ``data/datasets/eval_dataset.csv`` into the JSONL layout used by the
#     evaluators (one JSON object per row with ``query``, ``response``,
#     ``ground_truth``, and ``context`` fields) and registers it as a versioned
#     dataset in the Azure AI Foundry project named by ``AZURE_AI_PROJECT_ENDPOINT``.

#     Foundry dataset versions are immutable: uploading the same ``name``/``version``
#     twice fails, so pass a fresh ``version`` (CI usually uses the commit SHA).

#     Args:
#         name: Name to register the dataset under in Foundry. Defaults to
#             ``DATASET_NAME`` (``"cosmopilot-eval-dataset"``).
#         version: Immutable version label for this upload. Defaults to
#             ``DATASET_VERSION`` (the ``DATASET_VERSION`` environment variable, or
#             ``"1"`` if unset).

#     Returns:
#         FileDatasetVersion: The registered dataset version. Its ``id`` attribute is
#         the fully-qualified dataset reference that evals and runs point at.

#     Raises:
#         KeyError: If the ``AZURE_AI_PROJECT_ENDPOINT`` environment variable is not
#             set.
#         FileNotFoundError: If ``data/datasets/eval_dataset.csv`` is missing.
#         azure.core.exceptions.HttpResponseError: If the upload fails, including when
#             ``name``/``version`` already exists (versions are immutable).

#     Example:
#         Upload a new version and read back its id::

#             import os

#             os.environ["AZURE_AI_PROJECT_ENDPOINT"] = (
#                 "https://my-res.services.ai.azure.com/api/projects/my-proj"
#             )
#             dataset = upload_dataset(version="42")
#             print(dataset.id)

#         Or from the command line (uses ``DATASET_VERSION``)::

#             $ DATASET_VERSION=42 python src/evals.py upload
#     """
#     endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
#     data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "datasets")

#     credential = DefaultAzureCredential()
#     client = AIProjectClient(endpoint=endpoint, credential=credential)

#     dataset_csv = os.path.join(data_dir, "eval_dataset.csv")
#     dataset_jsonl = os.path.join(data_dir, "eval_dataset.jsonl")
#     with open(dataset_csv, newline="") as _src, open(dataset_jsonl, "w") as _dst:
#         for _row in csv.DictReader(_src):
#             _dst.write(
#                 json.dumps(
#                     {
#                         "query": _row["question"],
#                         "response": _row["answer"],
#                         "ground_truth": _row["answer"],
#                         "context": _row["answer"],
#                     }
#                 )
#                 + "\n"
#             )

#     dataset = client.datasets.upload_file(
#         name=name,
#         version=version,
#         file_path=dataset_jsonl,
#     )
#     print(f"Uploaded dataset {name}:{version} -> {dataset.id}")
#     return dataset
