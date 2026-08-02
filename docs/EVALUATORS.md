# Azure Evaluation Reference

This reference distinguishes two APIs that expose many of the same metrics:

- **Foundry cloud evaluators** are identified by `builtin.*` catalog IDs and are passed to `openai_client.evals.create(..., testing_criteria=[...])` through `TestingCriterionAzureAIEvaluator`.
- **Local SDK evaluators** are Python classes from `azure.ai.evaluation` and are passed to `evaluate(..., evaluators={...})`.

"Local" describes orchestration. Model-assisted and safety evaluators can still call Azure services.

## Lifecycle status

Statuses in this reference reflect Microsoft documentation available on August 1, 2026:

- **GA**: generally available and not marked preview or experimental in the current product documentation.
- **Preview**: public preview; no service-level agreement and not recommended for production-critical gating without a fallback.
- **Experimental**: a Python SDK API that can change or be removed without the compatibility guarantees of a stable API. A cloud evaluator can be GA while its local SDK wrapper remains experimental.
- **Deprecated**: retained for compatibility but scheduled for removal. No current evaluator catalog entry is documented as deprecated; the known deprecations are legacy local result keys described below.

The repository declares minimum package versions, not locked versions. The active Python environment used for this audit does not have the Azure evaluation packages installed, so public SDK coverage below is based on the current Microsoft Python API reference rather than runtime introspection.

### Cloud catalog status

| Category | GA | Preview |
| --- | --- | --- |
| General purpose | `builtin.coherence`, `builtin.fluency` | None |
| Textual similarity | `builtin.similarity`, `builtin.f1_score`, `builtin.bleu_score`, `builtin.gleu_score`, `builtin.rouge_score`, `builtin.meteor_score` | None |
| RAG | `builtin.retrieval`, `builtin.document_retrieval`, `builtin.groundedness`, `builtin.relevance` | `builtin.groundedness_pro`, `builtin.response_completeness` |
| Risk and safety | `builtin.hate_unfairness`, `builtin.sexual`, `builtin.violence`, `builtin.self_harm`, `builtin.protected_material`, `builtin.indirect_attack`, `builtin.code_vulnerability`, `builtin.ungrounded_attributes` | `builtin.prohibited_actions`, `builtin.sensitive_data_leakage` |
| Agent | `builtin.task_navigation_efficiency`, `builtin.tool_call_accuracy`, `builtin.tool_selection`, `builtin.tool_input_accuracy`, `builtin.tool_output_utilization`, `builtin.tool_call_success` | `builtin.task_adherence`, `builtin.task_completion`, `builtin.customer_satisfaction`, `builtin.intent_resolution`, `builtin.quality_grader` |
| Configurable | Azure OpenAI graders | Rubric evaluators and custom code-, prompt-, and endpoint-based evaluators |

Evaluation level is separate from evaluator lifecycle status. Conversation-level cloud evaluation is Preview even when it uses a GA evaluator such as Coherence or Groundedness.

## Foundry cloud evaluation

### Shared create and run pattern

Use this scaffold with any cloud criterion shown below:

```python
import os

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from openai.types.eval_create_params import DataSourceConfigCustom

client = AIProjectClient(
    endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential(),
).get_openai_client()

model = os.environ["AZURE_DEPLOYMENT_NAME"]

data_source_config = DataSourceConfigCustom(
    type="custom",
    item_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "response": {"type": "string"},
            "context": {"type": "string"},
            "ground_truth": {"type": "string"},
        },
        "required": ["query", "response"],
    },
    include_sample_schema=True,
)

eval_object = client.evals.create(
    name="cosmopilot-response-quality",
    data_source_config=data_source_config,
    testing_criteria=testing_criteria,
)

eval_run = client.evals.runs.create(
    eval_id=eval_object.id,
    name="cosmopilot-response-quality-run",
    data_source={
        "type": "jsonl",
        "source": {"type": "file_id", "id": dataset_id},
    },
)
```

For a model or agent target that generates the response during the run, map its text with `{{sample.output_text}}`. For precomputed dataset responses, use `{{item.response}}`. Agent evaluators that inspect tool calls generally use `{{sample.output_items}}`.

### General-purpose evaluators (GA)

#### Coherence

Measures logical consistency, organization, and flow. Requires `query`, `response`, and a judge model.

```python
testing_criteria = [{
    "type": "azure_ai_evaluator",
    "name": "coherence",
    "evaluator_name": "builtin.coherence",
    "initialization_parameters": {"deployment_name": model},
    "data_mapping": {"query": "{{item.query}}", "response": "{{item.response}}"},
}]
```

#### Fluency

Measures grammar, readability, vocabulary, and natural language quality. Requires `response` and a judge model.

