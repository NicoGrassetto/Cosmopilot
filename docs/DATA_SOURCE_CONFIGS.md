# Azure Evaluation Data Source Reference

This reference distinguishes the two similarly named objects used by Foundry cloud evaluations:

- **`data_source_config`** defines the data shape or managed Foundry scenario when an evaluation definition is created with `client.evals.create(...)`.
- **`data_source`** supplies the concrete dataset, target, responses, traces, or generated data when a run is created with `client.evals.runs.create(...)`.

An evaluation definition is reusable. Multiple runs can use different datasets or target versions as long as their run sources satisfy the definition's data contract.

## Shared create and run pattern

```python
eval_object = client.evals.create(
    name="eu-resilience-agent-turn-response-quality-v1",
    data_source_config=data_source_config,
    testing_criteria=testing_criteria,
)

eval_run = client.evals.runs.create(
    eval_id=eval_object.id,
    name="agent-v3-golden-v2-pr-184",
    data_source=data_source,
    metadata={
        "target_version": "3",
        "dataset_version": "2",
        "trigger": "pull-request",
    },
)
```

## Create-time `data_source_config` types

### `custom`

Defines a JSON Schema for each evaluation item. Use it for uploaded or inline JSONL/CSV data, model targets, agent targets, and conversation simulation.

```python
from openai.types.eval_create_params import DataSourceConfigCustom

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
```

`item_schema` describes fields supplied by each input row. Required fields must exist in every row used by a run.

`include_sample_schema=True` allows testing criteria to reference values generated during a run through `{{sample.*}}`. Use it when a model or agent target produces the response. Dataset-only evaluations that use precomputed responses can set it to `False` or omit it.

#### Turn-level precomputed responses

```python
data_source_config = {
    "type": "custom",
    "item_schema": {
        "type": "object",
        "properties": {
            "question": {"type": "string"},
            "answer": {"type": "string"},
        },
        "required": ["question", "answer"],
    },
    "include_sample_schema": False,
}

criterion = {
    "type": "azure_ai_evaluator",
    "name": "coherence",
    "evaluator_name": "builtin.coherence",
    "initialization_parameters": {"model": model},
    "data_mapping": {
        "query": "{{item.question}}",
        "response": "{{item.answer}}",
    },
}
```

#### Model or agent-generated responses

Only the input belongs in `item_schema`; the generated result comes from `sample`.

```python
data_source_config = {
    "type": "custom",
    "item_schema": {
        "type": "object",
        "properties": {"question": {"type": "string"}},
        "required": ["question"],
    },
    "include_sample_schema": True,
}

criterion = {
    "type": "azure_ai_evaluator",
    "name": "relevance",
    "evaluator_name": "builtin.relevance",
    "initialization_parameters": {"model": model},
    "data_mapping": {
        "query": "{{item.question}}",
        "response": "{{sample.output_text}}",
    },
}
```

#### Conversation-level data

Each row contains a complete OpenAI-format conversation. Add `tool_definitions` when tool-aware evaluators require it.

```python
data_source_config = {
    "type": "custom",
    "item_schema": {
        "type": "object",
        "properties": {
            "messages": {"type": "array"},
            "tool_definitions": {"type": "array"},
        },
        "required": ["messages"],
    },
    "include_sample_schema": False,
}
```

Set the evaluation level on the run:

```python
client.evals.runs.create(
    eval_id=eval_object.id,
    name="conversation-quality-run",
    data_source=data_source,
    extra_body={"evaluation_level": "conversation"},
)
```

### `azure_ai_source`

Selects a Foundry-managed source scenario. Unlike `custom`, the service owns the source schema.

#### Stored agent responses

Use response IDs from the Foundry Responses API.

```python
data_source_config = {
    "type": "azure_ai_source",
    "scenario": "responses",
}
```

#### Application Insights traces

Use OpenTelemetry agent traces associated with the Foundry project.

```python
data_source_config = {
    "type": "azure_ai_source",
    "scenario": "traces",
}
```

