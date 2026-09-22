import os
import tempfile
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

import pytest
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    AgentEndpointConfig,
    AgentOptimizationDatasetItem,
    AgentOptimizationEvaluatorRef,
    AgentOptimizationInlineDatasetInput,
    AgentOptimizationJob,
    AgentOptimizationJobInputs,
    CodeConfiguration,
    CodeDependencyResolution,
    FixedRatioVersionSelectionRule,
    GenerateVoiceAgentRequest,
    HostedAgentDefinition,
    Microsoft365PublishScope,
    OptimizedAgentIdentifier,
    PromptAgentDefinition,
    ProtocolVersionRecord,
    VersionRefIndicator,
    VersionSelector,
)
from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential


@pytest.mark.integration
def test_begin_create_optimization_job():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            client.beta.agents.begin_create_optimization_job(
                job=AgentOptimizationJob(
                    inputs=AgentOptimizationJobInputs(
                        agent=OptimizedAgentIdentifier(
                            agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                        ),
                        train_dataset=AgentOptimizationInlineDatasetInput(
                            dataset_items=[
                                AgentOptimizationDatasetItem(
                                    query="What is the weather in Paris?",
                                    ground_truth="It is sunny in Paris.",
                                )
                            ],
                        ),
                        evaluators=[AgentOptimizationEvaluatorRef(name="relevance")],
                    ),
                ),
            )


@pytest.mark.integration
def test_cancel_optimization_job():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            client.beta.agents.cancel_optimization_job(
                job_id=f"pytest-job-{uuid4().hex[:8]}",
            )


@pytest.mark.integration
def test_create_from_prompt():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        agent_name = f"pytest-agent-{uuid4().hex[:8]}"

        try:
            created_agent = client.beta.agents.create_from_prompt(
                body=GenerateVoiceAgentRequest(
                    name=agent_name,
                    goal="Tell the caller the weather and hang up.",
                    description="Temporary agent created by pytest.",
                    draft=True,
                ),
            )

            assert created_agent is not None
        finally:
            client.agents.delete(agent_name=agent_name)


@pytest.mark.integration
def test_create_session():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            client.agents.create_session(
                agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                version_indicator=VersionRefIndicator(agent_version="1"),
            )


@pytest.mark.integration
def test_create_version():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        agent_name = f"pytest-agent-{uuid4().hex[:8]}"

        try:
            created_agent_version = client.agents.create_version(
                agent_name=agent_name,
                definition=PromptAgentDefinition(
                    model=os.environ["AZURE_DEPLOYMENT_NAME"],
                    instructions="Answer the question and stop.",
                ),
                description="Temporary agent created by pytest.",
            )

            assert created_agent_version is not None
        finally:
            client.agents.delete(agent_name=agent_name)


@pytest.mark.integration
def test_create_version_from_code():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
        tempfile.TemporaryDirectory() as directory,
    ):
        agent_name = f"pytest-agent-{uuid4().hex[:8]}"
        entry_point_file = Path(directory) / "main.py"
        entry_point_file.write_text("print('pytest')\n")
        code_archive = Path(directory) / "code.zip"
        with ZipFile(code_archive, "w") as archive:
            archive.write(entry_point_file, "main.py")

        try:
            with code_archive.open("rb") as code:
                created_agent_version = client.agents.create_version_from_code(
                    agent_name=agent_name,
                    definition=HostedAgentDefinition(
                        cpu="0.5",
                        memory="1Gi",
                        code_configuration=CodeConfiguration(
                            runtime="python_3_14",
                            entry_point=["python", "main.py"],
                            dependency_resolution=CodeDependencyResolution.REMOTE_BUILD,
                        ),
                        protocol_versions=[
                            ProtocolVersionRecord(protocol="responses", version="2.0.0")
                        ],
                    ),
                    code=code,
                    description="Temporary agent created by pytest.",
                )

            assert created_agent_version is not None
        finally:
            client.agents.delete(agent_name=agent_name, force=True)


@pytest.mark.integration
def test_create_version_from_manifest():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            client.agents.create_version_from_manifest(
                agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                manifest_id=f"pytest-manifest-{uuid4().hex[:8]}",
                parameter_values={},
            )


