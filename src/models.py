from __future__ import annotations

import logging
import os
from collections.abc import MutableMapping
from time import perf_counter
from typing import IO, Any

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    DatasetCredential,
    ModelCredentialRequest,
    ModelVersion,
    UpdateModelVersionRequest,
)
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)

def upload_weights(
    *,
    name: str,
    version: str,
    source: str | os.PathLike[str],
    weight_type: str | None = None,
    base_model: str | None = None,
    description: str | None = None,
    tags: dict[str, str] | None = None,
    azcopy_path: str | None = None,
    wait_for_commit: bool = True,
    polling_timeout: float = 300.0,
    polling_interval: float = 2.0,
) -> ModelVersion | None:
    started = perf_counter()
    logger.info(
        "Uploading model weights name=%s version=%s source=%s",
        name,
        version,
        source,
    )

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        result = client.beta.models.create(
            name=name,
            version=version,
            source=source,
            weight_type=weight_type,
            base_model=base_model,
            description=description,
            tags=tags,
            azcopy_path=azcopy_path,
            wait_for_commit=wait_for_commit,
            polling_timeout=polling_timeout,
            polling_interval=polling_interval,
        )

    logger.info(
        "Uploaded model weights name=%s version=%s committed=%s duration_ms=%.0f",
        name,
        version,
        result is not None,
        (perf_counter() - started) * 1000,
    )
    return result

def delete_weights(name: str, version: str) -> None:
    started = perf_counter()
    logger.info("Deleting model weights name=%s version=%s", name, version)

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        client.beta.models.delete(name=name, version=version)

    logger.info(
        "Deleted model weights name=%s version=%s duration_ms=%.0f",
        name,
        version,
        (perf_counter() - started) * 1000,
    )

def get_model_credentials(
    name: str,
    version: str,
    credential_request: ModelCredentialRequest | MutableMapping[str, Any] | IO[bytes],
) -> DatasetCredential:
    started = perf_counter()
    logger.info("Getting model credentials name=%s version=%s", name, version)

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        result = client.beta.models.get_credentials(
            name=name,
            version=version,
            credential_request=credential_request,
        )

    logger.info(
        "Retrieved model credentials name=%s version=%s duration_ms=%.0f",
        name,
        version,
        (perf_counter() - started) * 1000,
    )
    return result

def update_weights(
    name: str,
    version: str,
    model_version_update: UpdateModelVersionRequest
    | MutableMapping[str, Any]
    | IO[bytes],
) -> ModelVersion:
    started = perf_counter()
    logger.info("Updating model weights name=%s version=%s", name, version)

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        result = client.beta.models.update(
            name=name,
            version=version,
            model_version_update=model_version_update,
        )

    logger.info(
        "Updated model weights name=%s version=%s duration_ms=%.0f",
        name,
        version,
        (perf_counter() - started) * 1000,
    )
    return result

def list_models() -> list[ModelVersion]:
    started = perf_counter()
    logger.info("Listing models")

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        result = list(client.beta.models.list())

    logger.info(
        "Listed models count=%d duration_ms=%.0f",
        len(result),
        (perf_counter() - started) * 1000,
    )
    return result

def list_model_versions(name: str) -> list[ModelVersion]:
    started = perf_counter()
    logger.info("Listing model versions name=%s", name)

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        result = list(client.beta.models.list_versions(name=name))

    logger.info(
        "Listed model versions name=%s count=%d duration_ms=%.0f",
        name,
        len(result),
        (perf_counter() - started) * 1000,
    )
    return result

def get_model_version(name: str, version: str) -> ModelVersion:
    started = perf_counter()
    logger.info("Getting model version name=%s version=%s", name, version)

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        result = client.beta.models.get(name=name, version=version)

    logger.info(
        "Retrieved model version name=%s version=%s duration_ms=%.0f",
        name,
        version,
        (perf_counter() - started) * 1000,
    )
    return result


# pending_upload(name, version, request)	Obtain project-managed storage and a SAS URI
# pending_create_version(name, version, model_version)	Finalize registration asynchronously