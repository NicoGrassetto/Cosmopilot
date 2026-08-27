# Weekly Test GitHub Action

The workflow in [`.github/workflows/weekly-tests.yml`](../.github/workflows/weekly-tests.yml) runs every test under `tests/` each Sunday at 00:00 UTC. It can also be started manually from the GitHub Actions page.

## GitHub configuration

Open **Settings > Secrets and variables > Actions** in the GitHub repository.

Add or confirm these repository secrets:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`

Add this repository variable:

- `AZURE_ENV_NAME`: the azd environment name, such as `demo` when the Azure resource group is named `rg-demo`. Do not include the `rg-` prefix.

The workflow does not require GitHub variables for `AZURE_AI_PROJECT_ENDPOINT` or `AZURE_DEPLOYMENT_NAME`. After signing in to Azure, it reads both values from the `cosmopilot-resources` deployment in `rg-${AZURE_ENV_NAME}` and exports them for the test process.

## Azure configuration

The identity identified by `AZURE_CLIENT_ID` must have:

- A federated GitHub Actions credential for this repository and branch or environment.
- Permission to read the `cosmopilot-resources` deployment.
- Permission to create, read, update, and delete the Foundry resources exercised by the integration tests.

The selected Foundry project must already contain:

- The `aisearch` connection used by the index tests.
- The `weather-agent` used by the routine tests.
- The model deployment emitted by the infrastructure as `AZURE_DEPLOYMENT_NAME`.

Use a dedicated non-production Foundry project because the integration tests modify remote resources and can incur Azure charges. The red-team tests currently create remote resources without deleting them.

## First run

1. Commit and push the workflow to the repository's default branch. GitHub only runs scheduled workflows from the default branch.
2. Open **Actions > Weekly tests > Run workflow**.
3. Leave `azure-environment` empty to use the `AZURE_ENV_NAME` repository variable, or enter an azd environment name to override it for that manual run.
4. Confirm that Azure OIDC login succeeds and that both unit and integration tests run.

Scheduled runs use the cron expression `0 0 * * 0`. GitHub interprets schedules in UTC and may start a run a few minutes late during periods of high load.

## Related workflow

The separate [dataset upload workflow](../.github/workflows/upload-dataset.yml) still reads `AZURE_AI_PROJECT_ENDPOINT` directly from a GitHub repository variable. Its configuration is independent from the weekly test workflow.