```python
testing_criteria = [{
    "type": "azure_ai_evaluator",
    "name": "fluency",
    "evaluator_name": "builtin.fluency",
    "initialization_parameters": {"deployment_name": model},
    "data_mapping": {"response": "{{item.response}}"},
}]
```

### Textual-similarity evaluators (GA)

#### Similarity

Measures semantic similarity between a response and ground truth using an LLM judge.

```python
testing_criteria = [{
    "type": "azure_ai_evaluator", "name": "similarity",
    "evaluator_name": "builtin.similarity",
    "initialization_parameters": {"deployment_name": model},
    "data_mapping": {
        "query": "{{item.query}}", "response": "{{item.response}}",
        "ground_truth": "{{item.ground_truth}}",
    },
}]
```

#### F1 score

Measures token overlap by combining precision and recall. It is deterministic and needs no judge model.

```python
testing_criteria = [{
    "type": "azure_ai_evaluator", "name": "f1_score",
    "evaluator_name": "builtin.f1_score",
    "data_mapping": {"response": "{{item.response}}", "ground_truth": "{{item.ground_truth}}"},
}]
```

#### BLEU score

Measures n-gram overlap, commonly for translation and summarization.

```python
testing_criteria = [{
    "type": "azure_ai_evaluator", "name": "bleu_score",
    "evaluator_name": "builtin.bleu_score",
    "data_mapping": {"response": "{{item.response}}", "ground_truth": "{{item.ground_truth}}"},
}]
```

#### GLEU score

Measures sentence-level n-gram overlap with balanced precision and recall.

```python
testing_criteria = [{
    "type": "azure_ai_evaluator", "name": "gleu_score",
    "evaluator_name": "builtin.gleu_score",
    "data_mapping": {"response": "{{item.response}}", "ground_truth": "{{item.ground_truth}}"},
}]
```

#### ROUGE score

Measures recall-oriented n-gram overlap. It returns precision, recall, and F1 metrics.

```python
testing_criteria = [{
    "type": "azure_ai_evaluator", "name": "rouge_score",
    "evaluator_name": "builtin.rouge_score",
    "initialization_parameters": {"rouge_type": "rougeL"},
    "data_mapping": {"response": "{{item.response}}", "ground_truth": "{{item.ground_truth}}"},
}]
```

#### METEOR score

Measures token alignment while accounting for stemming, synonyms, and paraphrases.

```python
testing_criteria = [{
    "type": "azure_ai_evaluator", "name": "meteor_score",
    "evaluator_name": "builtin.meteor_score",
    "data_mapping": {"response": "{{item.response}}", "ground_truth": "{{item.ground_truth}}"},
}]
```

### RAG evaluators

#### Retrieval

Uses an LLM judge to measure whether retrieved context is relevant to the query.

```python
testing_criteria = [{
    "type": "azure_ai_evaluator", "name": "retrieval",
    "evaluator_name": "builtin.retrieval",
    "initialization_parameters": {"deployment_name": model},
    "data_mapping": {"query": "{{item.query}}", "context": "{{item.context}}"},
}]
```

#### Document retrieval

Compares ranked retrieved documents with human relevance labels and reports metrics such as NDCG, fidelity, and holes.

```python
testing_criteria = [{
    "type": "azure_ai_evaluator", "name": "document_retrieval",
    "evaluator_name": "builtin.document_retrieval",
    "initialization_parameters": {"ground_truth_label_min": 0, "ground_truth_label_max": 4},
    "data_mapping": {
        "retrieval_ground_truth": "{{item.retrieval_ground_truth}}",
        "retrieved_documents": "{{item.retrieved_documents}}",
    },
}]
```

#### Groundedness

Uses an LLM judge to measure whether response claims are supported by context.

```python
testing_criteria = [{
    "type": "azure_ai_evaluator", "name": "groundedness",
    "evaluator_name": "builtin.groundedness",
    "initialization_parameters": {"deployment_name": model},
    "data_mapping": {
        "query": "{{item.query}}", "response": "{{item.response}}",
        "context": "{{item.context}}",
    },
}]
```

#### Groundedness Pro (preview)

Uses the hosted Azure safety service for a strict binary groundedness result and does not require a judge deployment.

```python
testing_criteria = [{
    "type": "azure_ai_evaluator", "name": "groundedness_pro",
    "evaluator_name": "builtin.groundedness_pro",
    "data_mapping": {
        "query": "{{item.query}}", "response": "{{item.response}}",
        "context": "{{item.context}}",
    },
}]
```

#### Relevance

Uses an LLM judge to measure whether a response directly and completely addresses the query.

```python
testing_criteria = [{
    "type": "azure_ai_evaluator", "name": "relevance",
    "evaluator_name": "builtin.relevance",
    "initialization_parameters": {"deployment_name": model},
    "data_mapping": {"query": "{{item.query}}", "response": "{{item.response}}"},
}]
```

#### Response completeness (preview)

