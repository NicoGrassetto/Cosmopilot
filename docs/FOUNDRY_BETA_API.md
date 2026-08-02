# Microsoft Foundry `client.beta` API

`AIProjectClient.beta` exposes preview Microsoft Foundry capabilities that have
not yet moved to the stable SDK surface. These APIs can change or be removed
without notice and should not be treated as stable production contracts.

```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

client = AIProjectClient(
    endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential(),
)

schedules = client.beta.schedules
```

Using `client.beta` implies preview acceptance. It does not require
`allow_preview=True`. That constructor option controls other preview features
outside the explicitly named beta subclient.

This reference reflects the published `azure-ai-projects` API in July 2026.
Because this repository specifies `azure-ai-projects>=2.3.0` without an upper
bound, inspect the installed SDK when exact compatibility matters.

## `client.beta.agents`

Creates and manages asynchronous agent optimization jobs. Optimization jobs
produce candidate improvements for an existing agent.

| Method | Purpose |
| --- | --- |
| `create_optimization_job` | Submit an optimization job. |
| `get_optimization_job` | Retrieve a job and its current status. |
| `list_optimization_jobs` | List jobs, optionally filtered by status or agent name. |
| `cancel_optimization_job` | Request cancellation of a queued or running job. |
| `delete_optimization_job` | Delete a job and its candidate artifacts. |

## `client.beta.datasets`

Manages asynchronous data-generation jobs. These jobs create synthetic or
derived datasets for evaluation and experimentation.

| Method | Purpose |
| --- | --- |
| `create_generation_job` | Submit a data-generation job. |
| `get_generation_job` | Retrieve a job and its current status. |
| `list_generation_jobs` | List data-generation jobs. |
| `cancel_generation_job` | Cancel an in-progress job. |
| `delete_generation_job` | Delete a job and its generated output. |

This differs from stable `client.datasets`, which uploads, retrieves, lists,
and deletes ordinary versioned datasets.

## `client.beta.evaluation_taxonomies`

Manages evaluation taxonomies. A taxonomy describes the risks, behaviors, or
categories that an evaluation or red-team run should exercise.

| Method | Purpose |
| --- | --- |
| `create` | Create or replace a taxonomy. |
| `get` | Retrieve a taxonomy by name. |
| `list` | List taxonomies, optionally filtered by input name or type. |
| `update` | Update an existing taxonomy. |
| `delete` | Delete a taxonomy. |

## `client.beta.evaluators`

Manages versioned custom evaluators and asynchronous evaluator-generation
jobs. Generation jobs can derive rubric-based evaluator definitions from
source material.

| Method | Purpose |
| --- | --- |
| `create_version` | Create a new auto-versioned evaluator definition. |
| `get_version` | Retrieve one evaluator version. |
| `list` | List the latest built-in or custom evaluator versions. |
| `list_versions` | List all versions of a named evaluator. |
| `update_version` | Update a specific evaluator version. |
| `delete_version` | Delete a specific evaluator version. |
| `pending_upload` | Start or retrieve an evaluator artifact upload. |
| `get_credentials` | Get temporary storage credentials for evaluator artifacts. |
| `create_generation_job` | Generate an evaluator from source material. |
| `get_generation_job` | Retrieve an evaluator-generation job. |
| `list_generation_jobs` | List evaluator-generation jobs. |
| `cancel_generation_job` | Cancel an evaluator-generation job. |
| `delete_generation_job` | Delete the job record without deleting its generated evaluator. |

Evaluation definitions and runs themselves remain on the OpenAI client:

```python
openai_client = client.get_openai_client()
evaluation = openai_client.evals.create(...)
run = openai_client.evals.runs.create(eval_id=evaluation.id, ...)
```

## `client.beta.insights`

Generates and retrieves analytical reports over evaluation runs or agent data.
Insight types include evaluation clustering, agent clustering, and evaluation
comparison.

| Method | Purpose |
| --- | --- |
| `generate` | Generate an insight report. |
| `get` | Retrieve one insight report. |
| `list` | List reports, optionally filtered by type, evaluation, run, or agent. |

## `client.beta.memory_stores`

Manages persistent agent memory stores and their memory items. A `scope`, such
as a user ID, isolates memories belonging to different users or sessions.

| Method | Purpose |
| --- | --- |
| `create` | Create a memory store. |
| `get` | Retrieve a memory store. |
| `list` | List memory stores. |
| `update` | Update store metadata or description. |
| `delete` | Delete a memory store. |
| `create_memory` | Add an explicit memory item. |
| `get_memory` | Retrieve one memory item. |
| `list_memories` | List memories within a scope. |
| `update_memory` | Change a memory item's content. |
| `delete_memory` | Delete one memory item. |
| `delete_scope` | Delete every memory associated with a scope. |
| `search_memories` | Find relevant memories from conversation context. |
| `begin_update_memories` | Asynchronously extract and store memories from messages. |

