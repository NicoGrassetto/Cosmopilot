from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from time import perf_counter
from typing import Any, cast, IO, Iterator

from azure.ai.projects import AIProjectClient
import azure.ai.projects.models as models
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)


def create_agent_version(
    agent_name: str,
    *,
    definition: models.AgentDefinition,
    content_type: str = "application/json",
    metadata: dict[str, str] | None = None,
    description: str | None = None,
    blueprint_reference: models.AgentBlueprintReference | None = None,
    draft: bool | None = None,
    allow_preview: bool = False,
    **kwargs: Any,
) -> models.AgentVersionDetails:
    started = perf_counter()
    logger.info(
        "Creating agent version name=%s kind=%s draft=%s",
        agent_name,
        definition.kind,
        bool(draft),
    )

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        result = client.agents.create_version(
            agent_name=agent_name,
            definition=definition,
            content_type=content_type,
            metadata=metadata,
            description=description,
            blueprint_reference=blueprint_reference,
            draft=draft,
            **kwargs,
        )
        logger.info(
            "Created agent version name=%s version=%s duration_ms=%.0f",
            result.name,
            result.version,
            (perf_counter() - started) * 1000,
        )
        return result

def create_prompt_agent(
    agent_name: str,
    *,
    model: str,
    rai_config: models.RaiConfig | None = None,
    instructions: str | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    reasoning: models.Reasoning | None = None,
    tools: list[models.Tool] | None = None,
    tool_choice: str | models.ToolChoiceParam | None = None,
    text: models.PromptAgentDefinitionTextOptions | None = None,
    structured_inputs: dict[str, models.StructuredInputDefinition] | None = None,
    content_type: str = "application/json",
    metadata: dict[str, str] | None = None,
    description: str | None = None,
    blueprint_reference: models.AgentBlueprintReference | None = None,
    draft: bool | None = None,
    allow_preview: bool = False,
    **kwargs: Any,
) -> models.AgentVersionDetails:
    started = perf_counter()
    logger.info(
        "Creating prompt agent name=%s model=%s draft=%s tool_count=%d",
        agent_name,
        model,
        bool(draft),
        len(tools or []),
    )

    definition = models.PromptAgentDefinition(
        model=model,
        rai_config=rai_config,
        instructions=instructions,
        temperature=temperature,
        top_p=top_p,
        reasoning=reasoning,
        tools=tools,
        tool_choice=tool_choice,
        text=text,
        structured_inputs=structured_inputs,
    )

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        result = client.agents.create_version(
            agent_name=agent_name,
            definition=definition,
            content_type=content_type,
            metadata=metadata,
            description=description,
            blueprint_reference=blueprint_reference,
            draft=draft,
            **kwargs,
        )
        logger.info(
            "Created prompt agent name=%s version=%s duration_ms=%.0f",
            result.name,
            result.version,
            (perf_counter() - started) * 1000,
        )
        return result

def create_version_from_manifest(
    agent_name: str,
    *,
    manifest_id: str,
    parameter_values: dict[str, Any],
    content_type: str = "application/json",
    metadata: dict[str, str] | None = None,
    description: str | None = None,
    allow_preview: bool = False,
    **kwargs: Any,
) -> models.AgentVersionDetails:
    started = perf_counter()
    logger.info(
        "Creating agent version from manifest name=%s manifest_id=%s",
        agent_name,
        manifest_id,
    )

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        result = client.agents.create_version_from_manifest(
            agent_name=agent_name,
            manifest_id=manifest_id,
            parameter_values=parameter_values,
            content_type=content_type,
            metadata=metadata,
            description=description,
            **kwargs,
        )
        logger.info(
            "Created agent version from manifest name=%s version=%s duration_ms=%.0f",
            result.name,
            result.version,
            (perf_counter() - started) * 1000,
        )
        return result

def create_version_from_code(
    agent_name: str,
    *,
    definition: models.HostedAgentDefinition,
    code: IO[bytes],
    code_zip_sha256: str | None = None,
    description: str | None = None,
    metadata: dict[str, str] | None = None,
    allow_preview: bool = False,
    **kwargs: Any,
) -> models.AgentVersionDetails:
    started = perf_counter()
    logger.info(
        "Creating agent version from code name=%s code_hash_present=%s",
        agent_name,
        code_zip_sha256 is not None,
    )

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        result = client.agents.create_version_from_code(
            agent_name=agent_name,
            definition=definition,
            code=code,
            code_zip_sha256=code_zip_sha256,
            description=description,
            metadata=metadata,
            **kwargs,
        )
        logger.info(
            "Created agent version from code name=%s version=%s duration_ms=%.0f",
            result.name,
            result.version,
            (perf_counter() - started) * 1000,
        )
        return result