#### Synthetic data generation (preview)

Foundry generates test queries and sends them to a model or agent target.

```python
data_source_config = {
    "type": "azure_ai_source",
    "scenario": "synthetic_data_gen_preview",
}
```

#### Red-team evaluation

Foundry generates adversarial prompts and evaluates a model or agent target.

```python
data_source_config = {
    "type": "azure_ai_source",
    "scenario": "red_team",
}
```

`azure_ai_source` is a Foundry extension and might require a plain dictionary or an Azure SDK model rather than an OpenAI `DataSourceConfig*` type, depending on the installed SDK version.

### `logs`

Selects OpenAI stored logs using metadata filters.

```python
from openai.types.eval_create_params import DataSourceConfigLogs

data_source_config = DataSourceConfigLogs(
    type="logs",
    metadata={
        "usecase": "eu-resilience-agent",
        "prompt-version": "v3",
    },
)
```

This is part of the OpenAI Evals API. For current Foundry agent telemetry, prefer the `azure_ai_source` traces scenario and a trace run source.

### `stored_completions` (deprecated)

The OpenAI SDK still exposes `DataSourceConfigStoredCompletions`, but it is deprecated in favor of `logs`.

```python
data_source_config = {
    "type": "stored_completions",
    "metadata": {"usecase": "eu-resilience-agent"},
}
```

Do not use it for new Foundry evaluation definitions.

## Run-time `data_source` types

### `jsonl`

Evaluates rows from an uploaded dataset or inline content. Use this for turn-level and conversation-level datasets.

#### Uploaded dataset

```python
data_source = {
    "type": "jsonl",
    "source": {
        "type": "file_id",
        "id": dataset_id,
    },
}
```

#### Inline rows

```python
data_source = {
    "type": "jsonl",
    "source": {
        "type": "file_content",
        "content": [
            {
                "item": {
                    "query": "What is hybrid resilience?",
                    "response": "Hybrid resilience combines preparedness across domains.",
                }
            }
        ],
    },
}
```

The row fields must satisfy the `custom.item_schema` used to create the evaluation definition.

### `csv`

Evaluates an uploaded or inline tabular dataset. Each row is a turn-level item and column names must match the custom schema.

```python
data_source = {
    "type": "csv",
    "source": {
        "type": "file_id",
        "id": dataset_id,
    },
}
```

CSV does not support conversation-level rows. Use JSONL for `messages` arrays.

### `azure_ai_target_completions`

Sends each source item to a model or agent and evaluates the generated response.

```python
data_source = {
    "type": "azure_ai_target_completions",
    "source": {
        "type": "file_id",
        "id": dataset_id,
    },
    "input_messages": {
        "type": "template",
        "template": [
            {
                "type": "message",
                "role": "user",
                "content": {
                    "type": "input_text",
                    "text": "{{item.question}}",
                },
            }
        ],
    },
    "target": target,
}
```

Criteria normally map generated text with `{{sample.output_text}}`. Agent evaluators that inspect tools use `{{sample.output_items}}`.

#### Model target

```python
target = {
    "type": "azure_ai_model",
    "model": model,
    "sampling_params": {
        "temperature": 0.0,
        "max_completion_tokens": 2048,
    },
}
```

#### Agent target

```python
target = {
    "type": "azure_ai_agent",
    "name": "eu-resilience-agent",
    "version": "3",
}
```

Omitting the agent version selects the latest version, which reduces reproducibility. Pin it for regression and release evaluations.

#### Hosted-agent invocations protocol

Hosted agents using a freeform invocations request can map fields directly instead of using the message template:

```python
data_source["input_messages"] = {
    "message": "{{item.question}}",
}
```

### `azure_ai_responses`

Retrieves already-stored Foundry responses by response ID and evaluates them without invoking the agent again.

