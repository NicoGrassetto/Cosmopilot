import os
from uuid import uuid4

import pytest
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    CreateTelephonyCallJobRequest,
    CreateTwilioTelephonyBindingRequest,
    PSTNTelephonyTransferDestination,
    TelephonyOutboundDestination,
    TelephonyOutboundDestinationType,
    TelephonyTransferTarget,
    UpdateTelephonyBindingRequest,
    VoiceAgentDefinition,
)
from azure.core import MatchConditions
from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential


@pytest.mark.integration
def test_cancel_call_job():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            client.beta.voice_agents.telephony.cancel_call_job(
                agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                call_job_id=f"pytest-call-job-{uuid4().hex[:8]}",
                etag="*",
                match_condition=MatchConditions.Unconditionally,
            )


@pytest.mark.integration
def test_connect():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        connection_manager = client.beta.voice_agents.realtime.connect(
            agent_name="weather-agent",
        )

        assert connection_manager is not None


@pytest.mark.integration
def test_create_binding():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            client.beta.voice_agents.telephony.create_binding(
                agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                telephony_binding=CreateTwilioTelephonyBindingRequest(
                    connection_name=f"pytest-connection-{uuid4().hex[:8]}",
                    label="Temporary binding created by pytest.",
                ),
            )


@pytest.mark.integration
def test_create_call_job():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            client.beta.voice_agents.telephony.create_call_job(
                agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                body=CreateTelephonyCallJobRequest(
                    destination=TelephonyOutboundDestination(
                        type=TelephonyOutboundDestinationType.PHONE_NUMBER,
                        value="+15555550100",
                    ),
                    connection_name=f"pytest-connection-{uuid4().hex[:8]}",
                    source="+15555550101",
                ),
                idempotency_key=uuid4().hex,
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
        with pytest.raises(ResourceNotFoundError):
            client.beta.voice_agents.conversations.delete(
                agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                conversation_id=f"pytest-conversation-{uuid4().hex[:8]}",
            )


@pytest.mark.integration
def test_delete_binding():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            client.beta.voice_agents.telephony.delete_binding(
                agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                binding_id=f"pytest-binding-{uuid4().hex[:8]}",
                etag="*",
                match_condition=MatchConditions.Unconditionally,
            )


@pytest.mark.integration
def test_download_audio():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            b"".join(
                client.beta.voice_agents.conversations.download_audio(
                    agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                    conversation_id=f"pytest-conversation-{uuid4().hex[:8]}",
                )
            )


@pytest.mark.integration
def test_download_audio_item():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            b"".join(
                client.beta.voice_agents.conversations.download_audio_item(
                    agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                    conversation_id=f"pytest-conversation-{uuid4().hex[:8]}",
                    item_id=f"pytest-item-{uuid4().hex[:8]}",
                )
            )


@pytest.mark.integration
def test_download_generated_audio_item():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            b"".join(
                client.beta.voice_agents.conversations.download_generated_audio_item(
                    agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                    conversation_id=f"pytest-conversation-{uuid4().hex[:8]}",
                    item_id=f"pytest-item-{uuid4().hex[:8]}",
                )
            )


@pytest.mark.integration
def test_end_call():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            client.beta.voice_agents.telephony.end_call(
                agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                call_id=f"pytest-call-{uuid4().hex[:8]}",
            )


@pytest.mark.integration
def test_get():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            client.beta.voice_agents.conversations.get(
                agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                conversation_id=f"pytest-conversation-{uuid4().hex[:8]}",
            )


@pytest.mark.integration
def test_get_audio():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            client.beta.voice_agents.conversations.get_audio(
                agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                conversation_id=f"pytest-conversation-{uuid4().hex[:8]}",
            )


@pytest.mark.integration
def test_get_audio_item():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            client.beta.voice_agents.conversations.get_audio_item(
                agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                conversation_id=f"pytest-conversation-{uuid4().hex[:8]}",
                item_id=f"pytest-item-{uuid4().hex[:8]}",
            )


@pytest.mark.integration
def test_get_binding():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            client.beta.voice_agents.telephony.get_binding(
                agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                binding_id=f"pytest-binding-{uuid4().hex[:8]}",
            )


@pytest.mark.integration
def test_get_call():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            client.beta.voice_agents.telephony.get_call(
                agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                call_id=f"pytest-call-{uuid4().hex[:8]}",
            )


@pytest.mark.integration
def test_get_call_job():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            client.beta.voice_agents.telephony.get_call_job(
                agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                call_job_id=f"pytest-call-job-{uuid4().hex[:8]}",
            )


@pytest.mark.integration
def test_get_generated_audio_item():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            client.beta.voice_agents.conversations.get_generated_audio_item(
                agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                conversation_id=f"pytest-conversation-{uuid4().hex[:8]}",
                item_id=f"pytest-item-{uuid4().hex[:8]}",
            )


@pytest.mark.integration
def test_get_item():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            client.beta.voice_agents.conversations.get_item(
                agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                conversation_id=f"pytest-conversation-{uuid4().hex[:8]}",
                item_id=f"pytest-item-{uuid4().hex[:8]}",
            )


@pytest.mark.integration
def test_get_response():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            client.beta.voice_agents.conversations.get_response(
                agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                conversation_id=f"pytest-conversation-{uuid4().hex[:8]}",
                response_id=f"pytest-response-{uuid4().hex[:8]}",
            )


@pytest.mark.integration
def test_get_transfer_targets():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=True,
        ) as client,
    ):
        agent_name = f"pytest-agent-{uuid4().hex[:8]}"
        client.agents.create_version(
            agent_name=agent_name,
            definition=VoiceAgentDefinition(
                instructions="Greet the caller and stop.",
            ),
        )

        try:
            transfer_targets = client.beta.voice_agents.telephony.get_transfer_targets(
                agent_name=agent_name,
            )

            assert transfer_targets is not None
        finally:
            client.agents.delete(agent_name=agent_name)