Measures whether the response covers the critical information in the ground truth.

```python
testing_criteria = [{
    "type": "azure_ai_evaluator", "name": "response_completeness",
    "evaluator_name": "builtin.response_completeness",
    "initialization_parameters": {"deployment_name": model},
    "data_mapping": {"response": "{{item.response}}", "ground_truth": "{{item.ground_truth}}"},
}]
```

### Risk and safety evaluators

These are hosted evaluators. The basic content-risk evaluators do not require your own judge deployment.

#### Hate and unfairness

Detects hateful, biased, discriminatory, or unfair content.

```python
testing_criteria = [{"type": "azure_ai_evaluator", "name": "hate_unfairness", "evaluator_name": "builtin.hate_unfairness", "data_mapping": {"query": "{{item.query}}", "response": "{{item.response}}"}}]
```

#### Sexual

Detects sexual or explicit content and reports risk severity.

```python
testing_criteria = [{"type": "azure_ai_evaluator", "name": "sexual", "evaluator_name": "builtin.sexual", "data_mapping": {"query": "{{item.query}}", "response": "{{item.response}}"}}]
```

#### Violence

Detects violent or threatening content and reports risk severity.

```python
testing_criteria = [{"type": "azure_ai_evaluator", "name": "violence", "evaluator_name": "builtin.violence", "data_mapping": {"query": "{{item.query}}", "response": "{{item.response}}"}}]
```

#### Self-harm

Detects content related to self-harm and reports risk severity.

```python
testing_criteria = [{"type": "azure_ai_evaluator", "name": "self_harm", "evaluator_name": "builtin.self_harm", "data_mapping": {"query": "{{item.query}}", "response": "{{item.response}}"}}]
```

#### Protected material

Detects potentially copyrighted or protected text.

```python
testing_criteria = [{"type": "azure_ai_evaluator", "name": "protected_material", "evaluator_name": "builtin.protected_material", "data_mapping": {"query": "{{item.query}}", "response": "{{item.response}}"}}]
```

#### Indirect attack

Detects whether injected instructions in retrieved content manipulated the response.

```python
testing_criteria = [{"type": "azure_ai_evaluator", "name": "indirect_attack", "evaluator_name": "builtin.indirect_attack", "data_mapping": {"query": "{{item.query}}", "response": "{{item.response}}"}}]
```

#### Code vulnerability

Detects common security vulnerabilities in generated code.

```python
testing_criteria = [{"type": "azure_ai_evaluator", "name": "code_vulnerability", "evaluator_name": "builtin.code_vulnerability", "data_mapping": {"query": "{{item.query}}", "response": "{{item.response}}"}}]
```

#### Ungrounded attributes

Detects unsupported inferences about protected classes or emotional states. Requires context.

```python
testing_criteria = [{"type": "azure_ai_evaluator", "name": "ungrounded_attributes", "evaluator_name": "builtin.ungrounded_attributes", "data_mapping": {"query": "{{item.query}}", "response": "{{item.response}}", "context": "{{item.context}}"}}]
```

#### Prohibited actions (preview)

Detects agent behaviors that violate explicitly prohibited actions. It is agent-only and requires tool calls.

```python
testing_criteria = [{"type": "azure_ai_evaluator", "name": "prohibited_actions", "evaluator_name": "builtin.prohibited_actions", "data_mapping": {"query": "{{item.query}}", "response": "{{sample.output_items}}", "tool_calls": "{{sample.tool_calls}}"}}]
```

#### Sensitive data leakage (preview)

Detects whether an agent exposes sensitive information. It is agent-only and requires tool calls.

```python
testing_criteria = [{"type": "azure_ai_evaluator", "name": "sensitive_data_leakage", "evaluator_name": "builtin.sensitive_data_leakage", "data_mapping": {"query": "{{item.query}}", "response": "{{sample.output_items}}", "tool_calls": "{{sample.tool_calls}}"}}]
```

### Agent evaluators

Agent evaluators generally require OpenAI-style agent messages and, for tool metrics, `tool_definitions`.

Tool-aware evaluators currently support File Search, user-defined Function tools, MCP, and knowledge-based MCP. Avoid `tool_call_accuracy`, `tool_input_accuracy`, `tool_output_utilization`, `tool_call_success`, and agent-mode Groundedness when interactions contain Azure AI Search, Bing Grounding, Bing Custom Search, SharePoint Grounding, Code Interpreter, Fabric Data Agent, or Web Search; current documentation marks those tools as having limited evaluator support.

#### Task adherence (preview)

Checks whether the agent obeyed its instructions, rules, constraints, and required procedure.

```python
testing_criteria = [{"type": "azure_ai_evaluator", "name": "task_adherence", "evaluator_name": "builtin.task_adherence", "initialization_parameters": {"deployment_name": model}, "data_mapping": {"query": "{{item.query}}", "response": "{{sample.output_items}}"}}]
```

