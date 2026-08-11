# Microsoft Foundry evaluation guide

This document explains how to design, run, automate, and operate evaluations in
Microsoft Foundry. It is grounded in the packages pinned by this repository:

- `azure-ai-projects==2.4.0`
- `azure-ai-evaluation==1.18.3`
- `openai==2.53.0`

Last audited: August 10, 2026.

The APIs include stable and preview surfaces. Preview status is attached to the
operation or feature, not inferred from the package version. Recheck the linked
Microsoft documentation before using preview features in production.

## Executive summary

Foundry evaluation has four cooperating API surfaces:

| Owner | Entry point | Responsibility |
| --- | --- | --- |
| OpenAI-compatible evaluation API | `project_client.get_openai_client().evals` | Reusable evaluation definitions, runs, run status, and row-level output items |
| Foundry project API | `project_client.beta.evaluators` | Versioned custom evaluator assets and evaluator-generation jobs |
| Foundry automation APIs | `project_client.evaluation_rules` (stable client surface) and `project_client.beta.schedules` | Continuous evaluation of completed responses and scheduled evaluation runs |
| Local Evaluation SDK | `azure.ai.evaluation.evaluate` | Local orchestration using Python evaluator classes or callables |

Do not confuse these resources:

- An **evaluator** defines how one aspect is scored.
- An **evaluation definition** declares the accepted data schema and evaluator
  criteria. It is reusable.
- An **evaluation run** applies one evaluation definition to one data source or
  target at a point in time.
- A **dataset** stores test cases. Dataset versions are immutable inputs to runs.
- An **evaluation rule** samples completed live responses and adds runs to an
  existing evaluation definition.
- A **schedule** starts a configured evaluation run at fixed times.

The usual production sequence is:

```text
Define behavior and risk requirements
  -> create or select evaluators
  -> create a versioned dataset
  -> create one reusable evaluation definition
  -> start a one-off run
  -> inspect aggregate and row-level results
  -> establish gates
  -> add scheduled and/or continuous evaluation
  -> investigate drift with traces, insights, and red teaming
```

## Which evaluation path to use

| Need | Recommended path | Why |
| --- | --- | --- |
| Fast deterministic checks during development | Python tests or local callable evaluators | Fast, cheap, reproducible, and no managed run required |
| Run SDK evaluator classes from a workstation or CI runner | `azure.ai.evaluation.evaluate()` | Local orchestration with optional upload of results to Foundry |
| Evaluate a versioned JSONL/CSV dataset at scale | OpenAI-compatible cloud evaluation | Managed parallel execution, stored reports, repeatable runs |
| Generate responses from a model or agent and score them | Cloud evaluation with a target-completions data source | Keeps test inputs stable while exercising the deployed target |
| Score already completed Foundry responses | `azure_ai_responses` run data source | Reuses stored response IDs without replaying the request |
| Score production behavior from telemetry | Trace data source or continuous evaluation rule | Measures real traffic and avoids synthetic-only blind spots |
| Run a golden regression suite every night | `project_client.beta.schedules` | Stable dataset, predictable cadence, comparable history |
| Sample each completed response probabilistically | `project_client.evaluation_rules` | Continuous, asynchronous production monitoring |
| Create domain-specific semantic criteria | Prompt-based custom evaluator | LLM judge can assess nuanced requirements |
| Create deterministic custom criteria | Code-based custom evaluator or local callable | Reproducible rule-based scoring |
| Use proprietary systems during scoring | Endpoint-based custom evaluator | Endpoint can use network, databases, and private dependencies |
| Bootstrap test questions before production traffic exists | Foundry data-generation job or synthetic run data source | Produces broad initial coverage from prompts, files, or an agent |
| Test multi-turn outcomes | Conversation-level evaluation or simulation | Measures resolution and satisfaction across the whole interaction |
| Probe jailbreak and harmful-content behavior | Red teaming and adversarial simulation | Generates attacks rather than only scoring normal prompts |

## Evaluation moments

Use multiple moments because each catches a different class of failure.

| Moment | Typical data | Scope | Blocking behavior |
| --- | --- | --- | --- |
| Local/manual | 3-10 focused cases | Deterministic checks and smoke evaluation | Developer decision |
| Pull request | Small, stable golden dataset | Prompt, schema, tool, and behavior regression | Block merge |
| Merge or predeployment | Held-out validation dataset | Quality, safety, grounding, agent behavior | Block promotion |
| Postdeployment | 3-5 live smoke cases | Identity, target, tools, connectivity | Roll back or stop promotion |
| Nightly | Larger evaluation dataset | Broad regression, conversations, model comparison | Alert or open issue |
| Weekly or pre-release | Synthetic, adversarial, red-team, compliance sets | Rare and safety-critical behavior | Release gate |
| Production continuous | Sampled responses or traces | Drift and real-user behavior | Alert, normally not user-blocking |
| Incident/manual | Failed trace plus neighboring cases | Reproduce and verify a fix | Incident-dependent |

Production evaluation must be asynchronous. Do not delay a user response while
an LLM judge scores it.

## Authentication and client construction

Most modules in this repository read environment variables directly. Run
Azure-dependent commands with `azd exec -- ...` or export the selected azd
environment first.

```python
import os

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

with (
    DefaultAzureCredential() as credential,
    AIProjectClient(
        endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
        credential=credential,
    ) as project_client,
    project_client.get_openai_client() as openai_client,
):
    ...
```

Important environment values include:

- `AZURE_AI_PROJECT_ENDPOINT`: project endpoint ending in
  `/api/projects/<project-name>`.
- `AZURE_DEPLOYMENT_NAME` or `AZURE_AI_MODEL_DEPLOYMENT_NAME`: model used as a
  target, simulator, or judge.
- Application Insights resource configuration when traces or monitoring are
  involved.

Calls through `project_client.beta.*` already opt in to preview behavior. Other
preview features exposed on stable clients can require `allow_preview=True`.

RBAC depends on the workflow. At minimum, the caller commonly needs the
**Foundry User** role. Continuous evaluation also requires the project managed
identity to have **Foundry User**. Trace evaluation requires access to the
connected Application Insights and Log Analytics resources; protected tables
can additionally require **Privileged Monitoring Data Reader**.

## Cloud evaluation lifecycle

### 1. Create a reusable evaluation definition

