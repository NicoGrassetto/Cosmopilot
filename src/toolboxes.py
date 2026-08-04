from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from time import perf_counter
from typing import Any

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

from azure.ai.projects.models import ToolboxVersionObject, ToolboxTool, ToolboxSkill, ToolboxPolicies, PageOrder, ToolboxObject

logger = logging.getLogger(__name__)

def create_toolbox(
    name: str,
    *,
    tools: list[ToolboxTool],
    description: str | None = None,
    metadata: dict[str, str] | None = None,
    skills: list[ToolboxSkill] | None = None,
    policies: ToolboxPolicies | None = None,
    content_type: str = "application/json",
    allow_preview: bool = False,
    **kwargs: Any,
    ) -> ToolboxVersionObject:
    started = perf_counter()
    logger.info(
        "Creating toolbox version name=%s tool_count=%d skill_count=%d",
        name,
        len(tools),
        len(skills or []),
    )

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        result = client.toolboxes.create_version(
            name=name,
            tools=tools,
            description=description,
            metadata=metadata,
            skills=skills,
            policies=policies,
            content_type=content_type,
            **kwargs,
        )

    logger.info(
        "Created toolbox version name=%s version=%s duration_ms=%.0f",
        result.name,
        result.version,
        (perf_counter() - started) * 1000,
    )
    return result

def create_toolbox_version_from_definition(
    name: str,
    definition: dict[str, Any],
    *,
    content_type: str = "application/json",
    allow_preview: bool = False,
    **kwargs: Any,
) -> ToolboxVersionObject:
    """Create a toolbox version from an already-serialized definition."""
    started = perf_counter()
    logger.info("Creating toolbox version from definition name=%s", name)

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        result = client.toolboxes.create_version(
            name=name,
            body=definition,
            content_type=content_type,
            **kwargs,
        )

    logger.info(
        "Created toolbox version name=%s version=%s duration_ms=%.0f",
        result.name,
        result.version,
        (perf_counter() - started) * 1000,
    )
    return result

def get_toolbox(
    name: str,
    *,
    allow_preview: bool = False,
    **kwargs: Any,
) -> ToolboxObject:
    started = perf_counter()
    logger.info("Getting toolbox name=%s", name)

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        result = client.toolboxes.get(name=name, **kwargs)

    logger.info(
        "Retrieved toolbox name=%s default_version=%s duration_ms=%.0f",
        result.name,
        result.default_version,
        (perf_counter() - started) * 1000,
    )
    return result

def list_toolboxes(
    *,
    limit: int | None = None,
    order: str | PageOrder | None = None,
    before: str | None = None,
    allow_preview: bool = False,
    **kwargs: Any,
) -> list[ToolboxObject]:
    started = perf_counter()
    logger.info("Listing toolboxes limit=%s order=%s", limit, order)

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        result = list(
            client.toolboxes.list(
                limit=limit,
                order=order,
                before=before,
                **kwargs,
            )
        )

    logger.info(
        "Listed toolboxes count=%d duration_ms=%.0f",
        len(result),
        (perf_counter() - started) * 1000,
    )
    return result

def update_toolbox(
    name: str,
    default_version: str,
    *,
    content_type: str = "application/json",
    allow_preview: bool = False,
    **kwargs: Any,
) -> ToolboxObject:
    started = perf_counter()
    logger.info(
        "Updating toolbox name=%s default_version=%s",
        name,
        default_version,
    )

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        result = client.toolboxes.update(
            name=name,
            default_version=default_version,
            content_type=content_type,
            **kwargs,
        )

    logger.info(
        "Updated toolbox name=%s default_version=%s duration_ms=%.0f",
        result.name,
        result.default_version,
        (perf_counter() - started) * 1000,
    )
    return result

def delete_toolbox(
    name: str,
    *,
    allow_preview: bool = False,
    **kwargs: Any,
) -> None:
    started = perf_counter()
    logger.info("Deleting toolbox name=%s", name)

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        client.toolboxes.delete(name=name, **kwargs)

    logger.info(
        "Deleted toolbox name=%s duration_ms=%.0f",
        name,
        (perf_counter() - started) * 1000,
    )

def get_toolbox_version(
    name: str,
    version: str,
    *,
    allow_preview: bool = False,
    **kwargs: Any,
) -> ToolboxVersionObject:
    started = perf_counter()
    logger.info("Getting toolbox version name=%s version=%s", name, version)

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        result = client.toolboxes.get_version(
            name=name,
            version=version,
            **kwargs,
        )

    logger.info(
        "Retrieved toolbox version name=%s version=%s duration_ms=%.0f",
        result.name,
        result.version,
        (perf_counter() - started) * 1000,
    )
    return result

