---
name: azure-ai-projects-notebooks
description: "Use when creating or editing any notebook under notebooks/. Defines the notebook template for one azure-ai-projects client module: a single McKinsey-style title followed by the module name, a version-pinned API reference link, a first code cell of imports and environment variables, then one subtitled section per public method whose cell passes every signature parameter with an inline comment."
---

# azure-ai-projects notebooks

Every notebook under `notebooks/` walks through one `azure-ai-projects` client
module, such as `client.agents` or `client.beta.memory_stores`, and can be run
top to bottom. It has one section per public method. Each section's call passes
every parameter, and a short comment explains each one, so running the notebook
covers the module's whole public surface.

## Start from the inventory

The installed package, pinned in `requirements.txt`, is the source of truth for
the method list, the signatures, and the links. Print them before writing a
cell:

```bash
python .github/skills/azure-ai-projects-notebooks/scripts/notebook.py inventory client.agents
```

The inventory prints the file name, the notebook metadata, and the link line
for the pinned version. It says whether cell 2 needs `allow_preview=True`, and
lists every public method with the exact parameters its section must pass. Each
parameter comes with the SDK's own description. The script refuses to run when
the installed version differs from the pin.
[`docs/azure-ai-projects.md`](../../../docs/azure-ai-projects.md) summarizes
the same surface; where the two disagree, the package wins.

## Layout

A notebook contains these cells, in this order, and nothing else:

| Cell | Type | Content |
| --- | --- | --- |
| 1 | Markdown | The title, then the API reference and version links |
| 2 | Code | Imports, environment variables, and the client |
| 3, 5, 7, … | Markdown | `` ## `<method>` `` and one sentence on what the call does |
| 4, 6, 8, … | Code | One call to that method, passing every parameter with an inline comment |

Write one notebook per module. A module is a client namespace with public
methods of its own. Containers such as `client.beta` and
`client.beta.voice_agents` don't get a notebook; each of their children gets
one. Name the file after the module: drop the `client.` prefix and replace `.`
and `_` with `-`. For example, `client.agents` becomes `notebooks/agents.ipynb`
and `client.beta.memory_stores` becomes `notebooks/beta-memory-stores.ipynb`.

Some notebooks were written before this template existed. A small fix to one of
them doesn't require a rewrite. When a task does rebuild one, follow this
layout, use the new file name, and update the notebook's link in the docs.

## Cell 1: title and links

```markdown
# Agents are named, versioned definitions that apps invoke by name: `client.agents`

**API reference:** [`AgentsOperations`](https://learn.microsoft.com/en-us/python/api/azure-ai-projects/azure.ai.projects.operations.agentsoperations?view=azure-python) · **Version:** [`azure-ai-projects==2.7.0`](https://github.com/Azure/azure-sdk-for-python/blob/azure-ai-projects_2.7.0/sdk/ai/azure-ai-projects/azure/ai/projects/operations/_patch_agents.py#L54)
```

The title is the notebook's only `#` heading, written as
`` # <action title>: `<module>` ``.

Write the action title the way McKinsey writes slide titles. The headline
states the takeaway, so a reader who reads nothing else still gets the point.

- Write one complete sentence of 5–15 words. It says what the module lets the
  reader do, or why that matters. It makes a claim; it isn't a topic label.
- Use active voice, present tense, and sentence case, with no closing
  punctuation.
- Keep it specific to this module and true for the pinned version. Avoid filler
  such as "powerful" or "seamless".

| Module | Topic label, rejected | Action title, accepted |
| --- | --- | --- |
| `client.agents` | Agents | Agents are named, versioned definitions that apps invoke by name |
| `client.deployments` | Deployments overview | Deployments name the models your project can call |
| `client.beta.memory_stores` | Working with memory stores | Memory stores let agents remember users across conversations |

The line under the title has exactly two links. Copy it from the inventory
rather than typing it.

- **API reference** links to the Microsoft Learn page for the operations class
  behind the module. Learn serves only the latest release in each channel, so
  the link picks the channel that matches the pin. That channel is
  `view=azure-python` for a GA release and `view=azure-python-preview` for a
  pre-release such as `2.8.0b1`.