Use the OpenAI-compatible client, not `project_client.beta.evaluators`, to
create an evaluation definition:

```python
evaluation = openai_client.evals.create(
    name="weather-agent-quality",
    data_source_config={
        "type": "custom",
        "item_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "context": {"type": "string"},
            },
            "required": ["query", "context"],
        },
        "include_sample_schema": True,
    },
    testing_criteria=[...],
    metadata={"owner": "weather-agent"},
)
```

Create one stable definition for one data contract and criterion suite. Create
new runs for commits, prompt versions, model versions, dataset versions, and
schedules. This preserves comparability.

`openai_client.evals` exposes:

| Method | Purpose |
| --- | --- |
| `create(...)` | Create an evaluation definition |
| `retrieve(eval_id)` | Retrieve one definition |
| `update(eval_id, ...)` | Update mutable definition fields |
| `list(...)` | List definitions with pagination/filtering |
| `delete(eval_id)` | Delete a definition |

### 2. Start a run

```python
run = openai_client.evals.runs.create(
    eval_id=evaluation.id,
    name="pr-142-a1b2c3d",
    data_source={...},
    metadata={
        "commit": "a1b2c3d",
        "dataset_version": "7",
        "agent_version": "12",
    },
)
```

Run metadata should make a result attributable to code, prompt, model, agent,
and dataset versions.

`openai_client.evals.runs` exposes:

| Method | Purpose |
| --- | --- |
| `create(eval_id, data_source=..., ...)` | Start an asynchronous run |
| `retrieve(run_id, eval_id=...)` | Retrieve status and aggregate results |
| `list(eval_id, after=..., limit=..., order=..., status=...)` | List run history |
| `cancel(run_id, eval_id=...)` | Cancel an ongoing run |
| `delete(run_id, eval_id=...)` | Delete a run record |

Run statuses are `queued`, `in_progress`, `completed`, `canceled`, and `failed`.

### 3. Poll and retrieve row-level output

```python
import time

while True:
    completed_run = openai_client.evals.runs.retrieve(
        run_id=run.id,
        eval_id=evaluation.id,
    )
    if completed_run.status in ("completed", "failed", "canceled"):
        break
    time.sleep(5)

output_items = list(
    openai_client.evals.runs.output_items.list(
        run_id=completed_run.id,
        eval_id=evaluation.id,
        order="asc",
    )
)
```

`output_items` supports:

| Method | Purpose |
| --- | --- |
| `list(run_id, eval_id=..., after=..., limit=..., order=..., status=...)` | List row-level outputs; `status` is `pass` or `fail` |
| `retrieve(output_item_id, run_id=..., eval_id=...)` | Retrieve one row-level result |

The run contains aggregate pass/fail counts, per-criterion summaries, and a
`report_url` when a portal report is available. Output items contain the source
item/sample, criterion results, score, label/pass state, threshold, reason, and
error details when applicable.

Treat failed infrastructure execution differently from a genuine failing
score. Retry transient service failures, not an evaluator judgment that simply
disagrees with the target output.

## Evaluation definition data-source configurations

The definition establishes what data shape graders may reference. The run later
supplies actual data.

### OpenAI-native configurations

| Type | Use |
| --- | --- |
| `custom` | Declare a JSON Schema for `item` and optionally expect generated `sample` values |
| `logs` | Select stored logs using metadata filters |
| `stored_completions` | Deprecated; use `logs` |

A custom definition has:

- `item_schema`: JSON Schema for each test item.
- `include_sample_schema`: set `True` when the run generates or retrieves target
  output under `sample`.

### Foundry scenario configurations

Foundry extends the OpenAI-compatible API with `azure_ai_source` scenarios.
These are commonly passed as dictionaries because the upstream OpenAI package
does not model every Foundry extension.

| Scenario | Intended runtime source |
| --- | --- |
| `responses` | Stored Foundry response IDs |
| `traces` | Agent traces or conversations from Application Insights |
| `synthetic_data_gen_preview` | Generated single-turn queries and target responses |
| Red-team scenario | Generated adversarial inputs and target responses |

The definition config and run data source must agree. A custom item schema used
for JSONL runs is not interchangeable with a traces scenario without changing
the mappings.

## Run data sources

The upstream OpenAI client models three native run data-source types. Foundry
adds project-specific types described in the following subsections.

| Native type | Populates `item` from | Generates `sample` |
| --- | --- | --- |
| `jsonl` | Uploaded file or inline rows | No, unless each row already supplies a `sample` object |
| `completions` | File, inline rows, or deprecated stored-completion filters | Yes, through Chat Completions-style model sampling |
| `responses` | File, inline rows, or filtered stored Responses API objects | Yes, through Responses API model sampling |

Both sampling sources accept an input-message template or an item reference,
model name, and sampling parameters. `completions` supports function tools and
Chat Completions response formats. `responses` supports Responses API tools,
reasoning effort, token limits, temperature, top-p, seed, and text format.

These native sources address OpenAI model sampling. Foundry's
`azure_ai_target_completions` is the project-aware path for Foundry model and
agent targets.

### Existing JSONL or CSV data

Use an uploaded file for reusable CI/CD and production evaluation. Use inline
content only for small experiments or APIs that require it.

`jsonl` is part of the upstream OpenAI run-source union. Foundry additionally
supports `csv` for turn-level tabular evaluation; the Foundry SDK exposes typed
CSV run-source models even though the upstream OpenAI union does not.

```python
data_source = {
    "type": "jsonl",
    "source": {
        "type": "file_id",
        "id": dataset.id,
    },
}
```

Inline rows use `file_content`:

```python
data_source = {
    "type": "jsonl",
    "source": {
        "type": "file_content",
        "content": [
            {
                "item": {
                    "query": "Will it rain in Paris tomorrow?",
                    "context": "Frozen authoritative forecast context",
                }
            }
        ],
    },
}
```

Each JSONL line is one turn-level item unless the evaluation is explicitly run
at conversation level with a `messages` array.

### Model or agent target completions

Use `azure_ai_target_completions` when the dataset has inputs but no responses.
Foundry sends each item to the target and exposes generated output in `sample`.

Target choices include:

- `azure_ai_model`: a deployed model.
- `azure_ai_agent`: a Foundry prompt or hosted agent, optionally pinned to a
  version.