#### Task completion (preview)

Checks whether the agent completed the requested task end to end.

```python
testing_criteria = [{"type": "azure_ai_evaluator", "name": "task_completion", "evaluator_name": "builtin.task_completion", "initialization_parameters": {"deployment_name": model}, "data_mapping": {"query": "{{item.query}}", "response": "{{sample.output_items}}", "tool_definitions": "{{item.tool_definitions}}"}}]
```

#### Customer satisfaction (preview)

Scores complete conversations for likely user satisfaction across helpfulness, completeness, clarity, tone, resolution, and adaptability.

```python
testing_criteria = [{"type": "azure_ai_evaluator", "name": "customer_satisfaction", "evaluator_name": "builtin.customer_satisfaction", "initialization_parameters": {"model": model}, "data_mapping": {"messages": "{{item.messages}}"}}]
```

Run this criterion with conversation-level evaluation:

```python
client.evals.runs.create(
    eval_id=eval_object.id,
    name="customer-satisfaction-run",
    data_source=data_source,
    extra_body={"evaluation_level": "conversation"},
)
```

#### Intent resolution (preview)

Measures whether the agent identified and addressed the user's intent.

```python
testing_criteria = [{"type": "azure_ai_evaluator", "name": "intent_resolution", "evaluator_name": "builtin.intent_resolution", "initialization_parameters": {"deployment_name": model}, "data_mapping": {"query": "{{item.query}}", "response": "{{sample.output_items}}"}}]
```

#### Task navigation efficiency

Compares actual agent actions with an expected action sequence.

```python
testing_criteria = [{"type": "azure_ai_evaluator", "name": "task_navigation_efficiency", "evaluator_name": "builtin.task_navigation_efficiency", "initialization_parameters": {"matching_mode": "in_order_match"}, "data_mapping": {"actions": "{{item.actions}}", "expected_actions": "{{item.expected_actions}}"}}]
```

#### Tool call accuracy

Scores overall tool choice, argument correctness, relevance, and efficiency.

```python
testing_criteria = [{"type": "azure_ai_evaluator", "name": "tool_call_accuracy", "evaluator_name": "builtin.tool_call_accuracy", "initialization_parameters": {"deployment_name": model}, "data_mapping": {"query": "{{item.query}}", "response": "{{sample.output_items}}", "tool_definitions": "{{item.tool_definitions}}"}}]
```

#### Tool selection

Checks whether the agent selected the correct and necessary tools without redundant choices.

```python
testing_criteria = [{"type": "azure_ai_evaluator", "name": "tool_selection", "evaluator_name": "builtin.tool_selection", "initialization_parameters": {"deployment_name": model}, "data_mapping": {"query": "{{item.query}}", "response": "{{sample.output_items}}", "tool_definitions": "{{item.tool_definitions}}"}}]
```

#### Tool input accuracy

Strictly validates tool argument grounding, types, format, completeness, and appropriateness.

```python
testing_criteria = [{"type": "azure_ai_evaluator", "name": "tool_input_accuracy", "evaluator_name": "builtin.tool_input_accuracy", "initialization_parameters": {"deployment_name": model}, "data_mapping": {"query": "{{item.query}}", "response": "{{sample.output_items}}", "tool_definitions": "{{item.tool_definitions}}"}}]
```

#### Tool output utilization

Checks whether the agent interpreted and used tool results correctly.

```python
testing_criteria = [{"type": "azure_ai_evaluator", "name": "tool_output_utilization", "evaluator_name": "builtin.tool_output_utilization", "initialization_parameters": {"deployment_name": model}, "data_mapping": {"query": "{{item.query}}", "response": "{{sample.output_items}}", "tool_definitions": "{{item.tool_definitions}}"}}]
```

#### Tool call success

Checks whether tool executions completed without technical failures.

```python
testing_criteria = [{"type": "azure_ai_evaluator", "name": "tool_call_success", "evaluator_name": "builtin.tool_call_success", "initialization_parameters": {"deployment_name": model}, "data_mapping": {"response": "{{sample.output_items}}"}}]
```

#### Quality grader (preview)

Combines relevance, abstention, and answer completeness, plus groundedness and context coverage when context is supplied.

```python
testing_criteria = [{"type": "azure_ai_evaluator", "name": "quality_grader", "evaluator_name": "builtin.quality_grader", "initialization_parameters": {"deployment_name": model}, "data_mapping": {"query": "{{item.query}}", "response": "{{item.response}}", "context": "{{item.context}}"}}]
```

### Cloud Azure OpenAI graders (GA)

These are testing-criterion types, not `builtin.*` catalog IDs. They can be mixed with Foundry criteria in the same `testing_criteria` list.

#### Label model

Uses an LLM to classify content into predefined labels.