def download_code(
    agent_name: str,
    *,
    agent_version: str | None = None,
    allow_preview: bool = False,
    **kwargs: Any,
) -> Iterator[bytes]:
    started = perf_counter()
    logger.info(
        "Downloading agent code name=%s version=%s",
        agent_name,
        agent_version,
    )
    byte_count = 0

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        for chunk in client.agents.download_code(
            agent_name=agent_name,
            agent_version=agent_version,
            **kwargs,
        ):
            byte_count += len(chunk)
            yield chunk

    logger.info(
        "Downloaded agent code name=%s bytes=%d duration_ms=%.0f",
        agent_name,
        byte_count,
        (perf_counter() - started) * 1000,
    )

def get_agent(
    agent_name: str,
    *,
    allow_preview: bool = False,
    **kwargs: Any,
) -> models.AgentDetails:
    started = perf_counter()
    logger.info("Getting agent name=%s", agent_name)

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        result = client.agents.get(agent_name=agent_name, **kwargs)
        logger.info(
            "Retrieved agent name=%s state=%s duration_ms=%.0f",
            result.name,
            result.state,
            (perf_counter() - started) * 1000,
        )
        return result
    
def list_agents(
    *,
    kind: str | models.AgentKind | None = None,
    limit: int | None = None,
    order: str | models.PageOrder | None = None,
    before: str | None = None,
    allow_preview: bool = False,
    **kwargs: Any,
) -> list[models.AgentDetails]:
    started = perf_counter()
    logger.info(
        "Listing agents kind=%s limit=%s order=%s cursor_present=%s",
        kind,
        limit,
        order,
        before is not None,
    )

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        result = list(
            client.agents.list(
                kind=kind,
                limit=limit,
                order=order,
                before=before,
                **kwargs,
            )
        )
        logger.info(
            "Listed agents count=%d duration_ms=%.0f",
            len(result),
            (perf_counter() - started) * 1000,
        )
        return result

def get_agent_version(
    agent_name: str,
    agent_version: str,
    *,
    allow_preview: bool = False,
    **kwargs: Any,
) -> models.AgentVersionDetails:
    started = perf_counter()
    logger.info(
        "Getting agent version name=%s version=%s",
        agent_name,
        agent_version,
    )

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        result = client.agents.get_version(
            agent_name=agent_name,
            agent_version=agent_version,
            **kwargs,
        )
        logger.info(
            "Retrieved agent version name=%s version=%s duration_ms=%.0f",
            result.name,
            result.version,
            (perf_counter() - started) * 1000,
        )
        return result

def list_agent_versions(
    agent_name: str,
    *,
    limit: int | None = None,
    order: str | models.PageOrder | None = None,
    before: str | None = None,
    include_drafts: bool | None = None,
    allow_preview: bool = False,
    **kwargs: Any,
) -> list[models.AgentVersionDetails]:
    started = perf_counter()
    logger.info("Listing agent versions name=%s", agent_name)

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        result = list(
            client.agents.list_versions(
                agent_name=agent_name,
                limit=limit,
                order=order,
                before=before,
                include_drafts=include_drafts,
                **kwargs,
            )
        )
        logger.info(
            "Listed agent versions name=%s count=%d duration_ms=%.0f",
            agent_name,
            len(result),
            (perf_counter() - started) * 1000,
        )
        return result

def update_agent_details(
    agent_name: str,
    *,
    content_type: str = "application/merge-patch+json",
    agent_endpoint: models.AgentEndpointConfig | None = None,
    agent_card: models.AgentCard | None = None,
    allow_preview: bool = False,
    **kwargs: Any,
) -> models.AgentDetails:
    started = perf_counter()
    logger.info("Updating agent details name=%s", agent_name)

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        result = client.agents.update_details(
            agent_name=agent_name,
            content_type=content_type,
            agent_endpoint=agent_endpoint,
            agent_card=agent_card,
            **kwargs,
        )
        logger.info(
            "Updated agent details name=%s state=%s duration_ms=%.0f",
            result.name,
            result.state,
            (perf_counter() - started) * 1000,
        )
        return result

def enable_agent(
    agent_name: str,
    *,
    allow_preview: bool = False,
    **kwargs: Any,
) -> None:
    started = perf_counter()
    logger.info("Enabling agent name=%s", agent_name)

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        client.agents.enable(agent_name=agent_name, **kwargs)
        logger.info(
            "Enabled agent name=%s duration_ms=%.0f",
            agent_name,
            (perf_counter() - started) * 1000,
        )

def disable_agent(
    agent_name: str,
    *,
    allow_preview: bool = False,
    **kwargs: Any,
) -> None:
    started = perf_counter()
    logger.info("Disabling agent name=%s", agent_name)

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        client.agents.disable(agent_name=agent_name, **kwargs)
        logger.info(
            "Disabled agent name=%s duration_ms=%.0f",
            agent_name,
            (perf_counter() - started) * 1000,
        )