Use `{{sample.output_text}}` for evaluators expecting plain text. Use
`{{sample.output_items}}` for agent evaluators that inspect structured response
items or tool calls.

### Native OpenAI completions and responses

Use `type="completions"` when the target should be sampled through the Chat
Completions contract. Sources may be `file_content`, `file_id`, or deprecated
`stored_completions` filters. Define `input_messages`, `model`, and optional
sampling parameters.

Use `type="responses"` when the target should be sampled through the Responses
API. Sources may be `file_content`, `file_id`, or a `responses` query filtered
by timestamps, metadata, model, instructions, reasoning effort, tools,
temperature, top-p, or users.

Prefer the Responses API for new OpenAI-native agentic/model workflows unless a
dependency specifically requires Chat Completions. Prefer the Foundry target
types when the target is a versioned Foundry agent or project deployment and
the run needs Foundry-specific output fields.

### Stored responses

Use `azure_ai_responses` to score already completed Responses API interactions.
The source maps each inline `response_id`. This path supports inline
`file_content`; a file ID is not supported for agent-response evaluation.

This is useful for targeted post-hoc evaluation, but a response ID is not a
substitute for a representative dataset.

### Traces

Use `azure_ai_trace_data_source_preview` or the currently supported trace source
form to evaluate OpenTelemetry `invoke_agent` spans from Application Insights.
Select data by:

- explicit trace IDs;
- explicit conversation IDs; or
- an agent filter, time window, maximum trace count, and sampling strategy.

Trace attributes must follow the generative AI OpenTelemetry semantic
conventions. Important inputs include:

- `gen_ai.operation.name="invoke_agent"`;
- agent ID/name;
- input and output messages;
- tool definitions when tool evaluators are used;
- conversation ID for conversation grouping.

Intelligent sampling favors diverse or interesting traces. Random sampling is
appropriate when an unbiased estimate of production frequency is more
important. Keep the sampling method in run metadata because it changes how
aggregate scores should be interpreted.

### Synthetic single-turn data

Use `azure_ai_synthetic_data_gen_preview` when no adequate test set exists.
The service:

1. generates queries from a prompt and optional source file;
2. sends queries to a model or agent target;
3. evaluates generated responses; and
4. stores generated queries as a reusable dataset.

`samples_count` is the maximum number of queries. For the standalone Foundry
data-generation service, current `SimpleQnA` generation supports 15-1,000
samples and Microsoft recommends reviewing a first batch of 15 before scaling.

### Conversation simulation

Use conversation generation when a single-turn score cannot measure task
resolution. Each source row describes a scenario with fields such as:

- `id`;
- `test_case_description`; and
- `desired_num_turns`.

The simulator plays the user against an agent target and produces complete
conversations. Configure the number of conversations per scenario, maximum
turns, simulator model, and sampling parameters. Evaluate the result at
conversation level.

### Red-team data

Use a red-team run when the objective is to discover vulnerabilities, not to
estimate ordinary quality. Red teaming generates attacks across risk categories
and strategies, sends them to the target, and reports attack success/defect
rates with examples.

Do not merge red-team results blindly into ordinary pass-rate averages. Track
risk categories separately and treat material safety defects as release issues.

## Data mapping

Testing criteria reference runtime fields using templates:

| Namespace | Meaning | Examples |
| --- | --- | --- |
| `item` | Dataset row, synthetic query, or mapped trace fields | `{{item.query}}`, `{{item.context}}`, `{{item.ground_truth}}` |
| `sample` | Output generated or retrieved by the run | `{{sample.output_text}}`, `{{sample.output_items}}` |

Rules:

1. Map precomputed dataset responses from `item`, for example
   `{{item.response}}`.
2. Map target-generated text from `sample.output_text`.
3. Use `sample.output_items` when the evaluator needs structured agent output.
4. Include `tool_definitions` and tool-call fields only for evaluators that need
   them.
5. Keep field names case-sensitive and consistent with the JSON Schema.
6. Set `include_sample_schema=True` whenever criteria reference `sample`.

## Testing criterion families

An evaluation can combine compatible criteria. Every criterion in one run must
be compatible with the evaluation level and available data fields.

### Microsoft Foundry catalog evaluators

Use criterion type `azure_ai_evaluator` and identify a built-in evaluator by its
`builtin.*` catalog ID or a custom evaluator by project asset name/version.

```python
criterion = {
    "type": "azure_ai_evaluator",
    "name": "weather_grounding",
    "evaluator_name": "weather-agent-grounding",
    "evaluator_version": "1",
    "initialization_parameters": {
        "deployment_name": os.environ["AZURE_DEPLOYMENT_NAME"],
        "threshold": 4,
    },
    "data_mapping": {
        "query": "{{item.query}}",
        "response": "{{sample.output_text}}",
        "context": "{{item.context}}",
    },
}
```

### OpenAI-native graders

The OpenAI package used by this repository accepts these evaluation criteria:

| Type | Best use |
| --- | --- |
| `label_model` | Classify outputs into predefined labels with designated passing labels |
| `string_check` | Deterministic equality, containment, or related string checks |
| `text_similarity` | Deterministic/reference similarity metrics with a pass threshold |
| `python` | Execute Python grader logic supported by the managed grader environment |
| `score_model` | Ask a model to assign a numeric score |

Prefer deterministic graders when the requirement can be expressed exactly.
Use model graders for semantic requirements and manually calibrate them against
human-reviewed examples.

## Built-in Foundry evaluator catalog

The catalog changes independently of this guide. Use
`project_client.beta.evaluators.list(type="builtin")` to inspect the catalog
available to the project and its supported evaluation levels.

### General quality

| Evaluator | Catalog ID | Typical inputs | Lifecycle | Use when |
| --- | --- | --- | --- | --- |
| Coherence | `builtin.coherence` | query, response or messages | GA | Logical organization and consistency matter |
| Fluency | `builtin.fluency` | response | GA | Natural-language quality matters |

### Textual similarity

| Evaluator | Catalog ID | Lifecycle | Notes |
| --- | --- | --- | --- |
| Similarity | `builtin.similarity` | GA | Semantic/reference similarity |
| F1 | `builtin.f1_score` | GA | Token overlap |
| BLEU | `builtin.bleu_score` | GA | N-gram precision-oriented comparison |
| GLEU | `builtin.gleu_score` | GA | Sentence-level overlap variant |
| ROUGE | `builtin.rouge_score` | GA | Recall-oriented overlap |
| METEOR | `builtin.meteor_score` | GA | Alignment with stemming/synonym-aware behavior |

