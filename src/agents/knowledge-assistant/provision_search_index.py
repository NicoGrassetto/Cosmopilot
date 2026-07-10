"""Post-provision helper: create the Azure AI Search index and load demo docs.

Creates (or updates) a simple keyword-searchable index and uploads every
``*.txt`` file under ``data/documents`` so the knowledge-assistant's
``azure_ai_search`` tool has enterprise content to ground answers in.

Env vars:
    SEARCH_SERVICE_ENDPOINT   https://<service>.search.windows.net (required)
    SEARCH_INDEX_NAME         Index name (default: knowledge-docs)
    SEARCH_ADMIN_KEY          Admin key (optional). If unset, uses Azure AD
                              (DefaultAzureCredential) which needs the
                              "Search Index Data Contributor" + "Search Service
                              Contributor" roles.
    DOCUMENTS_DIR             Folder of .txt docs (default: <repo>/data/documents)

Output:
    Prints "SEARCH_INDEX_NAME=<name>" on the last line (easy for shells to capture).

Auth: DefaultAzureCredential (run `az login`) unless SEARCH_ADMIN_KEY is set.
"""

import hashlib
import os
import sys
from pathlib import Path

from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchableField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
)

INDEX_NAME = os.environ.get("SEARCH_INDEX_NAME", "knowledge-docs")
REPO_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTS_DIR = Path(os.environ.get("DOCUMENTS_DIR", REPO_ROOT / "data" / "documents"))


def _credential():
    key = os.environ.get("SEARCH_ADMIN_KEY", "").strip()
    if key:
        return AzureKeyCredential(key)
    return DefaultAzureCredential()


def build_index() -> SearchIndex:
    """A minimal index: full-text searchable title/content plus a filter facet."""
    return SearchIndex(
        name=INDEX_NAME,
        fields=[
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(name="title", type=SearchFieldDataType.String),
            SearchableField(name="content", type=SearchFieldDataType.String),
            SearchableField(
                name="category",
                type=SearchFieldDataType.String,
                filterable=True,
                facetable=True,
            ),
            SimpleField(name="source", type=SearchFieldDataType.String),
        ],
    )


def load_documents() -> list[dict]:
    if not DOCUMENTS_DIR.is_dir():
        print(f"No documents directory at {DOCUMENTS_DIR}", file=sys.stderr)
        return []

    docs: list[dict] = []
    for path in sorted(DOCUMENTS_DIR.glob("*.txt")):
        text = path.read_text(encoding="utf-8").strip()
        title = text.splitlines()[0].strip() if text else path.stem
        # Stable, index-safe key derived from the file name.
        doc_id = hashlib.sha1(path.name.encode("utf-8")).hexdigest()
        docs.append(
            {
                "id": doc_id,
                "title": title,
                "content": text,
                "category": path.stem,
                "source": path.name,
            }
        )
    return docs


def main() -> None:
    endpoint = os.environ["SEARCH_SERVICE_ENDPOINT"].rstrip("/")
    credential = _credential()

    index_client = SearchIndexClient(endpoint=endpoint, credential=credential)
    index_client.create_or_update_index(build_index())
    print(f"Ensured index '{INDEX_NAME}'", file=sys.stderr)

    docs = load_documents()
    if not docs:
        print("No documents found to upload.", file=sys.stderr)
    else:
        search_client = SearchClient(endpoint=endpoint, index_name=INDEX_NAME, credential=credential)
        result = search_client.upload_documents(documents=docs)
        succeeded = sum(1 for r in result if r.succeeded)
        print(f"Uploaded {succeeded}/{len(docs)} documents", file=sys.stderr)

    # Last stdout line is easy to capture from a shell.
    print(f"SEARCH_INDEX_NAME={INDEX_NAME}")


if __name__ == "__main__":
    main()
