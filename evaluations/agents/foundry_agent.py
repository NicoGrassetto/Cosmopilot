"""
Foundry Agent target adapter.

Wraps any Azure AI Foundry agent (by name) into the AgentTarget protocol
so it can be used with the evaluation runner.
"""

import os
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient


class FoundryAgentTarget:
    """Wraps an Azure AI Foundry agent as an evaluation target.

    Args:
        agent_name: The name of the deployed agent in Foundry.
        endpoint: Azure AI project endpoint (defaults to AZURE_AI_PROJECT_ENDPOINT env var).
    """

    def __init__(self, agent_name: str, endpoint: str | None = None):
        self.name = agent_name
        self._endpoint = endpoint or os.environ["AZURE_AI_PROJECT_ENDPOINT"]
        self._client = AIProjectClient(
            endpoint=self._endpoint,
            credential=DefaultAzureCredential(),
        )
        self._openai_client = self._client.get_openai_client()

    def __call__(self, query: str, **kwargs) -> dict:
        """Run the agent on a single query and return structured output."""
        conversation = self._openai_client.conversations.create()

        self._openai_client.conversations.items.create(
            conversation_id=conversation.id,
            items=[{
                "type": "message",
                "role": "user",
                "content": query,
            }],
        )

        response = self._openai_client.responses.create(
            conversation=conversation.id,
            extra_body={"agent_reference": {"name": self.name, "type": "agent_reference"}},
            input="",
        )

        try:
            response_text = response.output[0].content[0].text
        except (IndexError, AttributeError):
            response_text = str(response)

        return {"response": response_text}
