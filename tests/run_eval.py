"""Trigger an evaluation run against a Cosmopilot eval defined in Foundry.

This picks the most recent ``cosmopilot-text_similarity`` eval (created by
``src/main.py``) and starts a *completions* run: the model answers each question
in the dataset, then the text-similarity graders score those answers against the
reference ``answer``.

Auth is via DefaultAzureCredential. Required environment variables:
  AZURE_AI_PROJECT_ENDPOINT   the Foundry project endpoint
  AZURE_DEPLOYMENT_NAME       the chat model deployment used to generate answers
"""

import csv
import os
import time

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

EVAL_NAME = "cosmopilot-text_similarity"
DATASET_CSV = os.path.join(os.path.dirname(__file__), "..", "data", "datasets", "eval_dataset.csv")


def load_items():
    with open(DATASET_CSV, newline="") as f:
        return [{"item": row} for row in csv.DictReader(f)]


def main():
    endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
    model = os.environ.get("AZURE_DEPLOYMENT_NAME", "gpt-4o-mini")

    client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())
    openai_client = client.get_openai_client()

    # Find the most recently created eval with the target name.
    evals = [e for e in openai_client.evals.list() if e.name == EVAL_NAME]
    if not evals:
        raise SystemExit(f"No eval named {EVAL_NAME!r} found. Run src/main.py first.")
    eval_id = sorted(evals, key=lambda e: e.created_at, reverse=True)[0].id
    print(f"Using eval {EVAL_NAME} -> {eval_id}")

    items = load_items()
    print(f"Loaded {len(items)} dataset items")

    run = openai_client.evals.runs.create(
        eval_id=eval_id,
        name="cosmopilot-text_similarity-run",
        data_source={
            "type": "completions",
            "model": model,
            "input_messages": {
                "type": "template",
                "template": [
                    {
                        "role": "developer",
                        "content": (
                            "You are Cosmopilot, an assistant for Azure Cosmos DB "
                            "operations. Answer the user's question concisely."
                        ),
                    },
                    {"role": "user", "content": "{{item.question}}"},
                ],
            },
            "source": {"type": "file_content", "content": items},
        },
    )
    print(f"Started run {run.id} (status: {run.status})")

    # Poll until the run finishes.
    terminal = {"completed", "failed", "canceled", "cancelled"}
    while run.status not in terminal:
        time.sleep(5)
        run = openai_client.evals.runs.retrieve(run.id, eval_id=eval_id)
        print(f"  status: {run.status}")

    print(f"\nFinal status: {run.status}")
    if getattr(run, "result_counts", None):
        print(f"Result counts: {run.result_counts}")
    if getattr(run, "report_url", None):
        print(f"Report: {run.report_url}")


if __name__ == "__main__":
    main()