def delete_agent(
    agent_name: str,
    *,
    force: bool | None = None,
    allow_preview: bool = False,
    **kwargs: Any,
) -> models.DeleteAgentResponse:
    started = perf_counter()
    logger.info("Deleting agent name=%s force=%s", agent_name, force)

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        result = client.agents.delete(
            agent_name=agent_name,
            force=force,
            **kwargs,
        )
        logger.info(
            "Deleted agent name=%s deleted=%s duration_ms=%.0f",
            agent_name,
            result.deleted,
            (perf_counter() - started) * 1000,
        )
        return result

def delete_agent_version(
    agent_name: str,
    agent_version: str,
    *,
    force: bool | None = None,
    allow_preview: bool = False,
    **kwargs: Any,
) -> models.DeleteAgentVersionResponse:
    started = perf_counter()
    logger.info(
        "Deleting agent version name=%s version=%s force=%s",
        agent_name,
        agent_version,
        force,
    )

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        result = client.agents.delete_version(
            agent_name=agent_name,
            agent_version=agent_version,
            force=force,
            **kwargs,
        )
        logger.info(
            "Deleted agent version name=%s version=%s deleted=%s duration_ms=%.0f",
            agent_name,
            agent_version,
            result.deleted,
            (perf_counter() - started) * 1000,
        )
        return result

def create_session(
    agent_name: str,
    *,
    version_indicator: models.VersionIndicator,
    content_type: str = "application/json",
    agent_session_id: str | None = None,
    allow_preview: bool = False,
    **kwargs: Any,
) -> models.AgentSessionResource:
    started = perf_counter()
    logger.info(
        "Creating agent session name=%s requested_session_id=%s",
        agent_name,
        agent_session_id,
    )

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        result = client.agents.create_session(
            agent_name=agent_name,
            version_indicator=version_indicator,
            content_type=content_type,
            agent_session_id=agent_session_id,
            **kwargs,
        )
        logger.info(
            "Created agent session name=%s session_id=%s status=%s duration_ms=%.0f",
            agent_name,
            result.agent_session_id,
            result.status,
            (perf_counter() - started) * 1000,
        )
        return result

def get_session(
    agent_name: str,
    session_id: str,
    *,
    allow_preview: bool = False,
    **kwargs: Any,
) -> models.AgentSessionResource:
    started = perf_counter()
    logger.info("Getting agent session name=%s session_id=%s", agent_name, session_id)

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        result = client.agents.get_session(
            agent_name=agent_name,
            session_id=session_id,
            **kwargs,
        )
        logger.info(
            "Retrieved agent session name=%s session_id=%s status=%s duration_ms=%.0f",
            agent_name,
            result.agent_session_id,
            result.status,
            (perf_counter() - started) * 1000,
        )
        return result

def list_sessions(
    agent_name: str,
    *,
    limit: int | None = None,
    order: str | models.PageOrder | None = None,
    before: str | None = None,
    allow_preview: bool = False,
    **kwargs: Any,
) -> list[models.AgentSessionResource]:
    started = perf_counter()
    logger.info("Listing agent sessions name=%s limit=%s", agent_name, limit)

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        result = list(
            client.agents.list_sessions(
                agent_name=agent_name,
                limit=limit,
                order=order,
                before=before,
                **kwargs,
            )
        )
        logger.info(
            "Listed agent sessions name=%s count=%d duration_ms=%.0f",
            agent_name,
            len(result),
            (perf_counter() - started) * 1000,
        )
        return result

def stop_session(
    agent_name: str,
    session_id: str,
    *,
    allow_preview: bool = False,
    **kwargs: Any,
) -> None:
    started = perf_counter()
    logger.info("Stopping agent session name=%s session_id=%s", agent_name, session_id)

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        client.agents.stop_session(
            agent_name=agent_name,
            session_id=session_id,
            **kwargs,
        )
        logger.info(
            "Stopped agent session name=%s session_id=%s duration_ms=%.0f",
            agent_name,
            session_id,
            (perf_counter() - started) * 1000,
        )

def delete_session(
    agent_name: str,
    session_id: str,
    *,
    allow_preview: bool = False,
    **kwargs: Any,
) -> None:
    started = perf_counter()
    logger.info("Deleting agent session name=%s session_id=%s", agent_name, session_id)

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        client.agents.delete_session(
            agent_name=agent_name,
            session_id=session_id,
            **kwargs,
        )
        logger.info(
            "Deleted agent session name=%s session_id=%s duration_ms=%.0f",
            agent_name,
            session_id,
            (perf_counter() - started) * 1000,
        )

