from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import timedelta
from pathlib import Path
from typing import Any

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    DeleteMemoryResult,
    DeleteMemoryStoreResult,
    MemoryItem,
    MemorySearchOptions,
    MemoryStoreDefaultDefinition,
    MemoryStoreDefaultOptions,
    MemoryStoreDeleteScopeResult,
    MemoryStoreDetails,
    MemoryStoreSearchResult,
    MemoryStoreUpdateCompletedResult,
    PageOrder,
)
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)


def create_memory_store(
    *,
    name: str,
    definition: MemoryStoreDefaultDefinition,
    description: str | None = None,
    metadata: dict[str, str] | None = None,
) -> MemoryStoreDetails:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return client.beta.memory_stores.create(
            name=name,
            definition=definition,
            description=description,
            metadata=metadata,
        )


def get_memory_store(name: str) -> MemoryStoreDetails:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return client.beta.memory_stores.get(name=name)


def list_memory_stores(
    *,
    limit: int | None = None,
    order: str | PageOrder | None = None,
    before: str | None = None,
) -> list[MemoryStoreDetails]:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return [
            store
            for store in client.beta.memory_stores.list(
                limit=limit,
                order=order,
                before=before,
            )
        ]


def update_memory_store(
    name: str,
    *,
    description: str | None = None,
    metadata: dict[str, str] | None = None,
) -> MemoryStoreDetails:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return client.beta.memory_stores.update(
            name=name,
            description=description,
            metadata=metadata,
        )


def delete_memory_store(name: str) -> DeleteMemoryStoreResult:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return client.beta.memory_stores.delete(name=name)


def begin_update_memories(
    name: str,
    *,
    scope: str,
    items: str | list[dict[str, Any]] | None = None,
    previous_update_id: str | None = None,
    update_delay: int | None = None,
) -> MemoryStoreUpdateCompletedResult:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        poller = client.beta.memory_stores.begin_update_memories(
            name=name,
            scope=scope,
            items=items,
            previous_update_id=previous_update_id,
            update_delay=update_delay,
        )
        return poller.result()


def search_memories(
    name: str,
    *,
    scope: str,
    items: str | list[dict[str, Any]] | None = None,
    previous_search_id: str | None = None,
    options: MemorySearchOptions | None = None,
) -> MemoryStoreSearchResult:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return client.beta.memory_stores.search_memories(
            name=name,
            scope=scope,
            items=items,
            previous_search_id=previous_search_id,
            options=options,
        )


def delete_scope(name: str, *, scope: str) -> MemoryStoreDeleteScopeResult:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return client.beta.memory_stores.delete_scope(name=name, scope=scope)


def create_memory(
    name: str,
    *,
    scope: str,
    content: str,
    kind: str,
) -> MemoryItem:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return client.beta.memory_stores.create_memory(
            name=name,
            scope=scope,
            content=content,
            kind=kind,
        )


def get_memory(name: str, memory_id: str) -> MemoryItem:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return client.beta.memory_stores.get_memory(
            name=name,
            memory_id=memory_id,
        )


def list_memories(
    name: str,
    *,
    scope: str,
    kind: str | None = None,
    limit: int | None = None,
    order: str | PageOrder | None = None,
    before: str | None = None,
) -> list[MemoryItem]:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return [
            memory
            for memory in client.beta.memory_stores.list_memories(
                name=name,
                scope=scope,
                kind=kind,
                limit=limit,
                order=order,
                before=before,
            )
        ]


def update_memory(name: str, memory_id: str, *, content: str) -> MemoryItem:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return client.beta.memory_stores.update_memory(
            name=name,
            memory_id=memory_id,
            content=content,
        )


