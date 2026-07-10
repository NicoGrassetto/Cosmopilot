"""Post-provision helper: create the Foundry memory store for memory_search.

Memory stores are a Foundry data-plane resource (not deployable via Bicep/ARM),
so this script creates one through the preview Projects API so the
knowledge-assistant's ``memory_search_preview`` tool has a store to read/write.
Idempotent: an already-existing store is treated as success.

Env vars:
    AZURE_AI_PROJECT_ENDPOINT   Foundry project endpoint (required)
    MEMORY_STORE_NAME           Memory store name (default: knowledge-memory)
    MEMORY_CHAT_MODEL           Chat model deployment (default: gpt-4-1-nano)
    MEMORY_EMBEDDING_MODEL      Embedding deployment (default: text-embedding-ada-002)

Output:
    Prints "MEMORY_STORE_NAME=<name>" on the last line (easy for shells to capture).

Auth: DefaultAzureCredential (run `az login` first).
"""

import os
import sys

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import MemoryStoreDefaultDefinition
from azure.core.exceptions import ResourceExistsError
from azure.identity import DefaultAzureCredential

MEMORY_STORE_NAME = os.environ.get("MEMORY_STORE_NAME", "knowledge-memory")
CHAT_MODEL = os.environ.get("MEMORY_CHAT_MODEL", "gpt-4-1-nano")
EMBEDDING_MODEL = os.environ.get("MEMORY_EMBEDDING_MODEL", "text-embedding-ada-002")


def main() -> None:
    endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]

    # Memory stores live on the preview (beta) surface of the Projects API.
    project = AIProjectClient(
        endpoint=endpoint,
        credential=DefaultAzureCredential(),
        allow_preview=True,
    )

    definition = MemoryStoreDefaultDefinition(
        chat_model=CHAT_MODEL,
        embedding_model=EMBEDDING_MODEL,
    )

    try:
        store = project.beta.memory_stores.create(
            name=MEMORY_STORE_NAME,
            definition=definition,
            description="Enterprise memory store for the knowledge-assistant demo.",
        )
        print(f"Created memory store '{getattr(store, 'name', MEMORY_STORE_NAME)}'", file=sys.stderr)
    except ResourceExistsError:
        print(f"Memory store '{MEMORY_STORE_NAME}' already exists; reusing it.", file=sys.stderr)

    # Last stdout line is easy to capture from a shell.
    print(f"MEMORY_STORE_NAME={MEMORY_STORE_NAME}")


if __name__ == "__main__":
    main()