```python
label_criterion = {
    "type": "label_model", "name": "relevance_label", "model": model,
    "input": [
        {"role": "developer", "content": "Return relevant or irrelevant."},
        {"role": "user", "content": "Query: {{item.query}}\nResponse: {{item.response}}"},
    ],
    "labels": ["relevant", "irrelevant"], "passing_labels": ["relevant"],
}
```

#### Score model

Uses an LLM and a custom prompt to assign a numeric score.

```python
score_criterion = {
    "type": "score_model", "name": "quality_score", "model": model,
    "input": [
        {"role": "developer", "content": "Score quality from 0 to 1. Return only the number."},
        {"role": "user", "content": "Response: {{item.response}}\nReference: {{item.ground_truth}}"},
    ],
    "range": [0, 1], "pass_threshold": 0.7,
}
```

#### String check

Performs deterministic exact or pattern comparisons with `eq`, `ne`, `like`, or `ilike`.

```python
string_criterion = {
    "type": "string_check", "name": "exact_match",
    "input": "{{item.response}}", "reference": "{{item.ground_truth}}",
    "operation": "eq",
}
```

#### Text similarity

Performs deterministic text comparison. Supported `evaluation_metric` values are:

```python
TEXT_SIMILARITY_METRICS = [
    "fuzzy_match",
    "bleu",
    "gleu",
    "meteor",
    "cosine",
    "rouge_1",
    "rouge_2",
    "rouge_3",
    "rouge_4",
    "rouge_5",
    "rouge_l",
]
```

```python
similarity_criterion = {
    "type": "text_similarity", "name": "answer_similarity",
    "input": "{{item.response}}", "reference": "{{item.ground_truth}}",
    "evaluation_metric": "bleu", "pass_threshold": 0.8,
}
```

A mixed cloud evaluation is simply:

```python
testing_criteria = [
    label_criterion,
    {
        "type": "azure_ai_evaluator", "name": "coherence",
        "evaluator_name": "builtin.coherence",
        "initialization_parameters": {"deployment_name": model},
        "data_mapping": {"query": "{{item.query}}", "response": "{{item.response}}"},
    },
]
```

### Rubric evaluators (Preview)

A rubric evaluator scores a response or conversation against weighted dimensions using an LLM judge. It returns per-dimension 1-5 scores and a weighted overall score normalized to 0-1. Rubrics can be generated from an agent, system prompt, reference files, and optional traces, or authored manually.

Rubric evaluators are versioned project assets. Current SDK samples generate or register the rubric and then use its project evaluator name; do not assume a universal `builtin.rubric` ID.

```python
criterion = {
    "type": "azure_ai_evaluator",
    "name": "reservation_quality",
    "evaluator_name": "reservation-quality-rubric",
    "evaluator_version": "1",
    "initialization_parameters": {"deployment_name": model},
    "data_mapping": {"query": "{{item.query}}", "response": "{{item.response}}"},
}
```

### Custom evaluators (Preview)

Custom evaluators are versioned project assets registered through `project_client.beta.evaluators.create_version(...)`. Their `evaluator_name` is the project evaluator name, not a `builtin.*` ID.

#### Code-based custom evaluator

Use deterministic Python logic for format, policy, length, keyword, or schema checks. The sandbox has no network access; code is limited to 256 KB, two minutes, 2 GB memory, 1 GB disk, and two CPU cores. The required function returns a float from 0.0 to 1.0:

```python
def grade(sample: dict, item: dict) -> float:
    response = item.get("response", "")
    return float("source:" in response.lower())
```

Register the function source with `EvaluatorDefinitionType.CODE`, plus its initialization schema, data schema, and continuous 0-1 metric. At run time, code-based evaluators currently require both `deployment_name` and `pass_threshold`, even though the grading code does not call a model.

#### Prompt-based custom evaluator

Use an LLM judge for subjective domain criteria. Register a prompt with `EvaluatorDefinitionType.PROMPT`, a data schema, and one of these metric types:

- `ordinal`: integer score in a configured range.
- `continuous`: float score in a configured range.
- `binary`: boolean result.

The prompt must return JSON containing `result` and `reason`. Runs require `deployment_name` and `threshold` initialization parameters.

#### Endpoint-based custom evaluator

Use an external HTTP endpoint when grading needs network access, proprietary models, databases, or dependencies unavailable in the sandbox. Register an evaluator definition with `type: "endpoint"` and `connection_name` through `project_client.beta.evaluators.create_version(...)`. The connection supports API-key or Microsoft Entra ID authentication. The endpoint receives mapped `item` and optional `sample` data and returns the standard result schema with `score`, `reason`, `status`, optional `properties`, `threshold`, and `passed`. It must respond within 30 seconds.