def list_toolbox_versions(
    name: str,
    *,
    limit: int | None = None,
    order: str | PageOrder | None = None,
    before: str | None = None,
    allow_preview: bool = False,
    **kwargs: Any,
) -> list[ToolboxVersionObject]:
    started = perf_counter()
    logger.info("Listing toolbox versions name=%s", name)

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        result = list(
            client.toolboxes.list_versions(
                name=name,
                limit=limit,
                order=order,
                before=before,
                **kwargs,
            )
        )

    logger.info(
        "Listed toolbox versions name=%s count=%d duration_ms=%.0f",
        name,
        len(result),
        (perf_counter() - started) * 1000,
    )
    return result

def delete_toolbox_version(
    name: str,
    version: str,
    *,
    allow_preview: bool = False,
    **kwargs: Any,
) -> None:
    started = perf_counter()
    logger.info("Deleting toolbox version name=%s version=%s", name, version)

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        client.toolboxes.delete_version(
            name=name,
            version=version,
            **kwargs,
        )

    logger.info(
        "Deleted toolbox version name=%s version=%s duration_ms=%.0f",
        name,
        version,
        (perf_counter() - started) * 1000,
    )

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    )

    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)

    create_command = commands.add_parser("create-toolbox")
    create_command.add_argument("-n", "--name", required=True)
    create_command.add_argument(
        "-f",
        "--definition",
        type=Path,
        required=True,
    )

    get_command = commands.add_parser("get-toolbox")
    get_command.add_argument("-n", "--name", required=True)

    list_command = commands.add_parser("list-toolboxes")
    list_command.add_argument("--limit", type=int)
    list_command.add_argument("--order", choices=("asc", "desc"))
    list_command.add_argument("--before")

    update_command = commands.add_parser("update-toolbox")
    update_command.add_argument("-n", "--name", required=True)
    update_command.add_argument(
        "-v",
        "--default-version",
        required=True,
    )

    delete_command = commands.add_parser("delete-toolbox")
    delete_command.add_argument("-n", "--name", required=True)

    get_version_command = commands.add_parser("get-toolbox-version")
    get_version_command.add_argument("-n", "--name", required=True)
    get_version_command.add_argument("-v", "--version", required=True)

    list_versions_command = commands.add_parser("list-toolbox-versions")
    list_versions_command.add_argument("-n", "--name", required=True)
    list_versions_command.add_argument("--limit", type=int)
    list_versions_command.add_argument("--order", choices=("asc", "desc"))
    list_versions_command.add_argument("--before")

    delete_version_command = commands.add_parser("delete-toolbox-version")
    delete_version_command.add_argument("-n", "--name", required=True)
    delete_version_command.add_argument("-v", "--version", required=True)

    args = parser.parse_args()

    try:
        if args.command == "create-toolbox":
            definition = json.loads(
                args.definition.read_text(encoding="utf-8")
            )
            result = create_toolbox_version_from_definition(
                name=args.name,
                definition=definition,
                allow_preview=args.allow_preview,
            )
            output = result.as_dict()

        elif args.command == "get-toolbox":
            result = get_toolbox(
                name=args.name,
                allow_preview=args.allow_preview,
            )
            output = result.as_dict()

        elif args.command == "list-toolboxes":
            result = list_toolboxes(
                limit=args.limit,
                order=args.order,
                before=args.before,
                allow_preview=args.allow_preview,
            )
            output = [toolbox.as_dict() for toolbox in result]

        elif args.command == "update-toolbox":
            result = update_toolbox(
                name=args.name,
                default_version=args.default_version,
                allow_preview=args.allow_preview,
            )
            output = result.as_dict()

        elif args.command == "delete-toolbox":
            delete_toolbox(
                name=args.name,
                allow_preview=args.allow_preview,
            )
            output = {
                "name": args.name,
                "deleted": True,
            }

        elif args.command == "get-toolbox-version":
            result = get_toolbox_version(
                name=args.name,
                version=args.version,
                allow_preview=args.allow_preview,
            )
            output = result.as_dict()

        elif args.command == "list-toolbox-versions":
            result = list_toolbox_versions(
                name=args.name,
                limit=args.limit,
                order=args.order,
                before=args.before,
                allow_preview=args.allow_preview,
            )
            output = [version.as_dict() for version in result]

        elif args.command == "delete-toolbox-version":
            delete_toolbox_version(
                name=args.name,
                version=args.version,
                allow_preview=args.allow_preview,
            )
            output = {
                "name": args.name,
                "version": args.version,
                "deleted": True,
            }

        else:
            raise AssertionError(f"Unhandled command: {args.command}")

    except Exception:
        logger.exception(
            "Toolbox command failed command=%s",
            args.command,
        )
        raise SystemExit(1)
    
if __name__ == "__main__":
    main()