def delete_memory(name: str, memory_id: str) -> DeleteMemoryResult:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return client.beta.memory_stores.delete_memory(
            name=name,
            memory_id=memory_id,
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Manage Microsoft Foundry memory stores.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    create_command = commands.add_parser("create")
    create_command.add_argument("-n", "--name", required=True)
    create_command.add_argument("--chat-model", required=True)
    create_command.add_argument("--embedding-model", required=True)
    create_command.add_argument("-d", "--description")
    create_command.add_argument("--metadata", type=Path)
    create_command.add_argument(
        "--user-profile-enabled",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    create_command.add_argument(
        "--chat-summary-enabled",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    create_command.add_argument(
        "--procedural-memory-enabled",
        action=argparse.BooleanOptionalAction,
        default=None,
    )
    create_command.add_argument("--user-profile-details")
    create_command.add_argument("--default-ttl-seconds", type=int)

    get_command = commands.add_parser("get")
    get_command.add_argument("-n", "--name", required=True)

    list_command = commands.add_parser("list")
    list_command.add_argument("--limit", type=int)
    list_command.add_argument("--order", choices=("asc", "desc"))
    list_command.add_argument("--before")

    update_command = commands.add_parser("update")
    update_command.add_argument("-n", "--name", required=True)
    update_command.add_argument("-d", "--description")
    update_command.add_argument("--metadata", type=Path)

    delete_command = commands.add_parser("delete")
    delete_command.add_argument("-n", "--name", required=True)

    update_memories_command = commands.add_parser("begin-update-memories")
    update_memories_command.add_argument("-n", "--name", required=True)
    update_memories_command.add_argument("-s", "--scope", required=True)
    update_memories_command.add_argument("--items", type=Path)
    update_memories_command.add_argument("--previous-update-id")
    update_memories_command.add_argument("--update-delay", type=int)

    search_command = commands.add_parser("search-memories")
    search_command.add_argument("-n", "--name", required=True)
    search_command.add_argument("-s", "--scope", required=True)
    search_command.add_argument("--items", type=Path)
    search_command.add_argument("--previous-search-id")
    search_command.add_argument("--options", type=Path)

    delete_scope_command = commands.add_parser("delete-scope")
    delete_scope_command.add_argument("-n", "--name", required=True)
    delete_scope_command.add_argument("-s", "--scope", required=True)

    create_memory_command = commands.add_parser("create-memory")
    create_memory_command.add_argument("-n", "--name", required=True)
    create_memory_command.add_argument("-s", "--scope", required=True)
    create_memory_command.add_argument("-c", "--content", required=True)
    create_memory_command.add_argument(
        "-k",
        "--kind",
        choices=("user_profile", "chat_summary", "procedural"),
        required=True,
    )

    get_memory_command = commands.add_parser("get-memory")
    get_memory_command.add_argument("-n", "--name", required=True)
    get_memory_command.add_argument("--memory-id", required=True)

    list_memories_command = commands.add_parser("list-memories")
    list_memories_command.add_argument("-n", "--name", required=True)
    list_memories_command.add_argument("-s", "--scope", required=True)
    list_memories_command.add_argument(
        "-k",
        "--kind",
        choices=("user_profile", "chat_summary", "procedural"),
    )
    list_memories_command.add_argument("--limit", type=int)
    list_memories_command.add_argument("--order", choices=("asc", "desc"))
    list_memories_command.add_argument("--before")

    update_memory_command = commands.add_parser("update-memory")
    update_memory_command.add_argument("-n", "--name", required=True)
    update_memory_command.add_argument("--memory-id", required=True)
    update_memory_command.add_argument("-c", "--content", required=True)

    delete_memory_command = commands.add_parser("delete-memory")
    delete_memory_command.add_argument("-n", "--name", required=True)
    delete_memory_command.add_argument("--memory-id", required=True)

    args = parser.parse_args()

    try:
        if args.command == "create":
            metadata = (
                json.loads(args.metadata.read_text(encoding="utf-8"))
                if args.metadata
                else None
            )
            options = MemoryStoreDefaultOptions(
                user_profile_enabled=args.user_profile_enabled,
                chat_summary_enabled=args.chat_summary_enabled,
                procedural_memory_enabled=args.procedural_memory_enabled,
                user_profile_details=args.user_profile_details,
                default_ttl_seconds=(
                    timedelta(seconds=args.default_ttl_seconds)
                    if args.default_ttl_seconds is not None
                    else None
                ),
            )
            result = create_memory_store(
                name=args.name,
                definition=MemoryStoreDefaultDefinition(
                    chat_model=args.chat_model,
                    embedding_model=args.embedding_model,
                    options=options,
                ),
                description=args.description,
                metadata=metadata,
            )
            output = result.as_dict()

        elif args.command == "get":
            output = get_memory_store(args.name).as_dict()

        elif args.command == "list":
            output = [
                store.as_dict()
                for store in list_memory_stores(
                    limit=args.limit,
                    order=args.order,
                    before=args.before,
                )
            ]

        elif args.command == "update":
            metadata = (
                json.loads(args.metadata.read_text(encoding="utf-8"))
                if args.metadata
                else None
            )
            output = update_memory_store(
                args.name,
                description=args.description,
                metadata=metadata,
            ).as_dict()

        elif args.command == "delete":
            output = delete_memory_store(args.name).as_dict()

        elif args.command == "begin-update-memories":
            items = (
                json.loads(args.items.read_text(encoding="utf-8"))
                if args.items
                else None
            )
            output = begin_update_memories(
                args.name,
                scope=args.scope,
                items=items,
                previous_update_id=args.previous_update_id,
                update_delay=args.update_delay,
            ).as_dict()

        elif args.command == "search-memories":
            items = (
                json.loads(args.items.read_text(encoding="utf-8"))
                if args.items
                else None
            )
            options = (
                MemorySearchOptions(
                    json.loads(args.options.read_text(encoding="utf-8"))
                )
                if args.options
                else None
            )
            output = search_memories(
                args.name,
                scope=args.scope,
                items=items,
                previous_search_id=args.previous_search_id,
                options=options,
            ).as_dict()

        elif args.command == "delete-scope":
            output = delete_scope(args.name, scope=args.scope).as_dict()

        elif args.command == "create-memory":
            output = create_memory(
                args.name,
                scope=args.scope,
                content=args.content,
                kind=args.kind,
            ).as_dict()

        elif args.command == "get-memory":
            output = get_memory(args.name, args.memory_id).as_dict()

        elif args.command == "list-memories":
            output = [
                memory.as_dict()
                for memory in list_memories(
                    args.name,
                    scope=args.scope,
                    kind=args.kind,
                    limit=args.limit,
                    order=args.order,
                    before=args.before,
                )
            ]

        elif args.command == "update-memory":
            output = update_memory(
                args.name,
                args.memory_id,
                content=args.content,
            ).as_dict()

        elif args.command == "delete-memory":
            output = delete_memory(args.name, args.memory_id).as_dict()

        else:
            raise AssertionError(f"Unhandled command: {args.command}")

        print(json.dumps(output, indent=2, default=str))
    except Exception:
        logger.exception("Memory store command failed command=%s", args.command)
        raise SystemExit(1)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    )
    main()

