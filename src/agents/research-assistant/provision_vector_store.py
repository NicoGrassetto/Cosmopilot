"""Post-provision helper: create a vector store with demo documents for file_search.

Creates a Foundry/OpenAI vector store, uploads a few small fake text documents so the
research-assistant's file_search tool has something to search, waits until the files
are processed, and prints the vector store id.

Env vars:
    AZURE_AI_PROJECT_ENDPOINT   Foundry project endpoint (required)
    VECTOR_STORE_NAME           Optional name for the vector store (default: research-demo-docs)

Output:
    Prints "FILE_SEARCH_VECTOR_STORE_ID=<id>" on the last line (easy for shells to capture).

Auth: DefaultAzureCredential (run `az login` first).
"""

import os
import sys
import tempfile
import time
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

VECTOR_STORE_NAME = os.environ.get("VECTOR_STORE_NAME", "research-demo-docs")

# Fake demo documents. Purely illustrative content so file_search returns hits.
DEMO_DOCS = {
    "acme-quarterly-report.txt": (
        "ACME Corp Q3 FY2026 internal summary.\n"
        "Revenue reached 42.5M USD, up 18% year over year, driven by the CosmoWidget line.\n"
        "Gross margin held at 61%. Cloud infrastructure costs fell 7% after the Cosmos DB migration.\n"
        "Leadership set a Q4 target of 50M USD and approved hiring 30 engineers.\n"
    ),
    "product-faq.txt": (
        "CosmoWidget product FAQ.\n"
        "Q: What regions are supported? A: East US, West Europe, UK South, and Sweden Central.\n"
        "Q: What is the default data consistency? A: Session consistency.\n"
        "Q: Is there a free tier? A: No, the free tier is disabled for production accounts.\n"
    ),
    "engineering-runbook.txt": (
        "CosmoWidget on-call runbook.\n"
        "If request units are throttled (HTTP 429), raise container throughput above 400 RU/s.\n"
        "The partition key is /tenantId; hot partitions usually indicate a skewed tenant.\n"
        "Escalate paging incidents to the platform team after 15 minutes without recovery.\n"
    ),
}


def main() -> None:
    endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]

    project = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())
    openai_client = project.get_openai_client()

    file_ids = []
    with tempfile.TemporaryDirectory() as tmp:
        for name, content in DEMO_DOCS.items():
            path = Path(tmp) / name
            path.write_text(content, encoding="utf-8")
            with path.open("rb") as fh:
                uploaded = openai_client.files.create(file=fh, purpose="assistants")
            file_ids.append(uploaded.id)
            print(f"Uploaded {name} -> {uploaded.id}", file=sys.stderr)

    vector_store = openai_client.vector_stores.create(
        name=VECTOR_STORE_NAME,
        file_ids=file_ids,
    )
    print(f"Created vector store {vector_store.id}", file=sys.stderr)

    # Wait for files to finish embedding.
    for _ in range(60):
        vs = openai_client.vector_stores.retrieve(vector_store.id)
        counts = vs.file_counts
        print(
            f"  status={vs.status} completed={counts.completed} "
            f"in_progress={counts.in_progress} failed={counts.failed}",
            file=sys.stderr,
        )
        if counts.in_progress == 0:
            break
        time.sleep(2)

    # Last stdout line is easy to capture from a shell.
    print(f"FILE_SEARCH_VECTOR_STORE_ID={vector_store.id}")


if __name__ == "__main__":
    main()