```python
criterion = {
    "type": "azure_ai_evaluator",
    "name": "domain_policy",
    "evaluator_name": "domain-policy-evaluator",
    "evaluator_version": "1",
    "initialization_parameters": {
        "deployment_name": model,
        "pass_threshold": 0.8,
    },
    "data_mapping": {
        "query": "{{item.query}}",
        "response": "{{item.response}}",
    },
}
```

Custom evaluators can also run at conversation level by accepting `item["messages"]` and creating the evaluation run with `extra_body={"evaluation_level": "conversation"}`. Conversation-level evaluation is itself Preview.

## Local SDK evaluation

### Local SDK status

The status below describes the public `azure.ai.evaluation` Python API, not the status of an equivalent cloud evaluator:

| Status | Public classes |
| --- | --- |
| GA | `CoherenceEvaluator`, `FluencyEvaluator`, `GroundednessEvaluator`, `RelevanceEvaluator`, `RetrievalEvaluator`, `SimilarityEvaluator`, `DocumentRetrievalEvaluator`, `QAEvaluator`, `BleuScoreEvaluator`, `F1ScoreEvaluator`, `GleuScoreEvaluator`, `MeteorScoreEvaluator`, `RougeScoreEvaluator` |
| Experimental | `GroundednessProEvaluator`, `ResponseCompletenessEvaluator`, `ContentSafetyEvaluator`, `HateUnfairnessEvaluator`, `SelfHarmEvaluator`, `SexualEvaluator`, `ViolenceEvaluator`, `ProtectedMaterialEvaluator`, `IndirectAttackEvaluator`, `CodeVulnerabilityEvaluator`, `UngroundedAttributesEvaluator`, `IntentResolutionEvaluator`, `TaskAdherenceEvaluator`, `ToolCallAccuracyEvaluator`, and all `AzureOpenAI*Grader` wrappers |
| Private, unsupported | `_ToolCallSuccessEvaluator`, `_ToolOutputUtilizationEvaluator`; leading-underscore symbols are not public API |
| Deprecated | None of the current public evaluator classes is documented as deprecated |

Experimental local wrappers can correspond to GA cloud evaluators. For example, `builtin.violence` is GA in Foundry cloud evaluation while `ViolenceEvaluator` is marked experimental in the Python API reference.

Install and import from `azure.ai.evaluation`. The shared pattern is:

```python
import os

from azure.ai.evaluation import CoherenceEvaluator, evaluate

model_config = {
    "azure_endpoint": os.environ["AZURE_OPENAI_ENDPOINT"],
    "azure_deployment": os.environ["AZURE_DEPLOYMENT_NAME"],
    "api_version": os.environ.get("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
}

evaluators = {
    "coherence": CoherenceEvaluator(model_config),
}

result = evaluate(
    data="data/datasets/eval_dataset.jsonl",
    evaluators=evaluators,
    evaluation_name="cosmopilot-local-quality",
    azure_ai_project=os.environ.get("AZURE_AI_PROJECT_ENDPOINT"),
)
```

The dictionary key is your result alias. Add any compatible evaluator below to that dictionary. Evaluators in one call must be compatible with the dataset fields or be configured with `evaluator_config` column mappings.

### Local callable custom evaluators (GA orchestration)

`evaluate()` accepts any synchronous or asynchronous callable as an evaluator. The callable's named parameters define the inputs that column mapping must supply, and it returns a dictionary of metric names and values.

```python
def citation_required(response: str) -> dict[str, float]:
    return {"citation_required": float("source:" in response.lower())}

result = evaluate(
    data="data/datasets/eval_dataset.jsonl",
    evaluators={"citation_required": citation_required},
    evaluator_config={
        "citation_required": {
            "column_mapping": {"response": "${data.response}"},
        },
    },
    output_path="data/datasets/eval_results/citation-check.json",
)
```

This logic runs under local orchestration and does not become a reusable evaluator-catalog asset. Use a cloud custom evaluator when the logic must be versioned, reused by managed or continuous evaluation, and surfaced as a Foundry catalog entry.

### Local quality and RAG evaluators

#### `CoherenceEvaluator`

Measures logical consistency and flow from `query` and `response`.

```python
"coherence": CoherenceEvaluator(model_config)
```

#### `FluencyEvaluator`

Measures grammar and readability from `response`.

```python
"fluency": FluencyEvaluator(model_config)
```

#### `GroundednessEvaluator`

Measures whether `response` is supported by `context`; `query` improves scoring.

```python
"groundedness": GroundednessEvaluator(model_config)
```

#### `GroundednessProEvaluator`

Uses the hosted evaluation service for strict binary groundedness.

```python
"groundedness_pro": GroundednessProEvaluator(DefaultAzureCredential(), project_endpoint)
```

#### `RelevanceEvaluator`

Measures whether `response` addresses `query`.

```python
"relevance": RelevanceEvaluator(model_config)
```