def get_session_log_stream(
    agent_name: str,
    agent_version: str,
    session_id: str,
    *,
    allow_preview: bool = False,
    **kwargs: Any,
) -> Iterator[bytes]:
    started = perf_counter()
    logger.info(
        "Streaming agent session logs name=%s version=%s session_id=%s",
        agent_name,
        agent_version,
        session_id,
    )
    byte_count = 0

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        stream = cast(
            Iterator[bytes],
            client.agents.get_session_log_stream(
                agent_name=agent_name,
                agent_version=agent_version,
                session_id=session_id,
                **kwargs,
            ),
        )
        for chunk in stream:
            byte_count += len(chunk)
            yield chunk

    logger.info(
        "Streamed agent session logs name=%s session_id=%s bytes=%d duration_ms=%.0f",
        agent_name,
        session_id,
        byte_count,
        (perf_counter() - started) * 1000,
    )

def list_session_files(
    agent_name: str,
    session_id: str,
    *,
    path: str | None = None,
    limit: int | None = None,
    order: str | models.PageOrder | None = None,
    before: str | None = None,
    allow_preview: bool = False,
    **kwargs: Any,
) -> list[models.SessionDirectoryEntry]:
    started = perf_counter()
    logger.info(
        "Listing agent session files name=%s session_id=%s path=%s",
        agent_name,
        session_id,
        path,
    )

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        result = list(
            client.agents.list_session_files(
                agent_name=agent_name,
                session_id=session_id,
                path=path,
                limit=limit,
                order=order,
                before=before,
                **kwargs,
            )
        )
        logger.info(
            "Listed agent session files name=%s session_id=%s count=%d duration_ms=%.0f",
            agent_name,
            session_id,
            len(result),
            (perf_counter() - started) * 1000,
        )
        return result

def upload_session_file(
    agent_name: str,
    session_id: str,
    content: bytes,
    *,
    path: str,
    allow_preview: bool = False,
    **kwargs: Any,
) -> models.SessionFileWriteResult:
    started = perf_counter()
    logger.info(
        "Uploading agent session file name=%s session_id=%s path=%s bytes=%d",
        agent_name,
        session_id,
        path,
        len(content),
    )

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        result = client.agents.upload_session_file(
            agent_name=agent_name,
            session_id=session_id,
            content=content,
            path=path,
            **kwargs,
        )
        logger.info(
            "Uploaded agent session file name=%s session_id=%s path=%s duration_ms=%.0f",
            agent_name,
            session_id,
            path,
            (perf_counter() - started) * 1000,
        )
        return result

def download_session_file(
    agent_name: str,
    session_id: str,
    *,
    path: str,
    allow_preview: bool = False,
    **kwargs: Any,
) -> Iterator[bytes]:
    started = perf_counter()
    logger.info(
        "Downloading agent session file name=%s session_id=%s path=%s",
        agent_name,
        session_id,
        path,
    )
    byte_count = 0

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        for chunk in client.agents.download_session_file(
            agent_name=agent_name,
            session_id=session_id,
            path=path,
            **kwargs,
        ):
            byte_count += len(chunk)
            yield chunk

    logger.info(
        "Downloaded agent session file name=%s session_id=%s path=%s bytes=%d duration_ms=%.0f",
        agent_name,
        session_id,
        path,
        byte_count,
        (perf_counter() - started) * 1000,
    )

def delete_session_file(
    agent_name: str,
    session_id: str,
    *,
    path: str,
    recursive: bool | None = None,
    allow_preview: bool = False,
    **kwargs: Any,
) -> None:
    started = perf_counter()
    logger.info(
        "Deleting agent session file name=%s session_id=%s path=%s recursive=%s",
        agent_name,
        session_id,
        path,
        recursive,
    )

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        client.agents.delete_session_file(
            agent_name=agent_name,
            session_id=session_id,
            path=path,
            recursive=recursive,
            **kwargs,
        )
        logger.info(
            "Deleted agent session file name=%s session_id=%s path=%s duration_ms=%.0f",
            agent_name,
            session_id,
            path,
            (perf_counter() - started) * 1000,
        )

def begin_create_optimization_job(
    job: models.OptimizationJob,
    *,
    operation_id: str | None = None,
    content_type: str = "application/json",
    polling_interval: int | None = None,
    allow_preview: bool = False,
    **kwargs: Any,
) -> models.OptimizationJobResult:
    started = perf_counter()
    logger.info(
        "Creating optimization job operation_id_present=%s",
        operation_id is not None,
    )

    if polling_interval is not None:
        kwargs["polling_interval"] = polling_interval

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        result = client.beta.agents.begin_create_optimization_job(
            job=job,
            operation_id=operation_id,
            content_type=content_type,
            **kwargs,
        ).result()
        logger.info(
            "Created optimization job best_candidate=%s candidate_count=%d duration_ms=%.0f",
            result.best,
            len(result.candidates or []),
            (perf_counter() - started) * 1000,
        )
        return result

