# Will my evals show up in the Azure AI Foundry experience?

**Short answer: by design yes, but not with the current setup.**

The `evaluations/` framework is wired to surface results in Foundry — `runner.py`
passes `azure_ai_project` to `azure.ai.evaluation.evaluate()`, which uploads each
run to **Foundry portal → your project → Evaluation tab**. The `safety` suite
additionally runs on Foundry's cloud RAI (Responsible AI) service. So results are
*meant* to appear there, not just in the local `results/` folder.

However, nothing will appear yet because of gaps between the eval config and what
is actually deployed by `infra/`.

## How results reach Foundry

- `runner.py` builds an `eval_kwargs` dict that always includes
  `azure_ai_project` and calls `evaluate(**eval_kwargs)`.
- When `evaluate()` receives `azure_ai_project`, the Azure AI Evaluation SDK
  uploads the run (scores, dataset, per-row results, logs) to the Foundry
  project. It then shows under **Foundry Portal → \<project\> → Evaluation**.
- Safety evaluators (`safety_suite`) don't use the local judge model — they call
  the Foundry-hosted RAI evaluation service, which also records to the project.

## Gaps that block results from showing today

1. **Nothing is configured or has run.** `config/model_config.yaml` and
   `config/project_config.yaml` are entirely env-var placeholders:
   `AZURE_AI_PROJECT_ENDPOINT`, `AZURE_SUBSCRIPTION_ID`, `AZURE_RESOURCE_GROUP`,
   `AZURE_AI_PROJECT_NAME`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`,
   `AZURE_OPENAI_DEPLOYMENT`. None are set, so no evaluation has executed.

2. **Project-type mismatch.** `project_config.yaml` uses the **dict form**
   (`subscription_id` + `resource_group_name` + `project_name`), which
   historically targets **legacy hub-based** projects (old Azure AI Studio / ML
   workspace). The deployed infra (`infra/main.bicep`) is a **new hub-less
   Foundry project** (`Microsoft.CognitiveServices/accounts` kind `AIServices`
   + `.../projects`). For the new experience you generally point
   `azure_ai_project` at the **project endpoint URL** — note the commented-out
   `azure_ai_project_url` hint in `project_config.yaml`. Depending on the
   installed `azure-ai-evaluation` version, the dict form may target the legacy
   experience or not surface in the new portal.

3. **Judge model mismatch.** The judge config expects a `gpt-4o` deployment
   (`AZURE_OPENAI_DEPLOYMENT`), but the deployed models are `gpt-4.1-nano`
   (deployment name `gpt-4-1-nano`) + `text-embedding-ada-002`. The judge
   deployment name must match a real deployment.

4. **No agent deployed.** `agents/foundry_agent.py` (`FoundryAgentTarget`) calls
   an agent by name (e.g. `adventure-works`) via `agent_reference`. No agent
   exists in the project, so **live-target runs fail**. Only offline runs with an
   explicit `--dataset` work today (that path skips the live agent).

5. **`results/` is local + gitignored.** The JSON written to
   `evaluations/results/` is independent of the portal upload.

## What was actually deployed (reference)

Deployed to resource group `cosmopilot-rg` in `swedencentral`:

| Thing | Value |
| --- | --- |
| Foundry account + project | `cosmopilot-37zj5tc2b3xym` |
| Chat model deployment | `gpt-4-1-nano` (model `gpt-4.1-nano`) |
| Embedding deployment | `text-embedding-ada-002` |
| Cosmos DB account | `cosmopilot-db-vzpog8` |
| Cosmos DB / container | `cosmopilot` / `conversations` (pk `/tenantId`, 400 RU/s) |

Likely project endpoint (verify in the portal / `az`):

```
https://cosmopilot-37zj5tc2b3xym.services.ai.azure.com/api/projects/cosmopilot-37zj5tc2b3xym
```

## To actually see evals in the Foundry Evaluation tab

1. Point config at the deployed project — prefer the **project endpoint URL**
   form for the new Foundry experience (uncomment/use `azure_ai_project_url`, or
   set the env vars to the deployed project's subscription/RG/name).
2. Set the judge deployment to an existing deployment (`gpt-4-1-nano`) or deploy
   a `gpt-4o`/`gpt-4o-mini` judge and set `AZURE_OPENAI_DEPLOYMENT` accordingly.
3. Set `AZURE_SUBSCRIPTION_ID`, `AZURE_RESOURCE_GROUP` (`cosmopilot-rg`),
   `AZURE_AI_PROJECT_NAME`, and `AZURE_AI_PROJECT_ENDPOINT`.
4. Run an **offline** (dataset-only) suite first, since no agent is deployed:

   ```bash
   cd evaluations
   pip install -e .
   python runner.py --agent adventure-works --suites quality,safety \
     --dataset datasets/per_agent/adventure-works.jsonl
   ```

5. Open **Foundry Portal → cosmopilot project → Evaluation** to view the run.
6. (Later) Deploy an agent so `FoundryAgentTarget` live-target runs work without
   `--dataset`.
