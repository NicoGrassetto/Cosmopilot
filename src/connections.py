"""Inspect Microsoft Foundry project connections with ``AIProjectClient``.

See the `ConnectionsOperations API reference <https://learn.microsoft.com/en-us/python/api/azure-ai-projects/azure.ai.projects.operations.connectionsoperations?view=azure-python>`_
for the underlying ``get``, ``get_default``, and ``list`` method signatures.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from time import perf_counter

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import Connection, ConnectionType
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)


def get_connection(name: str) -> Connection:
    started = perf_counter()
    logger.info("Getting connection name=%s", name)

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        result = client.connections.get(
            name=name,
            include_credentials=True
        )

    logger.info(
        "Retrieved connection name=%s duration_ms=%.0f",
        name,
        (perf_counter() - started) * 1000,
    )
    return result


def get_default_connection(
    connection_type: str | ConnectionType,
) -> Connection:
    started = perf_counter()
    logger.info("Getting default connection type=%s", connection_type)

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        result = client.connections.get_default(
            connection_type=connection_type,
            include_credentials=True,
        )

    logger.info(
        "Retrieved default connection type=%s name=%s duration_ms=%.0f",
        connection_type,
        result.name,
        (perf_counter() - started) * 1000,
    )
    return result


def list_connections(
    connection_type: str | ConnectionType | None = None,
    default_connection: bool | None = None,
) -> list[Connection]:
    started = perf_counter()
    logger.info(
        "Listing connections type=%s default_connection=%s",
        connection_type,
        default_connection,
    )

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        result = list(
            client.connections.list(
                connection_type=connection_type,
                default_connection=default_connection,
            )
        )

    logger.info(
        "Listed connections count=%d duration_ms=%.0f",
        len(result),
        (perf_counter() - started) * 1000,
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect Microsoft Foundry project connections.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    connection_types = tuple(item.value for item in ConnectionType) # we just load all the possible values of the enum.

    get_command = commands.add_parser("get")
    get_command.add_argument("-n", "--name", required=True)

    get_default_command = commands.add_parser("get-default")
    get_default_command.add_argument(
        "-t",
        "--connection-type",
        choices=connection_types,
        required=True,
    )

    list_command = commands.add_parser("list")
    list_command.add_argument(
        "-t",
        "--connection-type",
        choices=connection_types,
    )
    list_command.add_argument(
        "--default-connection",
        action=argparse.BooleanOptionalAction,
        default=None,
    )

    args = parser.parse_args()

    try:
        if args.command == "get":
            output = get_connection(args.name).as_dict()

        elif args.command == "get-default":
            output = get_default_connection(args.connection_type).as_dict()

        elif args.command == "list":
            output = [
                connection.as_dict()
                for connection in list_connections(
                    connection_type=args.connection_type,
                    default_connection=args.default_connection,
                )
            ]

        else:
            raise AssertionError(f"Unhandled command: {args.command}")

        print(json.dumps(output, indent=2, default=str))
    except Exception:
        logger.exception("Connection command failed command=%s", args.command)
        raise SystemExit(1)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    )
    main()