Similarity metrics are useful for constrained outputs, extraction, or
translation. They are weak proxies for open-ended correctness and should not be
the only quality signal for an assistant.

### RAG and grounding

| Evaluator | Catalog ID | Typical inputs | Lifecycle | Measures |
| --- | --- | --- | --- | --- |
| Retrieval | `builtin.retrieval` | query, context | GA | Relevance of retrieved context |
| Document retrieval | `builtin.document_retrieval` | retrieval truth, retrieved documents | GA | Retrieval ranking/coverage |
| Groundedness | `builtin.groundedness` | response, context, often query | GA | Whether claims follow from context |
| Relevance | `builtin.relevance` | query, response | GA | Whether the answer addresses the request |
| Groundedness Pro | `builtin.groundedness_pro` | query, response, context | Preview | Service-assisted advanced grounding |
| Response completeness | `builtin.response_completeness` | response and expected/reference information | Preview | Whether required information was omitted |

A typical RAG suite combines retrieval, groundedness, and relevance. A strong
answer cannot compensate for consistently poor retrieval, and relevant context
does not guarantee the answer used it faithfully.

### Risk and safety

| Evaluator | Catalog ID | Lifecycle | Purpose |
| --- | --- | --- | --- |
| Hate/unfairness | `builtin.hate_unfairness` | GA | Hate, unfairness, and protected-class harms |
| Sexual | `builtin.sexual` | GA | Sexual content risk |
| Violence | `builtin.violence` | GA | Violent content risk |
| Self-harm | `builtin.self_harm` | GA | Self-harm content risk |
| Protected material | `builtin.protected_material` | GA | Protected/copyright-sensitive material |
| Indirect attack | `builtin.indirect_attack` | GA | Prompt injection through retrieved/context content |
| Code vulnerability | `builtin.code_vulnerability` | GA | Vulnerabilities in generated code |
| Ungrounded attributes | `builtin.ungrounded_attributes` | GA | Unsupported sensitive/person attributes |
| Prohibited actions | `builtin.prohibited_actions` | Preview | Disallowed agent actions |
| Sensitive data leakage | `builtin.sensitive_data_leakage` | Preview | Leakage through messages or tool use |

Safety scores often use a severity scale where lower is safer, unlike quality
metrics where higher is better. Never assume that one threshold convention
applies to every criterion.

### Agent behavior

| Evaluator | Catalog ID | Lifecycle | Measures |
| --- | --- | --- | --- |
| Task adherence | `builtin.task_adherence` | Preview | Compliance with instructions and constraints |
| Task completion | `builtin.task_completion` | Preview | End-to-end task success |
| Customer satisfaction | `builtin.customer_satisfaction` | Preview | Likely satisfaction across a conversation |
| Intent resolution | `builtin.intent_resolution` | Preview | Correct identification and resolution of intent |
| Quality grader | `builtin.quality_grader` | Preview | Combined relevance, abstention, completeness, and optional grounding/context coverage |
| Task navigation efficiency | `builtin.task_navigation_efficiency` | GA | Actual versus expected action sequence |
| Tool call accuracy | `builtin.tool_call_accuracy` | GA | Overall choice, inputs, outputs, and efficiency |
| Tool selection | `builtin.tool_selection` | GA | Whether the correct necessary tools were selected |
| Tool input accuracy | `builtin.tool_input_accuracy` | GA | Correctness and grounding of tool arguments |
| Tool output utilization | `builtin.tool_output_utilization` | GA | Whether tool results were interpreted and used |
| Tool call success | `builtin.tool_call_success` | GA | Technical tool execution success |

Tool-aware evaluator support is not uniform. File Search, user-defined Function
tools, MCP, and knowledge-based MCP have the strongest support. Current
documentation identifies limited evaluator support for Azure AI Search, Bing
Grounding, Bing Custom Search, SharePoint Grounding, Code Interpreter, Fabric
Data Agent, Web Search, and other tools. For those tools, prefer frozen context
plus domain-specific grading or validate support with a focused run before
making the evaluator a release gate.

### Conversation-level evaluation

Turn-level evaluation is the default. Conversation-level evaluation scores a
complete `messages` sequence and is appropriate for:

- task completion across retries;
- customer satisfaction;
- repeated or ineffective actions;
- multi-agent handoffs;
- tool-use sequences; and
- whether a conversation eventually resolves the user's goal.

Create one JSONL row per conversation and pass:

```python
run = openai_client.evals.runs.create(
    eval_id=evaluation.id,
    name="conversation-regression",
    data_source=data_source,
    extra_body={"evaluation_level": "conversation"},
)
```

Do not mix turn-only evaluators into a conversation-level run. Inspect the
evaluator asset's `supported_evaluation_levels` field first.

## Custom evaluator assets

Custom evaluator assets are versioned project resources managed through
`project_client.beta.evaluators`. They are not evaluation definitions and do not
run until referenced by a criterion in an evaluation run.

### Asset lifecycle API

| Method | Purpose |
| --- | --- |
| `create_version(name, evaluator_version)` | Create a new auto-numbered version |
| `get_version(name, version)` | Retrieve one version |
| `list(type=..., limit=...)` | List latest versions, including built-in/custom filtering |
| `list_versions(name, type=..., limit=...)` | List all versions of one name |
| `update_version(name, version, evaluator_version)` | Update a specific version in place |
| `delete_version(name, version)` | Delete one version |
| `pending_upload(name, version, pending_upload_request)` | Prepare or retrieve an artifact upload location |
| `get_credentials(name, version, credential_request)` | Obtain temporary storage credentials for artifacts |
| `begin_create_generation_job(job, operation_id=...)` | Generate and persist a rubric evaluator asynchronously |
| `get_generation_job(job_id)` | Retrieve evaluator-generation job state |
| `list_generation_jobs(...)` | List generation jobs |
| `cancel_generation_job(job_id)` | Cancel a generation job |
| `delete_generation_job(job_id)` | Delete only the job record; preserve generated evaluator |

The SDK method is `begin_create_generation_job`, not
`create_generation_job`. It returns an `LROPoller[EvaluatorVersion]`.

