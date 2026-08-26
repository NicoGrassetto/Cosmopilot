from __future__ import annotations

import logging
import os
from time import perf_counter

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import Connection, ConnectionType
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)


def get_connection(
    name: str,
    *,
    include_credentials: bool | None = False,
) -> Connection:
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
            include_credentials=include_credentials,
        )

    logger.info(
        "Retrieved connection name=%s duration_ms=%.0f",
        name,
        (perf_counter() - started) * 1000,
    )
    return result


def get_default_connection(
    connection_type: str | ConnectionType,
    *,
    include_credentials: bool | None = False,
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
            include_credentials=include_credentials,
        )

    logger.info(
        "Retrieved default connection type=%s name=%s duration_ms=%.0f",
        connection_type,
        result.name,
        (perf_counter() - started) * 1000,
    )
    return result


def list_connections(
    *,
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