```python
data_source = {
    "type": "azure_ai_responses",
    "item_generation_params": {
        "type": "response_retrieval",
        "data_mapping": {"response_id": "{{item.response_id}}"},
        "source": {
            "type": "file_content",
            "content": [
                {"item": {"response_id": "resp_abc123"}},
                {"item": {"response_id": "resp_def456"}},
            ],
        },
    },
}
```

This source currently requires inline `file_content`; `file_id` is not supported.

### `azure_ai_trace_data_source_preview`

Evaluates agent interactions already captured in Application Insights. The agent must emit `invoke_agent` spans that follow OpenTelemetry generative-AI semantic conventions.

#### Selected conversation IDs

```python
data_source = {
    "type": "azure_ai_trace_data_source_preview",
    "trace_source": {
        "type": "conversation_id_source",
        "conversation_ids": ["conversation_123", "conversation_456"],
    },
}
```

#### Sample traces for an agent

```python
import time

now = int(time.time())

data_source = {
    "type": "azure_ai_trace_data_source_preview",
    "trace_source": {
        "type": "agent_filter",
        "agent_name": "eu-resilience-agent",
        "agent_version": "3",
        "start_time": now - 86400,
        "end_time": now + 600,
        "max_traces": 100,
        "filter_strategy": "smart_filtering",
    },
}
```

`filter_strategy` can be `random_sampling` or `smart_filtering`. Conversation-level time windows must span at least 15 minutes. The future padding on `end_time` allows for telemetry ingestion delay.

Trace criteria typically map extracted fields as `{{item.query}}`, `{{item.response}}`, `{{item.tool_calls}}`, and `{{item.tool_definitions}}`.

Some API versions and older samples use the run type `azure_ai_traces`. Follow the type used by the installed Azure SDK and the API version selected by your project; `azure_ai_trace_data_source_preview` is the current preview form documented for conversation and filtered-trace evaluation.

### `azure_ai_synthetic_data_gen_preview`

Generates queries, sends them to a target, and evaluates the generated responses.

```python
data_source = {
    "type": "azure_ai_synthetic_data_gen_preview",
    "item_generation_params": {
        "type": "synthetic_data_gen_preview",
        "samples_count": 25,
        "prompt": "Generate questions about EU infrastructure resilience.",
        "model_deployment_name": model,
        "output_dataset_name": "eu-resilience-synthetic-v1",
    },
    "target": {
        "type": "azure_ai_agent",
        "name": "eu-resilience-agent",
        "version": "3",
    },
}
```

The generated query is available as `{{item.query}}`; target output is available as `{{sample.output_text}}`.

### Conversation simulation (preview)

Conversation simulation also uses `azure_ai_target_completions`, but adds `conversation_gen_preview` item generation parameters. Each source row describes a user scenario.

```python
data_source = {
    "type": "azure_ai_target_completions",
    "source": {"type": "file_id", "id": scenarios_dataset_id},
    "target": {
        "type": "azure_ai_agent",
        "name": "eu-resilience-agent",
        "version": "3",
    },
    "item_generation_params": {
        "type": "conversation_gen_preview",
        "model": simulator_model,
        "num_conversations": 2,
        "max_turns": 8,
        "data_mapping": {
            "id": "id",
            "test_case_description": "test_case_description",
            "desired_num_turns": "desired_num_turns",
        },
    },
}

client.evals.runs.create(
    eval_id=eval_object.id,
    name="eu-resilience-conversation-simulation-v3",
    data_source=data_source,
    extra_body={"evaluation_level": "conversation"},
)
```

### `azure_ai_red_team`

Runs a managed adversarial evaluation against a model or agent. Its exact taxonomy and attack-strategy configuration is preview and SDK-version dependent.

```python
data_source_config = {
    "type": "azure_ai_source",
    "scenario": "red_team",
}

data_source = {
    "type": "azure_ai_red_team",
    "target": {
        "type": "azure_ai_agent",
        "name": "eu-resilience-agent",
        "version": "3",
    },
    # Add the risk categories and attack strategies supported by your SDK.
}
```