### Prompt-based evaluators

Use for semantic, domain-specific judgments. Define:

- `prompt_text` with `{{field}}` variables;
- `init_parameters` JSON Schema requiring `deployment_name` and `threshold`;
- `data_schema` for mapped inputs; and
- one or more `EvaluatorMetric` definitions.

The judge must return JSON with `result` and `reason`. Supported metric types are:

- `ordinal`;
- `continuous`; and
- `boolean`.

Prompt evaluators can support turn or conversation level, but each prompt-based
version supports exactly one configured level.

### Code-based evaluators

Use a Python function named `grade(sample: dict, item: dict) -> float`. It must
return a value from 0.0 through 1.0. Code execution is sandboxed and currently
has no network access, a two-minute limit, and resource/package restrictions.

Current runtime schema requires both `deployment_name` and `pass_threshold`,
even though grading code itself does not call a model.

Use this type for deterministic formatting, required phrase, range, schema, and
policy checks. Handle malformed data defensively because exceptions become
evaluation errors.

### Endpoint-based evaluators

Use when grading requires:

- network access;
- a proprietary model;
- a database;
- private dependencies; or
- complex logic outside the code sandbox.

The evaluator references a project connection by name. The endpoint receives
mapped `item` and optional `sample` data and must return the standard evaluator
response (`score`, `reason`, `status`, optional properties, threshold, and
passed state). It must respond within the service timeout.

Prefer Microsoft Entra authentication over static API keys when feasible.

### Rubric-based evaluators

Rubric evaluators contain weighted dimensions and an aggregate pass threshold.
They can be authored manually with `RubricBasedEvaluatorDefinition` or generated
from source material through an evaluator-generation job.

Generation inputs can reference:

- an agent definition;
- an inline prompt;
- traces; and
- a dataset.

Use generation to bootstrap a rubric, then review dimensions with domain owners.
Do not treat an automatically generated rubric as an approved policy contract.

### Versioning practice

- Keep a stable evaluator name for one semantic purpose.
- Create a new version when prompt, code, schema, dimensions, or metric meaning
  changes.
- Pin `evaluator_version` in release-gating definitions.
- Evaluate a new evaluator version against human-labeled calibration examples
  before replacing a gate.
- Delete old versions only after their historical runs no longer need to be
  reproduced.

## Dataset management

Stable dataset operations live at `project_client.datasets`:

| Method | Purpose |
| --- | --- |
| `upload_file(name, version, file_path)` | Upload a versioned file dataset |
| `get(name, version)` | Retrieve a dataset version |
| `list()` | List dataset versions |
| `delete(name, version)` | Delete a dataset version |

Use immutable versions and include the version in run metadata. Never overwrite
the conceptual meaning of a version.

### Recommended dataset roles

| Repository data | Role |
| --- | --- |
| `golden_dataset.jsonl` | Small, stable, human-reviewed regression gate |
| `validation_dataset.jsonl` | Held-out predeployment/release validation |
| `evaluation_dataset.jsonl` | Broader recurring and comparative evaluation |
| `synthetic/` | Generated edge cases and coverage expansion |
| Production traces | Real distribution and drift monitoring |

Avoid leakage: do not tune prompts repeatedly against the held-out validation
set. Promote important production failures into a reviewed regression set after
fixing and labeling them.

### Composition

Microsoft's GenAIOps learning path recommends starting a comprehensive set at
about 100 examples with this composition:

- 60-70% common scenarios;
- 20-30% phrasing/context variations;
- 5-10% edge cases; and
- 5-10% adversarial cases.

Five to ten diverse prompts are appropriate for manual or smoke evaluation, not
for estimating a stable production pass rate.

For time-sensitive domains such as weather, store frozen authoritative context
with each expected response. Do not compare today's live forecast against
yesterday's expected temperature.

## Foundry data-generation jobs

The current generation service lives under `project_client.beta.datasets`:

| Method | Purpose |
| --- | --- |
| `begin_create_generation_job(job, operation_id=...)` | Start asynchronous generation |
| `get_generation_job(job_id)` | Inspect one job |
| `list_generation_jobs(...)` | List jobs |
| `cancel_generation_job(job_id)` | Cancel a job |
| `delete_generation_job(job_id)` | Delete the job record, not generated output |

Data-generation sources include agent definitions, prompts, reference files,
and traces. Scenarios include evaluation data and fine-tuning/task/tool-use data
supported by the service models. The `SimpleQnA` evaluation path produces
`query` and `ground_truth` rows.

Review generated rows before using them as a gate. Synthetic data can amplify
the generator's assumptions and should complement, not replace, human-curated
and production-derived examples.

## Local Evaluation SDK

Use `azure.ai.evaluation.evaluate()` when the orchestrator should run in your
Python process. Model-assisted evaluators still call Azure services; “local”
describes orchestration, not necessarily inference.

```python
from azure.ai.evaluation import CoherenceEvaluator, evaluate

result = evaluate(
    data="data/weather/datasets/evaluation_dataset.jsonl",
    evaluators={
        "coherence": CoherenceEvaluator(model_config),
    },
    evaluator_config={
        "coherence": {
            "column_mapping": {
                "query": "${data.query}",
                "response": "${data.response}",
            }
        }
    },
    azure_ai_project=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
    evaluation_name="weather-local-evaluation",
    output_path="artifacts/weather-evaluation.json",
)
```

### Public local evaluator families

| Family | Public classes in 1.18.3 |
| --- | --- |
| Quality | `CoherenceEvaluator`, `FluencyEvaluator`, `RelevanceEvaluator`, `SimilarityEvaluator`, `QAEvaluator`, `ResponseCompletenessEvaluator` |
| RAG/retrieval | `GroundednessEvaluator`, `GroundednessProEvaluator`, `RetrievalEvaluator`, `DocumentRetrievalEvaluator` |
| Text similarity | `F1ScoreEvaluator`, `BleuScoreEvaluator`, `GleuScoreEvaluator`, `MeteorScoreEvaluator`, `RougeScoreEvaluator` and `RougeType` |
| Safety | `ContentSafetyEvaluator`, `HateUnfairnessEvaluator`, `SexualEvaluator`, `ViolenceEvaluator`, `SelfHarmEvaluator`, `ProtectedMaterialEvaluator`, `IndirectAttackEvaluator`, `CodeVulnerabilityEvaluator`, `UngroundedAttributesEvaluator` |
| Agent | `IntentResolutionEvaluator`, `TaskAdherenceEvaluator`, `ToolCallAccuracyEvaluator` |