def get_optimization_job(
    job_id: str,
    *,
    allow_preview: bool = False,
    **kwargs: Any,
) -> models.OptimizationJob:
    started = perf_counter()
    logger.info("Getting optimization job id=%s", job_id)

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        result = client.beta.agents.get_optimization_job(
            job_id=job_id,
            **kwargs,
        )
        logger.info(
            "Retrieved optimization job id=%s status=%s duration_ms=%.0f",
            result.id,
            result.status,
            (perf_counter() - started) * 1000,
        )
        return result

def list_optimization_jobs(
    *,
    limit: int | None = None,
    order: str | models.PageOrder | None = None,
    before: str | None = None,
    status: str | models.JobStatus | None = None,
    agent_name: str | None = None,
    allow_preview: bool = False,
    **kwargs: Any,
) -> list[models.OptimizationJobListItem]:
    started = perf_counter()
    logger.info(
        "Listing optimization jobs agent_name=%s status=%s limit=%s",
        agent_name,
        status,
        limit,
    )

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        result = list(
            client.beta.agents.list_optimization_jobs(
                limit=limit,
                order=order,
                before=before,
                status=status,
                agent_name=agent_name,
                **kwargs,
            )
        )
        logger.info(
            "Listed optimization jobs count=%d duration_ms=%.0f",
            len(result),
            (perf_counter() - started) * 1000,
        )
        return result

def cancel_optimization_job(
    job_id: str,
    *,
    allow_preview: bool = False,
    **kwargs: Any,
) -> models.OptimizationJob:
    started = perf_counter()
    logger.info("Cancelling optimization job id=%s", job_id)

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        result = client.beta.agents.cancel_optimization_job(
            job_id=job_id,
            **kwargs,
        )
        logger.info(
            "Cancelled optimization job id=%s status=%s duration_ms=%.0f",
            result.id,
            result.status,
            (perf_counter() - started) * 1000,
        )
        return result

def delete_optimization_job(
    job_id: str,
    *,
    allow_preview: bool = False,
    **kwargs: Any,
) -> None:
    started = perf_counter()
    logger.info("Deleting optimization job id=%s", job_id)

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        client.beta.agents.delete_optimization_job(
            job_id=job_id,
            **kwargs,
        )
        logger.info(
            "Deleted optimization job id=%s duration_ms=%.0f",
            job_id,
            (perf_counter() - started) * 1000,
        )

def _load_json_object(file_path: Path) -> dict[str, Any]:
    with file_path.open(encoding="utf-8") as source:
        value = json.load(source)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {file_path}")
    return value