#### `RetrievalEvaluator`

Measures whether `context` is relevant to `query`.

```python
"retrieval": RetrievalEvaluator(model_config)
```

#### `SimilarityEvaluator`

Measures semantic similarity between `response` and `ground_truth` for a `query`.

```python
"similarity": SimilarityEvaluator(model_config)
```

#### `ResponseCompletenessEvaluator`

Measures whether `response` contains the critical information in `ground_truth`.

```python
"response_completeness": ResponseCompletenessEvaluator(model_config)
```

#### `DocumentRetrievalEvaluator`

Compares `retrieved_documents` with labeled `retrieval_ground_truth`.

```python
"document_retrieval": DocumentRetrievalEvaluator()
```

#### `QAEvaluator`

Composite question-answer evaluator that runs a standard set of QA quality metrics.

```python
"qa": QAEvaluator(model_config)
```

### Local textual-similarity evaluators

#### `BleuScoreEvaluator`

Computes BLEU n-gram overlap between `response` and `ground_truth`.

```python
"bleu": BleuScoreEvaluator()
```

#### `F1ScoreEvaluator`

Computes token-overlap precision/recall F1 between `response` and `ground_truth`.

```python
"f1_score": F1ScoreEvaluator()
```

#### `GleuScoreEvaluator`

Computes sentence-level GLEU overlap between `response` and `ground_truth`.

```python
"gleu": GleuScoreEvaluator()
```

#### `MeteorScoreEvaluator`

Computes METEOR alignment between `response` and `ground_truth`.

```python
"meteor": MeteorScoreEvaluator()
```

#### `RougeScoreEvaluator`

Computes the configured ROUGE variant between `response` and `ground_truth`.

```python
from azure.ai.evaluation import RougeScoreEvaluator, RougeType

"rouge": RougeScoreEvaluator(RougeType.ROUGE_L)
```

`RougeType` is an enum, not an evaluator.

### Local risk and safety evaluators

These use a Foundry project endpoint and credential. `ContentSafetyEvaluator` aggregates the four basic content-risk categories.

#### `ContentSafetyEvaluator`

Runs the core hate/unfairness, sexual, violence, and self-harm checks.

```python
"content_safety": ContentSafetyEvaluator(DefaultAzureCredential(), project_endpoint)
```

#### `HateUnfairnessEvaluator`

Detects hateful, discriminatory, biased, or unfair content.

```python
"hate_unfairness": HateUnfairnessEvaluator(DefaultAzureCredential(), project_endpoint)
```

#### `SelfHarmEvaluator`

Detects self-harm-related content.

```python
"self_harm": SelfHarmEvaluator(DefaultAzureCredential(), project_endpoint)
```

#### `SexualEvaluator`

Detects sexual or explicit content.

```python
"sexual": SexualEvaluator(DefaultAzureCredential(), project_endpoint)
```

#### `ViolenceEvaluator`

Detects violent or threatening content.

```python
"violence": ViolenceEvaluator(DefaultAzureCredential(), project_endpoint)
```

#### `ProtectedMaterialEvaluator`

Detects potentially copyrighted or protected text.

```python
"protected_material": ProtectedMaterialEvaluator(DefaultAzureCredential(), project_endpoint)
```

#### `IndirectAttackEvaluator`

Detects cross-domain prompt injection and indirect jailbreak behavior.

```python
"indirect_attack": IndirectAttackEvaluator(DefaultAzureCredential(), project_endpoint)
```

#### `CodeVulnerabilityEvaluator`

Detects common vulnerabilities in generated code.

```python
"code_vulnerability": CodeVulnerabilityEvaluator(DefaultAzureCredential(), project_endpoint)
```

#### `UngroundedAttributesEvaluator`

Detects unsupported personal-attribute inferences using `query`, `response`, and `context`.

```python
"ungrounded_attributes": UngroundedAttributesEvaluator(DefaultAzureCredential(), project_endpoint)
```

### Local agent evaluators

These expect simple query/response pairs or OpenAI-style agent messages. Tool evaluation also needs tool definitions.

#### `IntentResolutionEvaluator`

Measures whether the agent identified and resolved the user's intent.

```python
"intent_resolution": IntentResolutionEvaluator(model_config)
```

#### `TaskAdherenceEvaluator`

Checks whether agent actions follow system instructions, rules, and procedure.

```python
"task_adherence": TaskAdherenceEvaluator(model_config)
```

#### `ToolCallAccuracyEvaluator`

Scores tool selection, relevance, arguments, and execution efficiency.

```python
"tool_call_accuracy": ToolCallAccuracyEvaluator(model_config)
```

The package currently exports `_ToolCallSuccessEvaluator` and `_ToolOutputUtilizationEvaluator`, but their leading underscores mark them private and unstable. Prefer the cloud `builtin.tool_call_success` and `builtin.tool_output_utilization` evaluators.