Use the Azure SDK red-team sample matching the installed `azure-ai-projects` version before fixing preview configuration in source control.

## Source containers

Most dataset-backed run sources accept one of these containers.

### `file_id`

References a versioned dataset uploaded to the Foundry project.

```python
source = {
    "type": "file_id",
    "id": dataset_id,
}
```

Prefer this for CI/CD, repeatable comparisons, larger datasets, and dataset version tracking.

### `file_content`

Supplies rows inline with the run request.

```python
source = {
    "type": "file_content",
    "content": [
        {"item": {"query": "Example question", "response": "Example response"}},
    ],
}
```

Use this for quick tests, small curated cases, or source types such as `azure_ai_responses` that require inline content.

## Template namespaces

### `{{item.*}}`

References fields from the dataset row or fields extracted from a managed source.

```python
"query": "{{item.question}}"
"ground_truth": "{{item.expected_answer}}"
```

### `{{sample.output_text}}`

References plain text generated or retrieved during the run.

```python
"response": "{{sample.output_text}}"
```

Use it for model targets, agent targets, synthetic generation, and response retrieval when the evaluator expects text.

### `{{sample.output_items}}`

References structured agent output, including tool calls and tool results.

```python
"response": "{{sample.output_items}}"
```

Use it for agent evaluators such as task adherence and tool-call accuracy.

Do not map a generated target response to `{{item.response}}`; that would evaluate a dataset field instead of the target output.

## Selection guide

| Goal | `data_source_config` | Run `data_source` | Response mapping |
| --- | --- | --- | --- |
| Score precomputed JSONL responses | `custom` | `jsonl` | `{{item.response}}` |
| Score precomputed CSV responses | `custom` | `csv` | `{{item.response}}` |
| Generate and score model responses | `custom` | `azure_ai_target_completions` + `azure_ai_model` | `{{sample.output_text}}` |
| Generate and score agent responses | `custom` | `azure_ai_target_completions` + `azure_ai_agent` | `{{sample.output_text}}` or `{{sample.output_items}}` |
| Score stored Foundry response IDs | `azure_ai_source/responses` | `azure_ai_responses` | Managed output or `{{sample.*}}` |
| Score Application Insights traces | `azure_ai_source/traces` | `azure_ai_trace_data_source_preview` | `{{item.*}}` extracted from traces |
| Generate synthetic tests | `azure_ai_source/synthetic_data_gen_preview` | `azure_ai_synthetic_data_gen_preview` | `{{sample.output_text}}` |
| Simulate full conversations | `custom` | `azure_ai_target_completions` + `conversation_gen_preview` | Conversation mappings |
| Run managed red teaming | `azure_ai_source/red_team` | `azure_ai_red_team` | Scenario-managed |
| Filter OpenAI stored logs | `logs` | Log-backed run | Depends on log schema |

## Practical rules

- Keep one stable evaluation definition for one schema, scope, and criterion suite; create multiple runs to compare datasets, prompts, models, or agent versions.
- Version uploaded datasets and pin agent versions for reproducible comparisons.
- Use JSONL for conversations and structured agent messages.
- Make every field referenced by `{{item.*}}` available in the schema or managed source.
- Set `include_sample_schema=True` when criteria reference `{{sample.*}}`.
- Use `evaluation_level="conversation"` only with evaluators that support conversation-level scoring.
- Treat names containing `_preview` and red-team/simulation payloads as version-sensitive.

## Official references

- [Foundry cloud evaluation](https://learn.microsoft.com/azure/ai-foundry/how-to/develop/cloud-evaluation)
- [Run evaluations in the Foundry portal](https://learn.microsoft.com/azure/ai-foundry/how-to/evaluate-generative-ai-app)
- [Azure SDK evaluation samples](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/ai/azure-ai-projects/samples/evaluations)
- [OpenAI Python eval create types](https://github.com/openai/openai-python/blob/main/src/openai/types/eval_create_params.py)
- [Evaluator reference](EVALUATORS.md)