def _write_chunks(file_path: Path, chunks: Iterator[bytes]) -> int:
    byte_count = 0
    with file_path.open("wb") as destination:
        for chunk in chunks:
            destination.write(chunk)
            byte_count += len(chunk)
    return byte_count

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-preview", action="store_true")
    commands = parser.add_subparsers(dest="command", required=True)

    create_version_command = commands.add_parser("create-agent-version")
    create_version_command.add_argument("-n", "--agent-name", required=True)
    create_version_command.add_argument(
        "--definition-file",
        type=Path,
        required=True,
    )
    create_version_command.add_argument("--metadata-file", type=Path)
    create_version_command.add_argument("--description")
    create_version_command.add_argument("--blueprint-reference-file", type=Path)
    create_version_command.add_argument(
        "--draft",
        action="store_true",
        default=None,
    )

    create_manifest_command = commands.add_parser("create-version-from-manifest")
    create_manifest_command.add_argument("-n", "--agent-name", required=True)
    create_manifest_command.add_argument("--manifest-id", required=True)
    create_manifest_command.add_argument(
        "--parameter-values-file",
        type=Path,
        required=True,
    )
    create_manifest_command.add_argument("--metadata-file", type=Path)
    create_manifest_command.add_argument("--description")

    create_code_command = commands.add_parser("create-version-from-code")
    create_code_command.add_argument("-n", "--agent-name", required=True)
    create_code_command.add_argument(
        "--definition-file",
        type=Path,
        required=True,
    )
    create_code_command.add_argument("--code-file", type=Path, required=True)
    create_code_command.add_argument("--code-zip-sha256")
    create_code_command.add_argument("--metadata-file", type=Path)
    create_code_command.add_argument("--description")

    download_code_command = commands.add_parser("download-code")
    download_code_command.add_argument("-n", "--agent-name", required=True)
    download_code_command.add_argument("-v", "--agent-version")
    download_code_command.add_argument("-o", "--output", type=Path, required=True)

    get_command = commands.add_parser("get-agent")
    get_command.add_argument("-n", "--agent-name", required=True)

    list_command = commands.add_parser("list-agents")
    list_command.add_argument("-k", "--kind", choices=("prompt", "hosted", "workflow", "external"),)

    list_command.add_argument("--limit", type=int)
    list_command.add_argument("--order", choices=("asc", "desc"))
    list_command.add_argument("--before")

    get_version_command = commands.add_parser("get-agent-version")
    get_version_command.add_argument("-n", "--agent-name", required=True)
    get_version_command.add_argument("-v", "--agent-version", required=True)

    list_versions_command = commands.add_parser("list-agent-versions")
    list_versions_command.add_argument("-n", "--agent-name", required=True)
    list_versions_command.add_argument("--limit", type=int)
    list_versions_command.add_argument("--order", choices=("asc", "desc"))
    list_versions_command.add_argument("--before")
    list_versions_command.add_argument(
        "--include-drafts",
        action="store_true",
        default=None,
    )

    enable_command = commands.add_parser("enable-agent")
    enable_command.add_argument("-n", "--agent-name", required=True)

    disable_command = commands.add_parser("disable-agent")
    disable_command.add_argument("-n", "--agent-name", required=True)

    delete_command = commands.add_parser("delete-agent")
    delete_command.add_argument("-n", "--agent-name", required=True)
    delete_command.add_argument("--force", action="store_true", default=None)

    delete_version_command = commands.add_parser("delete-agent-version")
    delete_version_command.add_argument("-n", "--agent-name", required=True)
    delete_version_command.add_argument("-v", "--agent-version", required=True)
    delete_version_command.add_argument(
        "--force",
        action="store_true",
        default=None,
    )

    create_session_command = commands.add_parser("create-session")
    create_session_command.add_argument("-n", "--agent-name", required=True)
    create_session_command.add_argument(
        "--version-indicator-file",
        type=Path,
        required=True,
    )
    create_session_command.add_argument("--session-id")

    get_session_command = commands.add_parser("get-session")
    get_session_command.add_argument("-n", "--agent-name", required=True)
    get_session_command.add_argument("--session-id", required=True)

    list_sessions_command = commands.add_parser("list-sessions")
    list_sessions_command.add_argument("-n", "--agent-name", required=True)
    list_sessions_command.add_argument("--limit", type=int)
    list_sessions_command.add_argument("--order", choices=("asc", "desc"))
    list_sessions_command.add_argument("--before")

    stop_session_command = commands.add_parser("stop-session")
    stop_session_command.add_argument("-n", "--agent-name", required=True)
    stop_session_command.add_argument("--session-id", required=True)

    delete_session_command = commands.add_parser("delete-session")
    delete_session_command.add_argument("-n", "--agent-name", required=True)
    delete_session_command.add_argument("--session-id", required=True)

    session_log_command = commands.add_parser("get-session-log-stream")
    session_log_command.add_argument("-n", "--agent-name", required=True)
    session_log_command.add_argument("-v", "--agent-version", required=True)
    session_log_command.add_argument("--session-id", required=True)
    session_log_command.add_argument("-o", "--output", type=Path, required=True)

    list_session_files_command = commands.add_parser("list-session-files")
    list_session_files_command.add_argument("-n", "--agent-name", required=True)
    list_session_files_command.add_argument("--session-id", required=True)
    list_session_files_command.add_argument("--path")
    list_session_files_command.add_argument("--limit", type=int)
    list_session_files_command.add_argument("--order", choices=("asc", "desc"))
    list_session_files_command.add_argument("--before")

    upload_session_file_command = commands.add_parser("upload-session-file")
    upload_session_file_command.add_argument("-n", "--agent-name", required=True)
    upload_session_file_command.add_argument("--session-id", required=True)
    upload_session_file_command.add_argument("--source", type=Path, required=True)
    upload_session_file_command.add_argument("--path", required=True)

    download_session_file_command = commands.add_parser("download-session-file")
    download_session_file_command.add_argument("-n", "--agent-name", required=True)
    download_session_file_command.add_argument("--session-id", required=True)
    download_session_file_command.add_argument("--path", required=True)
    download_session_file_command.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
    )

    delete_session_file_command = commands.add_parser("delete-session-file")
    delete_session_file_command.add_argument("-n", "--agent-name", required=True)
    delete_session_file_command.add_argument("--session-id", required=True)
    delete_session_file_command.add_argument("--path", required=True)
    delete_session_file_command.add_argument(
        "--recursive",
        action="store_true",
        default=None,
    )

    create_optimization_command = commands.add_parser(
        "begin-create-optimization-job"
    )
    create_optimization_command.add_argument(
        "--job-file",
        type=Path,
        required=True,
    )
    create_optimization_command.add_argument("--operation-id")
    create_optimization_command.add_argument("--polling-interval", type=int)

    get_optimization_command = commands.add_parser("get-optimization-job")
    get_optimization_command.add_argument("--job-id", required=True)

    list_optimization_command = commands.add_parser("list-optimization-jobs")
    list_optimization_command.add_argument("--limit", type=int)
    list_optimization_command.add_argument("--order", choices=("asc", "desc"))
    list_optimization_command.add_argument("--before")
    list_optimization_command.add_argument(
        "--status",
        choices=("queued", "in_progress", "succeeded", "failed", "cancelled"),
    )
    list_optimization_command.add_argument("--agent-name")

    cancel_optimization_command = commands.add_parser(
        "cancel-optimization-job"
    )
    cancel_optimization_command.add_argument("--job-id", required=True)

    delete_optimization_command = commands.add_parser(
        "delete-optimization-job"
    )
    delete_optimization_command.add_argument("--job-id", required=True)

    args = parser.parse_args()

    try:
        if args.command == "create-agent-version":
            metadata = (
                cast(
                    dict[str, str],
                    _load_json_object(args.metadata_file),
                )
                if args.metadata_file
                else None
            )
            blueprint_reference = (
                models.AgentBlueprintReference(
                    _load_json_object(args.blueprint_reference_file)
                )
                if args.blueprint_reference_file
                else None
            )
            result = create_agent_version(
                agent_name=args.agent_name,
                definition=models.AgentDefinition(
                    _load_json_object(args.definition_file)
                ),
                metadata=metadata,
                description=args.description,
                blueprint_reference=blueprint_reference,
                draft=args.draft,
                allow_preview=args.allow_preview,
            )
            output = result.as_dict()
        elif args.command == "create-version-from-manifest":
            metadata = (
                cast(
                    dict[str, str],
                    _load_json_object(args.metadata_file),
                )
                if args.metadata_file
                else None
            )
            result = create_version_from_manifest(
                agent_name=args.agent_name,
                manifest_id=args.manifest_id,
                parameter_values=_load_json_object(args.parameter_values_file),
                metadata=metadata,
                description=args.description,
                allow_preview=args.allow_preview,
            )
            output = result.as_dict()
        elif args.command == "create-version-from-code":
            metadata = (
                cast(
                    dict[str, str],
                    _load_json_object(args.metadata_file),
                )
                if args.metadata_file
                else None
            )
            definition = models.HostedAgentDefinition(
                _load_json_object(args.definition_file)
            )
            with args.code_file.open("rb") as code:
                result = create_version_from_code(
                    agent_name=args.agent_name,
                    definition=definition,
                    code=code,
                    code_zip_sha256=args.code_zip_sha256,
                    metadata=metadata,
                    description=args.description,
                    allow_preview=args.allow_preview,
                )
            output = result.as_dict()
        elif args.command == "download-code":
            byte_count = _write_chunks(
                args.output,
                download_code(
                    agent_name=args.agent_name,
                    agent_version=args.agent_version,
                    allow_preview=args.allow_preview,
                ),
            )
            output = {
                "agent_name": args.agent_name,
                "agent_version": args.agent_version,
                "output": str(args.output),
                "bytes": byte_count,
            }
        elif args.command == "get-agent":
            result = get_agent(
                agent_name=args.agent_name,
                allow_preview=args.allow_preview,
            )
            output = result.as_dict()
        elif args.command == "list-agents":
            result = list_agents(
                kind=args.kind,
                limit=args.limit,
                order=args.order,
                before=args.before,
                allow_preview=args.allow_preview,
            )
            output = [agent.as_dict() for agent in result]
        elif args.command == "get-agent-version":
            result = get_agent_version(
                agent_name=args.agent_name,
                agent_version=args.agent_version,
                allow_preview=args.allow_preview,
            )
            output = result.as_dict()
        elif args.command == "list-agent-versions":
            result = list_agent_versions(
                agent_name=args.agent_name,
                limit=args.limit,
                order=args.order,
                before=args.before,
                include_drafts=args.include_drafts,
                allow_preview=args.allow_preview,
            )
            output = [version.as_dict() for version in result]
        elif args.command == "enable-agent":
            enable_agent(
                agent_name=args.agent_name,
                allow_preview=args.allow_preview,
            )
            output = {"agent_name": args.agent_name, "enabled": True}
        elif args.command == "disable-agent":
            disable_agent(
                agent_name=args.agent_name,
                allow_preview=args.allow_preview,
            )
            output = {"agent_name": args.agent_name, "enabled": False}
        elif args.command == "delete-agent":
            result = delete_agent(
                agent_name=args.agent_name,
                force=args.force,
                allow_preview=args.allow_preview,
            )
            output = result.as_dict()
        elif args.command == "delete-agent-version":
            result = delete_agent_version(
                agent_name=args.agent_name,
                agent_version=args.agent_version,
                force=args.force,
                allow_preview=args.allow_preview,
            )
            output = result.as_dict()
        elif args.command == "create-session":
            result = create_session(
                agent_name=args.agent_name,
                version_indicator=models.VersionIndicator(
                    _load_json_object(args.version_indicator_file)
                ),
                agent_session_id=args.session_id,
                allow_preview=args.allow_preview,
            )
            output = result.as_dict()
        elif args.command == "get-session":
            result = get_session(
                agent_name=args.agent_name,
                session_id=args.session_id,
                allow_preview=args.allow_preview,
            )
            output = result.as_dict()
        elif args.command == "list-sessions":
            result = list_sessions(
                agent_name=args.agent_name,
                limit=args.limit,
                order=args.order,
                before=args.before,
                allow_preview=args.allow_preview,
            )
            output = [session.as_dict() for session in result]
        elif args.command == "stop-session":
            stop_session(
                agent_name=args.agent_name,
                session_id=args.session_id,
                allow_preview=args.allow_preview,
            )
            output = {"session_id": args.session_id, "stopped": True}
        elif args.command == "delete-session":
            delete_session(
                agent_name=args.agent_name,
                session_id=args.session_id,
                allow_preview=args.allow_preview,
            )
            output = {"session_id": args.session_id, "deleted": True}
        elif args.command == "get-session-log-stream":
            byte_count = _write_chunks(
                args.output,
                get_session_log_stream(
                    agent_name=args.agent_name,
                    agent_version=args.agent_version,
                    session_id=args.session_id,
                    allow_preview=args.allow_preview,
                ),
            )
            output = {
                "session_id": args.session_id,
                "output": str(args.output),
                "bytes": byte_count,
            }
        elif args.command == "list-session-files":
            result = list_session_files(
                agent_name=args.agent_name,
                session_id=args.session_id,
                path=args.path,
                limit=args.limit,
                order=args.order,
                before=args.before,
                allow_preview=args.allow_preview,
            )
            output = [entry.as_dict() for entry in result]
        elif args.command == "upload-session-file":
            result = upload_session_file(
                agent_name=args.agent_name,
                session_id=args.session_id,
                content=args.source.read_bytes(),
                path=args.path,
                allow_preview=args.allow_preview,
            )
            output = result.as_dict()
        elif args.command == "download-session-file":
            byte_count = _write_chunks(
                args.output,
                download_session_file(
                    agent_name=args.agent_name,
                    session_id=args.session_id,
                    path=args.path,
                    allow_preview=args.allow_preview,
                ),
            )
            output = {
                "session_id": args.session_id,
                "path": args.path,
                "output": str(args.output),
                "bytes": byte_count,
            }
        elif args.command == "delete-session-file":
            delete_session_file(
                agent_name=args.agent_name,
                session_id=args.session_id,
                path=args.path,
                recursive=args.recursive,
                allow_preview=args.allow_preview,
            )
            output = {
                "session_id": args.session_id,
                "path": args.path,
                "deleted": True,
            }
        elif args.command == "begin-create-optimization-job":
            with args.job_file.open(encoding="utf-8") as job_file:
                job = models.OptimizationJob(json.load(job_file))
            result = begin_create_optimization_job(
                job=job,
                operation_id=args.operation_id,
                polling_interval=args.polling_interval,
                allow_preview=args.allow_preview,
            )
            output = result.as_dict()
        elif args.command == "get-optimization-job":
            result = get_optimization_job(
                job_id=args.job_id,
                allow_preview=args.allow_preview,
            )
            output = result.as_dict()
        elif args.command == "list-optimization-jobs":
            result = list_optimization_jobs(
                limit=args.limit,
                order=args.order,
                before=args.before,
                status=args.status,
                agent_name=args.agent_name,
                allow_preview=args.allow_preview,
            )
            output = [job.as_dict() for job in result]
        elif args.command == "cancel-optimization-job":
            result = cancel_optimization_job(
                job_id=args.job_id,
                allow_preview=args.allow_preview,
            )
            output = result.as_dict()
        elif args.command == "delete-optimization-job":
            delete_optimization_job(
                job_id=args.job_id,
                allow_preview=args.allow_preview,
            )
            output = {"job_id": args.job_id, "deleted": True}
        else:
            raise ValueError(f"Unsupported agent command: {args.command}")
    except Exception:
        logger.exception("Agent command failed command=%s", args.command)
        raise SystemExit(1)

    print(json.dumps(output, indent=2, default=str))

if __name__ == "__main__":
    main()