@pytest.mark.integration
def test_delete():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        agent_name = f"pytest-agent-{uuid4().hex[:8]}"
        client.agents.create_version(
            agent_name=agent_name,
            definition=PromptAgentDefinition(
                model=os.environ["AZURE_DEPLOYMENT_NAME"],
                instructions="Answer the question and stop.",
            ),
        )

        deleted_agent = client.agents.delete(agent_name=agent_name)

        assert deleted_agent is not None


@pytest.mark.integration
def test_delete_optimization_job():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            client.beta.agents.delete_optimization_job(
                job_id=f"pytest-job-{uuid4().hex[:8]}",
            )


@pytest.mark.integration
def test_delete_session():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            client.agents.delete_session(
                agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                session_id=f"pytest-session-{uuid4().hex[:8]}",
            )


@pytest.mark.integration
def test_delete_session_file():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            client.agents.delete_session_file(
                agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                session_id=f"pytest-session-{uuid4().hex[:8]}",
                path="pytest.txt",
            )


@pytest.mark.integration
def test_delete_version():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        agent_name = f"pytest-agent-{uuid4().hex[:8]}"
        client.agents.create_version(
            agent_name=agent_name,
            definition=PromptAgentDefinition(
                model=os.environ["AZURE_DEPLOYMENT_NAME"],
                instructions="Answer the question and stop.",
            ),
        )
        second_agent_version = client.agents.create_version(
            agent_name=agent_name,
            definition=PromptAgentDefinition(
                model=os.environ["AZURE_DEPLOYMENT_NAME"],
                instructions="Answer the question briefly and stop.",
            ),
        )

        try:
            deleted_agent_version = client.agents.delete_version(
                agent_name=agent_name,
                agent_version=second_agent_version.version,
            )

            assert deleted_agent_version is not None
        finally:
            client.agents.delete(agent_name=agent_name)


@pytest.mark.integration
def test_disable():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        agent_name = f"pytest-agent-{uuid4().hex[:8]}"
        client.agents.create_version(
            agent_name=agent_name,
            definition=PromptAgentDefinition(
                model=os.environ["AZURE_DEPLOYMENT_NAME"],
                instructions="Answer the question and stop.",
            ),
        )

        try:
            disabled_agent = client.agents.disable(agent_name=agent_name)

            assert disabled_agent is None
        finally:
            client.agents.delete(agent_name=agent_name)


@pytest.mark.integration
def test_download_code():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            b"".join(
                client.agents.download_code(
                    agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                )
            )


@pytest.mark.integration
def test_download_session_file():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            b"".join(
                client.agents.download_session_file(
                    agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                    session_id=f"pytest-session-{uuid4().hex[:8]}",
                    path="pytest.txt",
                )
            )


@pytest.mark.integration
def test_enable():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        agent_name = f"pytest-agent-{uuid4().hex[:8]}"
        client.agents.create_version(
            agent_name=agent_name,
            definition=PromptAgentDefinition(
                model=os.environ["AZURE_DEPLOYMENT_NAME"],
                instructions="Answer the question and stop.",
            ),
        )
        client.agents.disable(agent_name=agent_name)

        try:
            enabled_agent = client.agents.enable(agent_name=agent_name)

            assert enabled_agent is None
        finally:
            client.agents.delete(agent_name=agent_name)


@pytest.mark.integration
def test_get():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        agent_name = f"pytest-agent-{uuid4().hex[:8]}"
        client.agents.create_version(
            agent_name=agent_name,
            definition=PromptAgentDefinition(
                model=os.environ["AZURE_DEPLOYMENT_NAME"],
                instructions="Answer the question and stop.",
            ),
        )

        try:
            retrieved_agent = client.agents.get(agent_name=agent_name)

            assert retrieved_agent is not None
        finally:
            client.agents.delete(agent_name=agent_name)


@pytest.mark.integration
def test_get_microsoft365_package():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            b"".join(
                client.agents.get_microsoft365_package(
                    agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                    publish_scope=Microsoft365PublishScope.PERSONAL,
                )
            )


@pytest.mark.integration
def test_get_microsoft365_publish_defaults():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        agent_name = f"pytest-agent-{uuid4().hex[:8]}"
        client.agents.create_version(
            agent_name=agent_name,
            definition=PromptAgentDefinition(
                model=os.environ["AZURE_DEPLOYMENT_NAME"],
                instructions="Answer the question and stop.",
            ),
        )

        try:
            publish_defaults = client.agents.get_microsoft365_publish_defaults(
                agent_name=agent_name,
            )

            assert publish_defaults is not None
        finally:
            client.agents.delete(agent_name=agent_name)