### Local Azure OpenAI grader wrappers

These experimental wrappers let `evaluate()` orchestrate OpenAI graders alongside local SDK evaluators. Constructor details can change between `azure-ai-evaluation` versions.

#### `AzureOpenAILabelGrader`

Wraps the `label_model` grader for custom classification.

```python
evaluators = {
    "label": AzureOpenAILabelGrader(
        model_config=model_config,
        input=[{"role": "user", "content": "Classify: {{item.response}}"}],
        labels=["pass", "fail"],
        model=model,
        name="label",
        passing_labels=["pass"],
    ),
}
```

#### `AzureOpenAIScoreModelGrader`

Wraps the `score_model` grader for custom numeric scoring.

```python
evaluators = {
    "score": AzureOpenAIScoreModelGrader(
        model_config=model_config,
        input=[{"role": "user", "content": "Score: {{item.response}}"}],
        model=model,
        name="score",
        range=[0, 5],
        pass_threshold=3,
    ),
}
```

#### `AzureOpenAIStringCheckGrader`

Wraps deterministic exact and pattern string checks.

```python
evaluators = {
    "string_check": AzureOpenAIStringCheckGrader(
        model_config=model_config,
        input="{{item.response}}",
        name="string_check",
        operation="eq",
        reference="{{item.ground_truth}}",
    ),
}
```

#### `AzureOpenAITextSimilarityGrader`

Wraps deterministic fuzzy, BLEU, GLEU, METEOR, cosine, or ROUGE comparison.

```python
evaluators = {
    "text_similarity": AzureOpenAITextSimilarityGrader(
        model_config=model_config,
        evaluation_metric="cosine",
        input="{{item.response}}",
        pass_threshold=0.8,
        reference="{{item.ground_truth}}",
        name="text_similarity",
    ),
}
```

#### `AzureOpenAIPythonGrader`

Runs custom Python grading logic with an optional pass threshold.

```python
evaluators = {
    "python": AzureOpenAIPythonGrader(
        model_config=model_config,
        name="exact_match",
        pass_threshold=1.0,
        source="""def grade(sample: dict, item: dict) -> float:
    return float(item["response"] == item["ground_truth"])
""",
    ),
}
```

`AzureOpenAIGrader` is the shared base class, not a concrete evaluator to instantiate directly.

## Deprecation and compatibility notes

- No current built-in evaluator, custom evaluator type, or public local evaluator class is documented as deprecated as of August 1, 2026.
- Local AI-assisted evaluators can still emit legacy metric keys prefixed with `gpt_` for backward compatibility. Microsoft recommends the unprefixed keys and states that the prefixed keys will be deprecated in the future.
- `_ToolCallSuccessEvaluator` and `_ToolOutputUtilizationEvaluator` are private, not deprecated public APIs. Do not treat their presence in a package build as a compatibility promise.
- Experimental APIs and Preview services are not synonyms for deprecated features: they are active but can change without stable compatibility guarantees.
- Package support evolves independently. Pin and test `azure-ai-projects`, `azure-ai-evaluation`, and `openai` versions in CI before using evaluator results as a merge gate.

## Choosing an API

Use Foundry cloud evaluation when you need managed asynchronous runs, portal reports, evaluator-catalog features, agent targets, traces, scheduling, or cloud-only evaluators.

Use local `evaluate()` when you need callable Python evaluators, custom local target functions, local result files, or compatibility with an existing `azure-ai-evaluation` workflow.

Do not pass local class instances such as `CoherenceEvaluator(...)` to `testing_criteria`. Do not pass a cloud criterion such as `{"evaluator_name": "builtin.coherence"}` to `evaluate(evaluators=...)`.

## Official references

- [Foundry built-in evaluators](https://learn.microsoft.com/azure/foundry/concepts/built-in-evaluators)
- [Foundry cloud evaluation](https://learn.microsoft.com/azure/foundry/how-to/develop/cloud-evaluation)
- [General-purpose evaluators](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/general-purpose-evaluators)
- [Textual-similarity evaluators](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/textual-similarity-evaluators)
- [RAG evaluators](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/rag-evaluators)
- [Agent evaluators](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/agent-evaluators)
- [Risk and safety evaluators](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/risk-safety-evaluators)
- [Azure OpenAI graders](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/azure-openai-graders)
- [Rubric evaluators](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/rubric-evaluators)
- [Custom evaluators](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/custom-evaluators)
- [Evaluation regions and limits](https://learn.microsoft.com/azure/foundry/concepts/evaluation-regions-limits-virtual-network)
- [`azure.ai.evaluation` Python API](https://learn.microsoft.com/python/api/azure-ai-evaluation/azure.ai.evaluation)
- [Azure SDK evaluation samples](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/ai/azure-ai-projects/samples/evaluations)