Memory item kinds currently include `user_profile`, `chat_summary`, and
`procedural`.

## `client.beta.models`

Registers and manages custom model weight assets. This is model asset storage,
not the stable deployment-listing API at `client.deployments`.

| Method | Purpose |
| --- | --- |
| `create` | Upload local weights with AzCopy and register the model version. |
| `get` | Retrieve a model version. |
| `list` | List the latest version of each model. |
| `list_versions` | List every version of a model. |
| `update` | Update model version metadata. |
| `delete` | Delete a model version. |
| `pending_upload` | Provision storage and obtain an upload URI. |
| `pending_create_version` | Finalize model registration asynchronously. |
| `get_credentials` | Get temporary credentials for model storage. |

The convenience `create` method performs the pending upload, AzCopy transfer,
and registration sequence. AzCopy must be installed or supplied explicitly.

## `client.beta.red_teams`

Starts and retrieves red-team runs that probe a target for safety and security
risks.

| Method | Purpose |
| --- | --- |
| `create` | Submit a red-team run. |
| `get` | Retrieve one run and its configuration. |
| `list` | List red-team runs in the project. |

## `client.beta.routines`

Manages reusable triggered automations. A routine combines a trigger with an
action and records asynchronous dispatch runs.

| Method | Purpose |
| --- | --- |
| `create_or_update` | Create or replace a routine definition. |
| `get` | Retrieve a routine. |
| `list` | List routines. |
| `enable` | Enable dispatch for a routine. |
| `disable` | Prevent a routine from running. |
| `dispatch` | Manually queue a routine run, optionally overriding its input. |
| `list_runs` | List prior runs for a routine. |
| `delete` | Delete a routine. |

## `client.beta.schedules`

Manages recurring evaluation and insight tasks. A schedule contains a trigger
and a task payload. For evaluation schedules, that payload references a
registered evaluation and contains the same run configuration passed to
`openai_client.evals.runs.create()`.

| Method | Purpose |
| --- | --- |
| `create_or_update` | Create or replace a schedule. |
| `get` | Retrieve a schedule. |
| `list` | List schedules, optionally filtered by task type or enabled state. |
| `delete` | Delete a schedule. |
| `get_run` | Retrieve one execution of a schedule. |
| `list_runs` | List executions of a schedule. |

```python
from azure.ai.projects.models import (
    DailyRecurrenceSchedule,
    EvaluationScheduleTask,
    RecurrenceTrigger,
    Schedule,
)

client.beta.schedules.create_or_update(
    schedule_id="daily-evaluation",
    schedule=Schedule(
        display_name="Daily evaluation",
        enabled=True,
        trigger=RecurrenceTrigger(
            interval=1,
            schedule=DailyRecurrenceSchedule(hours=[9]),
        ),
        task=EvaluationScheduleTask(eval_id=eval_id, eval_run=eval_run),
    ),
)
```

The project managed identity needs sufficient access to execute the scheduled
task, normally the **Foundry User** role on the project.

## `client.beta.skills`

Manages versioned Foundry Agent Skills. A skill packages reusable instructions
and supporting files that can be attached to agents.

| Method | Purpose |
| --- | --- |
| `create` | Create a skill version from inline content. |
| `create_from_files` | Create a skill version from uploaded files. |
| `get` | Retrieve a skill and its default version information. |
| `list` | List project skills. |
| `update` | Change a skill's default version. |
| `delete` | Delete a skill and all versions. |
| `get_version` | Retrieve one skill version. |
| `list_versions` | List versions of a skill. |
| `delete_version` | Delete one skill version. |
| `download` | Download the default version as a zip stream. |
| `download_version` | Download a specific version as a zip stream. |

## Stability guidance

- Pin `azure-ai-projects` when beta API compatibility matters.
- Isolate beta calls behind small project helpers.
- Expect model names, request shapes, and return types to change.
- Do not assume a beta feature has a production service-level agreement.
- Validate permissions for the project managed identity when work runs without
  the developer's interactive credential, especially schedules and continuous
  evaluation.

## References

- [AIProjectClient API](https://learn.microsoft.com/python/api/azure-ai-projects/azure.ai.projects.aiprojectclient)
- [BetaOperations API](https://learn.microsoft.com/python/api/azure-ai-projects/azure.ai.projects.operations.betaoperations)
- [Azure AI Projects Python samples](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/ai/azure-ai-projects/samples)