The package also exports private, leading-underscore tool evaluators. Do not
build production code against private symbols.

Public lifecycle status differs by class. Stable orchestration does not make
every evaluator GA. In this repository's pinned version, quality and traditional
similarity evaluators are generally the most stable; several safety, advanced
grounding, and agent evaluators are experimental. Check the current Python API
reference before upgrading or making an experimental class a hard gate.

### Local callable evaluators

`evaluate()` accepts synchronous or asynchronous callables. Named parameters
define required mapped inputs, and the callable returns a dictionary of metric
values.

Use local callables for repository-specific deterministic logic that does not
need to become a reusable Foundry catalog asset. Use a cloud custom evaluator
when the evaluator must be versioned, shared, scheduled, or used in continuous
evaluation.

### Local result shape

The local `evaluate()` result contains aggregate metrics, row-level results,
and a portal/studio URL when results are uploaded to a Foundry project. Persist
`output_path` artifacts in CI for diagnosis, but do not commit generated results
unless they are intentional baselines.

### Azure OpenAI grader wrappers

The local SDK can delegate grader execution to the OpenAI-compatible eval API.
Version 1.18.3 exports:

- `AzureOpenAIGrader` (base contract);
- `AzureOpenAILabelGrader`;
- `AzureOpenAIStringCheckGrader`;
- `AzureOpenAITextSimilarityGrader`;
- `AzureOpenAIScoreModelGrader`; and
- `AzureOpenAIPythonGrader`.

Pass these objects in the same `evaluators` dictionary accepted by
`evaluate()`. The orchestrator separates local callable evaluators from managed
graders and combines their outputs. This is useful when a single local command
must run both SDK evaluator classes and OpenAI-native graders.

The public package also exports configuration and result contracts including
`AzureAIProject`, `AzureOpenAIModelConfiguration`,
`OpenAIModelConfiguration`, `EvaluatorConfig`, `Conversation`, `Message`, and
`EvaluationResult`.

`evaluate()` requires `data` and `evaluators`; accepts an optional callable
`target`, column mappings in `evaluator_config`, `azure_ai_project`, output
path, tags, and `fail_on_evaluator_errors`. Keep the call under an
`if __name__ == "__main__":` guard because local orchestration can use multiple
processes. Avoid `fail_on_evaluator_errors=True` for broad runs: one evaluator
error cancels the run and can discard otherwise useful results.

## Simulation and adversarial testing

There are three distinct mechanisms:

1. **Foundry cloud synthetic evaluation** generates queries inside an evaluation
   run, invokes a target, and scores responses.
2. **Foundry beta dataset generation** creates a reusable versioned dataset from
   agent, prompt, file, or trace sources.
3. **Azure AI Evaluation SDK simulators** generate interaction data under local
   orchestration. These simulator APIs are preview/classic-oriented and can
   change between releases.

The local SDK simulator family includes non-adversarial simulation and direct or
indirect adversarial simulation. Use indirect attack simulation when untrusted
retrieved content could inject instructions. Use direct attacks for jailbreak
and harmful-request resilience.

The simulator module exports:

- `Simulator`;
- `AdversarialSimulator`;
- `DirectAttackSimulator`;
- `IndirectAttackSimulator`;
- `AdversarialScenario`;
- `AdversarialScenarioJailbreak`; and
- `SupportedLanguages`.

The separate `azure.ai.evaluation.red_team` package exports `RedTeam`,
`AttackStrategy`, `RiskCategory`, `RedTeamResult`, and `SupportedLanguages`.
It requires the optional dependency installed with
`azure-ai-evaluation[redteam]`. This local/PyRIT-based orchestration is distinct
from `project_client.beta.red_teams`.

Always label synthetic and adversarial rows with provenance and scenario. Keep
them separate from organic production-frequency estimates.

## Red teaming and taxonomies

Foundry's beta red-team resource surface is:

| Method | Purpose |
| --- | --- |
| `project_client.beta.red_teams.create(red_team)` | Create a red-team resource/run configuration |
| `project_client.beta.red_teams.get(name)` | Retrieve it by name |
| `project_client.beta.red_teams.list()` | List red-team resources |

A `RedTeam` resource requires a target and can specify display name, number of
turns, attack strategies, simulation-only mode, risk categories, application
scenario, tags, and add-only properties. `simulation_only=True` produces attack
conversations without evaluation results; leave it false when the service
should simulate and evaluate.

Evaluation taxonomies are managed separately:

| Method | Purpose |
| --- | --- |
| `project_client.beta.evaluation_taxonomies.create(name, taxonomy)` | Create or replace a taxonomy |
| `get(name)` | Retrieve a taxonomy |
| `list(name=..., type=...)` | List/filter taxonomies |
| `update(name, taxonomy)` | Update a taxonomy |
| `delete(name)` | Delete a taxonomy |

Use built-in risk taxonomies when they fit. Create a domain taxonomy for
regulated or business-specific harms that generic safety categories do not
capture. Taxonomy design requires policy and domain review.

An `EvaluationTaxonomy` contains an input configuration, taxonomy categories,
description, tags, and optional properties. The taxonomy API is asset-oriented;
it does not itself execute attacks or score a target.

Red-team findings are discovery signals. Confirm reproducibility, severity, and
actual policy impact before turning every generated attack into a permanent
release gate.

## Automation

### Pull-request and deployment automation

CI should:

1. validate JSONL and schemas;
2. upload or select an immutable dataset version;
3. create a uniquely named run against a stable evaluation definition;
4. poll to a terminal state with a timeout;
5. download output items and preserve the report URL;
6. compute criterion-level and aggregate gates;
7. distinguish execution errors from score failures; and
8. post a concise result to the pull request.

Avoid creating a new evaluation definition on every PR. Definitions are the
stable contract; runs represent individual changes.

### Scheduled evaluation

Use `project_client.beta.schedules` for fixed-time runs, especially stable
golden or validation datasets.

Core methods:

- `create_or_update(schedule_id, schedule)`;
- `get(schedule_id)`;
- `list(enabled=..., type=...)`;
- `delete(schedule_id)`;
- `get_run(schedule_id, run_id)`; and
- `list_runs(schedule_id, ...)`.

