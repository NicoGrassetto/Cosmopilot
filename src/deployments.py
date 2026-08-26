from __future__ import annotations

import logging
import os
from time import perf_counter

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import Deployment, DeploymentType
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)


def get_deployment(name: str) -> Deployment:
    started = perf_counter()
    logger.info("Getting deployment name=%s", name)

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        result = client.deployments.get(name=name)

    logger.info(
        "Retrieved deployment name=%s duration_ms=%.0f",
        name,
        (perf_counter() - started) * 1000,
    )
    return result


def list_deployments(
    *,
    model_publisher: str | None = None,
    model_name: str | None = None,
    deployment_type: str | DeploymentType | None = None,
) -> list[Deployment]:
    started = perf_counter()
    logger.info(
        "Listing deployments model_publisher=%s model_name=%s "
        "deployment_type=%s",
        model_publisher,
        model_name,
        deployment_type,
    )

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        result = list(
            client.deployments.list(
                model_publisher=model_publisher,
                model_name=model_name,
                deployment_type=deployment_type,
            )
        )

    logger.info(
        "Listed deployments count=%d duration_ms=%.0f",
        len(result),
        (perf_counter() - started) * 1000,
    )
    return result