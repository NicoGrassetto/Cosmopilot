import os

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

from evals import register_evals, run_builtin_evaluations


def main():
    endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
    model = os.environ.get("AZURE_DEPLOYMENT_NAME", "gpt-4o-mini")
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")

    credential = DefaultAzureCredential()
    client = AIProjectClient(endpoint=endpoint, credential=credential)
    openai_client = client.get_openai_client()

    # Register (create) the reusable OpenAI-graded evals in the Foundry project.
    register_evals(openai_client, model)

    # Run the ready-made azure-ai-evaluation built-in evaluators over the dataset.
    run_builtin_evaluations(credential, model, endpoint, data_dir)


if __name__ == "__main__":
    main()
