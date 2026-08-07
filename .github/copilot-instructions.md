# Cosmopilot Repository Guidelines

## Project Scope

- Cosmopilot is an exploration and validation demo for Microsoft Foundry GA and preview capabilities.
- `azure.yaml` is infrastructure-only. `azd up` provisions Azure resources; it does not deploy application code.
- Keep changes focused on the existing agents, skills, toolboxes, evaluations, datasets, documentation, and Bicep infrastructure. Do not add application hosting targets unless explicitly requested.

## Python Environment

- Use Python 3.10 or newer; Python 3.12 is the recommended development version.
- Use the repository-root `.venv` and install dependencies with `python -m pip install -r requirements.txt`.
- Dependencies are deliberately pinned. Update `requirements.txt` when a direct import or SDK contract changes, and validate the complete resolution before finishing.
- The source tree is not installed as a package. Set `PYTHONPATH=src` when running tests or modules that import `agents`, `evaluations`, `skills`, or `toolboxes`.
- Prefer the Python standard library for common functionality such as logging rather than adding framework dependencies.

## Microsoft Foundry

- Use `azure-ai-projects==2.4.0`. The stable package includes preview features; do not replace it with the legacy 1.x SDK or add `azure-ai-agents`.
- Calls through `client.beta.*` already opt into preview behavior. For preview features exposed through stable clients, construct `AIProjectClient` with `allow_preview=True`.
- Preview APIs can change between SDK releases. Preserve the repository's current typed models and method names, and update tests and relevant docs when changing an SDK version.
- Authentication uses `DefaultAzureCredential`. Local development expects an Azure CLI login via `az login` or `azd auth login`.
- Most Python modules read `os.environ` directly and do not automatically load `.env`. Run Azure-dependent commands with `azd exec -- ...` or export the selected azd environment values first.
- Never commit credentials or real endpoint values. Use `.env.example` only as a variable reference.

## Infrastructure

- Make infrastructure changes in `infra/*.bicep`; preserve the subscription-scoped entry point in `infra/main.bicep`.
- The primary Foundry region is intentionally constrained to East US 2. Azure AI Search uses a separately selected region.
- Preserve the infrastructure-only `azure.yaml` shape unless the task explicitly changes the deployment model.

## Tests

- Run tests from the repository root with `PYTHONPATH=src python -m pytest`.
- Tests marked `integration` call live Azure services, create resources, can incur cost, and require a configured azd environment. Prefer narrow collection or unit checks unless live integration coverage is explicitly needed.
- Run live integration tests with the azd environment injected, for example: `azd exec -- env PYTHONPATH=src python -m pytest -m integration`.
- Do not weaken cleanup assertions or silently skip service failures to make integration tests pass.

## Change Discipline

- Preserve local formatting and public APIs; the current Python files contain both tab- and space-indented sections.
- Avoid unrelated refactors, generated-file churn, or changes to scenario data while addressing a focused task.
- Treat prompts, `SKILL.md` files, and evaluation datasets as behavioral contracts, not incidental text.