- **Version** links to the class's source at the `azure-ai-projects_<version>`
  release tag. This link pins the exact API the notebook was written against.
  Its text is the pin from `requirements.txt`.

When the pin in `requirements.txt` changes, rerun the inventory. Then update
both links, the metadata, and every section whose signature changed.

## Cell 2: imports, environment variables, and the client

```python
import os
from uuid import uuid4

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from azure.identity import DefaultAzureCredential

PROJECT_ENDPOINT = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
MODEL_DEPLOYMENT_NAME = os.environ["AZURE_DEPLOYMENT_NAME"]

AGENT_NAME = f"notebook-agent-{uuid4().hex[:8]}"

credential = DefaultAzureCredential()
client = AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=credential, allow_preview=True)
```

This is the notebook's first code cell. It holds, in order:

1. **Imports.** Put every import the notebook uses here and nowhere else.
   Standard library imports come first, then third-party imports, as separate
   groups. Don't add `%pip` or `!` lines; the kernel is the repository `.venv`
   with `requirements.txt` installed.
2. **Environment variables.** Read every setting the notebook needs into an
   UPPER_CASE constant with `os.environ["NAME"]`. A missing value then fails
   here, before anything is created. Use the names the repository already
   uses, `AZURE_AI_PROJECT_ENDPOINT` and `AZURE_DEPLOYMENT_NAME`, and add any
   new name to `.env.example`. Never hard-code endpoints, keys, or IDs.
3. **Names** for the resources the notebook creates, unique per run:
   `f"notebook-<kind>-{uuid4().hex[:8]}"`. The prefix makes leftovers from an
   interrupted run easy to find.
4. **The client.** Create one `DefaultAzureCredential` and one synchronous
   `AIProjectClient`. Every section shares them, and they stay open for the
   kernel's lifetime. Constructing them sends no request. Pass
   `allow_preview=True` when the inventory reports preview parameters on a
   stable module. Modules under `client.beta.*` already opt in and don't need
   it.

## Sections: one per public method

````markdown
## `create_version`

Saves a new version of the agent's definition; the first call also creates the agent.
````

```python
agent_version = client.agents.create_version(
    agent_name=AGENT_NAME,  # Unique agent name; the first version creates the agent
    definition=PromptAgentDefinition(  # What the agent is: a prompt agent's model and instructions
        model=MODEL_DEPLOYMENT_NAME,
        instructions="Answer in one short sentence.",
    ),
    content_type="application/json",  # Media type of the request body; keep the default
    metadata={"source": "notebook"},  # Up to 16 key-value pairs for your own bookkeeping
    description="Created by the client.agents notebook",  # Human-readable description of the agent
    blueprint_reference=None,  # Agent identity blueprint to reference; None skips it
    draft=None,  # Preview: True saves a draft that "latest" resolution skips
)
print(agent_version.name, agent_version.version)
```

1. The heading is exactly `` ## `<method>` ``, using the SDK method name
   verbatim. One sentence follows it: what the call does, plus anything the
   reader must know before running it. Examples: the method is in preview or
   billable, it needs a prerequisite, or it creates something the module can't
   delete.
2. The code cell calls the method once, through its full path
   `client.<module>.<method>(...)`. It passes every parameter of the signature
   the inventory prints:
   - by keyword, one per line, in signature order, including optional
     parameters and `content_type`;
   - each with a short inline comment on the line where the parameter starts,
     saying what it does. Base the comment on the SDK description the inventory
     prints, and keep it to one clause.

   `self` and `**kwargs` aren't parameters; don't show them.
3. Generated methods have overloads that take either typed keywords or a raw
   JSON/bytes `body`. Show the typed overload, which the inventory has already
   chosen, and never pass `body`.
4. Use realistic values that are safe to send. Sometimes a real value would
   change behavior (`force=True`) or needs something the project doesn't have.
   Then pass the default, and let the comment say what a real value does.
   "Every parameter" means every parameter of the method. When a parameter
   takes a model, as in `definition=PromptAgentDefinition(...)`, set only the
   model fields the example needs.