@pytest.mark.integration
def test_list():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=True,
        ) as client,
    ):
        agent_name = f"pytest-agent-{uuid4().hex[:8]}"
        client.agents.create_version(
            agent_name=agent_name,
            definition=VoiceAgentDefinition(
                instructions="Greet the caller and stop.",
            ),
        )

        try:
            listed_conversations = list(
                client.beta.voice_agents.conversations.list(agent_name=agent_name)
            )

            assert isinstance(listed_conversations, list)
        finally:
            client.agents.delete(agent_name=agent_name)


@pytest.mark.integration
def test_list_bindings():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=True,
        ) as client,
    ):
        agent_name = f"pytest-agent-{uuid4().hex[:8]}"
        client.agents.create_version(
            agent_name=agent_name,
            definition=VoiceAgentDefinition(
                instructions="Greet the caller and stop.",
            ),
        )

        try:
            listed_bindings = list(
                client.beta.voice_agents.telephony.list_bindings(agent_name=agent_name)
            )

            assert isinstance(listed_bindings, list)
        finally:
            client.agents.delete(agent_name=agent_name)


@pytest.mark.integration
def test_list_calls():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=True,
        ) as client,
    ):
        agent_name = f"pytest-agent-{uuid4().hex[:8]}"
        client.agents.create_version(
            agent_name=agent_name,
            definition=VoiceAgentDefinition(
                instructions="Greet the caller and stop.",
            ),
        )

        try:
            listed_calls = list(
                client.beta.voice_agents.telephony.list_calls(agent_name=agent_name)
            )

            assert isinstance(listed_calls, list)
        finally:
            client.agents.delete(agent_name=agent_name)


@pytest.mark.integration
def test_list_items():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            list(
                client.beta.voice_agents.conversations.list_items(
                    agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                    conversation_id=f"pytest-conversation-{uuid4().hex[:8]}",
                )
            )


@pytest.mark.integration
def test_list_response_items():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            list(
                client.beta.voice_agents.conversations.list_response_items(
                    agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                    conversation_id=f"pytest-conversation-{uuid4().hex[:8]}",
                    response_id=f"pytest-response-{uuid4().hex[:8]}",
                )
            )


@pytest.mark.integration
def test_list_responses():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            list(
                client.beta.voice_agents.conversations.list_responses(
                    agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                    conversation_id=f"pytest-conversation-{uuid4().hex[:8]}",
                )
            )


@pytest.mark.integration
def test_replace_transfer_targets():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=True,
        ) as client,
    ):
        agent_name = f"pytest-agent-{uuid4().hex[:8]}"
        client.agents.create_version(
            agent_name=agent_name,
            definition=VoiceAgentDefinition(
                instructions="Greet the caller and stop.",
            ),
        )

        try:
            replaced_transfer_targets = (
                client.beta.voice_agents.telephony.replace_transfer_targets(
                    agent_name=agent_name,
                    transfer_targets=[
                        TelephonyTransferTarget(
                            name="pytest",
                            description="Temporary transfer target created by pytest.",
                            destination=PSTNTelephonyTransferDestination(
                                value="+15555550100",
                            ),
                        )
                    ],
                    etag="*",
                    match_condition=MatchConditions.IfPresent,
                )
            )

            assert replaced_transfer_targets is not None
        finally:
            client.agents.delete(agent_name=agent_name)


@pytest.mark.integration
def test_transfer_call():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            client.beta.voice_agents.telephony.transfer_call(
                agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                call_id=f"pytest-call-{uuid4().hex[:8]}",
                target="pytest",
            )


@pytest.mark.integration
def test_update_binding():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            client.beta.voice_agents.telephony.update_binding(
                agent_name=f"pytest-agent-{uuid4().hex[:8]}",
                binding_id=f"pytest-binding-{uuid4().hex[:8]}",
                body=UpdateTelephonyBindingRequest(
                    label="Temporary binding updated by pytest.",
                ),
                etag="*",
                match_condition=MatchConditions.Unconditionally,
            )