An evaluation schedule contains:

- a `RecurrenceTrigger` with daily, weekly, monthly, hourly, cron, or supported
  recurrence details;
- an `EvaluationScheduleTask` with the existing `eval_id`; and
- the run payload (`name`, `data_source`, and other supported run values).

Use schedules when each execution should use a fixed dataset or trace query at a
predictable cadence.

The generic schedule service also models `InsightScheduleTask` for recurring
insight generation. Keep it separate from `EvaluationScheduleTask`: one creates
evaluation runs, while the other creates analytical insight reports over
eligible data.

### Continuous evaluation rules

Use `project_client.evaluation_rules` for sampled completed agent responses.

Core methods:

- `create_or_update(id, evaluation_rule)`;
- `get(id)`;
- `list(action_type=..., agent_name=..., enabled=...)`; and
- `delete(id)`.

Evaluation rules support two action types:

- `ContinuousEvaluationRuleAction`: add sampled response-completion runs to an
  existing evaluation definition; and
- `HumanEvaluationPreviewRuleAction`: route matching events to a human
  evaluation template by `template_id` (preview and requires preview enablement
  on the client where documented).

Rule events are `responseCompleted` and `manual`. Continuous production
monitoring normally uses `responseCompleted`; manual events are useful for
explicit review workflows.

```python
from azure.ai.projects.models import (
    ContinuousEvaluationRuleAction,
    EvaluationRule,
    EvaluationRuleEventType,
    EvaluationRuleFilter,
)

rule = project_client.evaluation_rules.create_or_update(
    id="weather-agent-continuous-quality",
    evaluation_rule=EvaluationRule(
        display_name="Weather agent continuous quality",
        description="Samples completed weather-agent responses.",
        action=ContinuousEvaluationRuleAction(
            eval_id=evaluation.id,
            sampling_rate=5,
            max_hourly_runs=100,
        ),
        event_type=EvaluationRuleEventType.RESPONSE_COMPLETED,
        filter=EvaluationRuleFilter(agent_name="weather-agent"),
        enabled=True,
    ),
)
```

The rule requires an existing `eval_id`. `sampling_rate` is a percentage in
`(0, 100]`; omitted means evaluate every matching event. `max_hourly_runs`
controls cost and load.

Use rules for production monitoring, not PR regression. Assign the project
managed identity the required role and verify traffic reaches the monitored
agent.

### Rules versus schedules

| Dimension | Evaluation rule | Schedule |
| --- | --- | --- |
| Trigger | Completed matching response | Time recurrence |
| Data | Live traffic | Configured dataset or trace query |
| Sampling | Percentage and hourly cap | Dataset/run configuration |
| Best use | Production drift monitoring | Nightly regression and periodic assurance |
| User latency | Asynchronous | Asynchronous |

## Insights and comparisons

`project_client.beta.insights` creates analytical reports over evaluation runs
or agent data:

| Method | Purpose |
| --- | --- |
| `generate(insight)` | Generate an insight report |
| `get(insight_id, include_coordinates=...)` | Retrieve a report |
| `list(...)` | List/filter reports |

Supported model families include evaluation clustering, agent clustering, and
evaluation comparison. Use insights after enough runs or rows exist to form
meaningful clusters. Clustering does not replace row-level root-cause analysis.

Use the typed request matching the analysis:

- `EvaluationRunClusterInsightRequest` for one evaluation and selected run IDs;
- `AgentClusterInsightRequest` for an agent's evaluation results; or
- `EvaluationComparisonInsightRequest` to compare evaluation runs.

For simple release decisions, compare the same criteria and dataset across two
runs before introducing insight generation. Change one major variable at a time
when possible.

## Gates and statistical interpretation

Starting gates used by this repository are:

- deterministic checks: 100% passing;
- safety checks: 100% passing;
- groundedness: at least 95% passing;
- relevance: at least 90% passing;
- rubric quality: at least 85% passing; and
- no meaningful regression from the latest successful main baseline.

These are policy starting points, not universal truth. Calibrate them with
reviewed examples and business risk.

Important interpretation rules:

- A pass rate from five examples has high uncertainty; use it as a smoke signal.
- Report per-category results so common examples do not hide adversarial or
  safety failures.
- Preserve denominator and execution-error counts.
- Compare like with like: same evaluator version, model/judge version, dataset
  version, scope, and sampling method.
- LLM judges are nondeterministic. Investigate marginal changes and use human
  review around release thresholds.
- Safety-critical failures can be vetoes even when aggregate quality passes.

## Cost, latency, and reliability

Evaluation cost scales approximately with:

- number of rows or conversations;
- turns per conversation;
- number and type of evaluators;
- target inference calls;
- judge inference calls;
- simulation/red-team generation; and
- retries caused by throttling.

Control cost by:

- using deterministic checks first;
- using small PR suites and broader nightly suites;
- sampling production traffic;
- setting `max_hourly_runs` on continuous rules;
- choosing a fit-for-purpose judge model;
- avoiding duplicate semantic evaluators; and
- caching/reusing target outputs when target replay is unnecessary.

Set explicit polling timeouts in CI. A run that never reaches a terminal state
must fail as infrastructure, not hang a pipeline indefinitely.

## Failure modes and troubleshooting

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Schema validation failure | Item fields do not match `item_schema` | Validate every JSONL row and required field before upload |
| Criterion returns no score | Missing or incorrect mapping | Check `item` versus `sample` and evaluator-required fields |
| Agent evaluator tool error | Unsupported tool type or missing definitions | Check current supported-tool matrix; use frozen context or custom evaluator |
| Grounding score is meaningless | Context is absent, mutable, or unrelated | Store authoritative context and observation time with each case |
| Run remains queued/in progress | Judge/target quota or service capacity | Inspect errors, quota, retry-after, and deployment health |
| 401/403 | Caller or project identity lacks RBAC | Check Foundry and monitoring resource roles |
| Trace run finds no data | Missing semantic-convention spans or ingestion delay | Verify `invoke_agent` spans, IDs, time window, and wait for ingestion |
| Continuous charts are empty | Rule disabled, no matching traffic, or identity failure | List rules/runs and generate controlled traffic |
| Prompt judge is inconsistent | Ambiguous rubric or weak calibration | Make dimensions specific and compare against human labels |
| Synthetic set looks repetitive | Weak source/prompt or generator bias | Add grounded files, domain constraints, traces, and manual review |