5. Keep the result display short. Assign the result to a descriptive variable
   and print one or two identifying fields.
   - Iterate `ItemPaged` results.
   - Call `.result()` on the poller that a `begin_*` method returns.
   - Consume `Iterator[bytes]` with `b"".join(...)` and print its length.
   - A method that returns `None` needs no print.
6. Reuse earlier results through their variables: write
   `agent_version.version`, not a hard-coded `"1"`.
7. Never print secrets: credentials, keys, tokens, SAS URLs, or connection
   strings. Sources include `include_credentials=True`, `get_credentials`, and
   `get_application_insights_connection_string`. Print a non-secret field
   instead.
8. Don't use `try`/`except`, retries, or flags that hide a failing call. A cell
   either works or fails loudly.

The remaining sections follow the same pattern. A method with one parameter
still puts it on its own line:

````markdown
## `get`

Retrieves the agent, including its latest version.
````

```python
agent = client.agents.get(
    agent_name=AGENT_NAME,  # Agent to retrieve
)
print(agent.name, agent.versions.latest.version)
```

````markdown
## `list`

Pages through the project's prompt agents, newest first.
````

```python
agents = client.agents.list(
    kind="prompt",  # Only this kind: prompt, hosted, workflow, external, or voice
    limit=20,  # Agents per page, from 1 to 100
    order="desc",  # Sort by creation time: "asc" or "desc"
    before=None,  # Cursor: only agents listed before this agent ID
)
for agent in agents:  # ItemPaged fetches further pages as the loop advances
    print(agent.name)
```

````markdown
## `delete`

Deletes the agent and all of its versions, so it runs last and leaves nothing behind.
````

```python
deleted_agent = client.agents.delete(
    agent_name=AGENT_NAME,  # Agent to delete, with every version
    force=None,  # Hosted agents: True deletes even when sessions are active
)
print(deleted_agent.name, deleted_agent.deleted)
```

### Order and prerequisites

- Order the sections so Run All works top to bottom and leaves nothing behind.
  Creates come first, then reads, lists, and other actions, then updates.
  Deletes come last, children before parents: `delete_version` runs before
  `delete`.
- A notebook creates only what its own module creates. Anything else it needs
  comes from the project fixtures that the weekly workflow guarantees: the
  `aisearch` connection, the `weather-agent`, and the deployment named by
  `AZURE_DEPLOYMENT_NAME`. Otherwise it comes from an environment variable read
  in cell 2.
- Some methods need something the demo project lacks, such as a running
  hosted-agent session or a provisioned phone number. Their sections still show
  the full call. Read the identifier from an environment variable in cell 2,
  and name the prerequisite in the section's sentence.

## File format

- Use nbformat 4.5, with a unique `id` on every cell.
- The notebook metadata records the pinned version and the module, in the
  shape the inventory prints:

  ```json
  "metadata": {
    "cosmopilot": {"sdk_version": "2.7.0", "modules": ["client.agents"]},
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"}
  }
  ```

- Commit with outputs cleared: every code cell has `"outputs": []` and
  `"execution_count": null`. Outputs carry endpoints, resource IDs, and
  sometimes secrets.
- Link the notebook from its module's section of
  [`docs/azure-ai-projects.md`](../../../docs/azure-ai-projects.md), under the
  API reference link: `[Demo notebook](../notebooks/<file>.ipynb).`

## Check, then run

```bash
python .github/skills/azure-ai-projects-notebooks/scripts/notebook.py check notebooks/agents.ipynb
```

The check enforces the structural rules:

- the title's format and word count, the exact links for the pinned version,
  and a single `#` heading;
- cell 2's imports, its single client, `allow_preview`, and environment
  variable names that are listed in `.env.example`;
- one section per public method, with every parameter passed by keyword, on
  its own line, in signature order, with a comment;
- the metadata, the file name, and cleared outputs.

It can't judge whether the title makes a real claim or whether a comment is
accurate, so review those yourself.

Then run the notebook. Open it in VS Code with the repository `.venv` as the
kernel. Put the cell 2 variables in the gitignored `.env` at the repository
root, for example from `azd env get-values`; VS Code loads that file into
notebook kernels. Then choose Run All. Running creates and deletes real
resources in the Foundry project and can incur cost. Clear all outputs before
committing.