@pytest.mark.integration
def test_get_optimization_job():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            client.beta.agents.get_optimization_job(
                job_id=f"pytest-job-{uuid4().hex[:8]}",
            )


@pytest.mark.integration
def test_get_session():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            client.agents.get_session(
                agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                session_id=f"pytest-session-{uuid4().hex[:8]}",
            )


@pytest.mark.integration
def test_get_session_log_stream():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            client.agents.get_session_log_stream(
                agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                agent_version="1",
                session_id=f"pytest-session-{uuid4().hex[:8]}",
            )


@pytest.mark.integration
def test_get_version():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        agent_name = f"pytest-agent-{uuid4().hex[:8]}"
        client.agents.create_version(
            agent_name=agent_name,
            definition=PromptAgentDefinition(
                model=os.environ["AZURE_DEPLOYMENT_NAME"],
                instructions="Answer the question and stop.",
            ),
        )

        try:
            retrieved_agent_version = client.agents.get_version(
                agent_name=agent_name,
                agent_version="1",
            )

            assert retrieved_agent_version is not None
        finally:
            client.agents.delete(agent_name=agent_name)


@pytest.mark.integration
def test_list():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        listed_agents = list(client.agents.list())

        assert isinstance(listed_agents, list)


@pytest.mark.integration
def test_list_optimization_jobs():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        listed_optimization_jobs = list(client.beta.agents.list_optimization_jobs())

        assert isinstance(listed_optimization_jobs, list)


@pytest.mark.integration
def test_list_session_files():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            list(
                client.agents.list_session_files(
                    agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                    session_id=f"pytest-session-{uuid4().hex[:8]}",
                )
            )


@pytest.mark.integration
def test_list_sessions():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        agent_name = f"pytest-agent-{uuid4().hex[:8]}"
        client.agents.create_version(
            agent_name=agent_name,
            definition=PromptAgentDefinition(
                model=os.environ["AZURE_DEPLOYMENT_NAME"],
                instructions="Answer the question and stop.",
            ),
        )

        try:
            listed_sessions = list(client.agents.list_sessions(agent_name=agent_name))

            assert isinstance(listed_sessions, list)
        finally:
            client.agents.delete(agent_name=agent_name)


@pytest.mark.integration
def test_list_versions():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        agent_name = f"pytest-agent-{uuid4().hex[:8]}"
        client.agents.create_version(
            agent_name=agent_name,
            definition=PromptAgentDefinition(
                model=os.environ["AZURE_DEPLOYMENT_NAME"],
                instructions="Answer the question and stop.",
            ),
        )

        try:
            agent_versions = list(client.agents.list_versions(agent_name=agent_name))

            assert isinstance(agent_versions, list)
        finally:
            client.agents.delete(agent_name=agent_name)


@pytest.mark.integration
def test_publish_to_microsoft365():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            client.agents.publish_to_microsoft365(
                agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                publish_scope=Microsoft365PublishScope.PERSONAL,
            )


@pytest.mark.integration
def test_stop_session():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            client.agents.stop_session(
                agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                session_id=f"pytest-session-{uuid4().hex[:8]}",
            )


@pytest.mark.integration
def test_update_details():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        agent_name = f"pytest-agent-{uuid4().hex[:8]}"
        client.agents.create_version(
            agent_name=agent_name,
            definition=PromptAgentDefinition(
                model=os.environ["AZURE_DEPLOYMENT_NAME"],
                instructions="Answer the question and stop.",
            ),
        )

        try:
            updated_agent = client.agents.update_details(
                agent_name=agent_name,
                agent_endpoint=AgentEndpointConfig(
                    version_selector=VersionSelector(
                        version_selection_rules=[
                            FixedRatioVersionSelectionRule(
                                agent_version="1",
                                traffic_percentage=100,
                            )
                        ],
                    ),
                ),
            )

            assert updated_agent is not None
        finally:
            client.agents.delete(agent_name=agent_name)


@pytest.mark.integration
def test_upload_session_file():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            client.agents.upload_session_file(
                agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                session_id=f"pytest-session-{uuid4().hex[:8]}",
                content=b"pytest",
                path="pytest.txt",
            )