## Repository implementation map

| Concern | Repository location |
| --- | --- |
| Custom evaluator CRUD and CLI | `src/evaluations/evals.py` |
| Dataset CRUD and generation jobs | `src/evaluations/datasets.py` |
| Schedule wrappers | `src/evaluations/schedules.py` |
| Insight placeholder | `src/evaluations/insights.py` |
| Weather custom evaluator definitions | `src/evaluations/weather-agent-evaluations/create_evaluation.py` |
| Evaluation lifecycle and starting gates | `docs/EVALUATION_LIFECYCLE.md` |
| Cloud and local evaluator catalog | `docs/EVALUATORS.md` and `docs/evaluations.md` |
| Data-source payload examples | `docs/DATA_SOURCE_CONFIGS.md` |
| Beta project-client inventory | `docs/FOUNDRY_BETA_API.md` |

Known repository gaps at the August 10, 2026 audit point:

- the OpenAI evaluation definition wrappers near the top of `evals.py` remain
  commented, while other modules still import `register_eval`;
- `src/evaluations/insights.py` is not implemented;
- weather `run_evaluation.py` is empty;
- red-team and taxonomy wrappers are not implemented; and
- local simulator wrappers in `evals.py` are commented.

## Recommended implementation sequence for Cosmopilot

1. Finish and run the weather custom evaluator registration script.
2. Create valid weather JSONL sets with frozen authoritative context and source
   timestamps.
3. Restore typed wrappers for OpenAI evaluation definitions and runs in
   `src/evaluations/evals.py`.
4. Create one stable weather evaluation definition referencing pinned custom
   evaluator versions.
5. Run a small manual smoke suite and inspect every output item.
6. Calibrate prompt evaluators against human scores; revise and version them.
7. Add a PR golden-dataset run and enforce criterion-specific gates.
8. Add a larger nightly schedule against the evaluation dataset.
9. Connect Application Insights and verify trace completeness.
10. Add a low-rate continuous evaluation rule with an hourly cap.
11. Add synthetic edge cases and red-team runs weekly or before release.
12. Use insights/comparison only after comparable run history exists.

## Complete API coverage checklist

Use this checklist during SDK upgrades.

### OpenAI-compatible evaluation definitions

- [x] `evals.create`
- [x] `evals.retrieve`
- [x] `evals.update`
- [x] `evals.list`
- [x] `evals.delete`
- [x] custom, logs, and deprecated stored-completions configs
- [x] Foundry `azure_ai_source` scenarios
- [x] OpenAI native graders
- [x] Foundry catalog criteria

### Evaluation runs and results

- [x] `evals.runs.create`
- [x] `evals.runs.retrieve`
- [x] `evals.runs.list`
- [x] `evals.runs.cancel`
- [x] `evals.runs.delete`
- [x] `output_items.list`
- [x] `output_items.retrieve`
- [x] statuses, report URL, aggregates, row-level results, and errors

### Run data sources

- [x] uploaded JSONL/CSV
- [x] inline file content
- [x] model target completions
- [x] agent target completions
- [x] stored response IDs
- [x] explicit trace IDs
- [x] agent-filtered traces and sampling
- [x] turn-level data
- [x] conversation-level data
- [x] synthetic query generation
- [x] conversation simulation
- [x] red-team generation
- [x] `item` and `sample` mappings

### Custom evaluator catalog

- [x] create/get/list/list-versions/update/delete
- [x] prompt-based evaluators
- [x] code-based evaluators
- [x] endpoint-based evaluators
- [x] rubric evaluators
- [x] ordinal, continuous, and boolean metrics
- [x] evaluator levels and versioning
- [x] pending artifact upload and credentials
- [x] evaluator-generation job lifecycle

### Built-in evaluator families

- [x] general quality
- [x] textual similarity
- [x] RAG and grounding
- [x] risk and safety
- [x] agent and tool behavior
- [x] conversation-level evaluators
- [x] tool-support limitations

### Data and generation

- [x] stable dataset CRUD
- [x] immutable versions
- [x] generation job lifecycle
- [x] agent, prompt, file, and trace sources
- [x] synthetic provenance and review
- [x] golden, validation, broad evaluation, and production-trace roles

### Automation and observability

- [x] local/manual evaluation
- [x] PR and merge gates
- [x] postdeployment smoke evaluation
- [x] scheduled evaluations
- [x] continuous evaluation rules
- [x] human evaluation preview rules
- [x] production trace evaluation
- [x] evaluation and insight schedule task variants
- [x] Application Insights and RBAC prerequisites
- [x] incident replay

### Advanced analysis and assurance

- [x] local Evaluation SDK
- [x] local callable evaluators
- [x] local simulators
- [x] Foundry insights
- [x] red-team resources
- [x] evaluation taxonomies
- [x] cost, latency, failure, and statistical interpretation

## References

- [Cloud evaluation with the Microsoft Foundry SDK](https://learn.microsoft.com/azure/foundry/how-to/develop/cloud-evaluation)
- [Custom evaluators](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/custom-evaluators)
- [Built-in evaluators](https://learn.microsoft.com/azure/foundry/concepts/built-in-evaluators)
- [Run evaluations from the Foundry portal](https://learn.microsoft.com/azure/foundry/how-to/evaluate-generative-ai-app)
- [Generate a synthetic evaluation dataset](https://learn.microsoft.com/azure/foundry/observability/how-to/evaluation-dataset-synthetic)
- [Monitor agents and configure continuous evaluation](https://learn.microsoft.com/azure/foundry/observability/how-to/how-to-monitor-agents-dashboard)
- [Operationalize generative AI applications learning path](https://learn.microsoft.com/training/paths/operationalize-gen-ai-apps/)
- [Azure AI Projects Python API](https://learn.microsoft.com/en-us/python/api/azure-ai-projects/azure.ai.projects?view=azure-python)
- [Azure AI Evaluation Python API](https://learn.microsoft.com/en-us/python/api/azure-ai-evaluation/azure.ai.evaluation?view=azure-python)
- [OpenAI Python eval resources](https://github.com/openai/openai-python/tree/main/src/openai/resources/evals)