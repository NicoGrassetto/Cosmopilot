from __future__ import annotations

import os
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, Tool
from azure.identity import DefaultAzureCredential

import logging

logger = logging.getLogger(__name__)

def create(name: str, instructions: str, description: str, tools: list[Tool] | None = None, temperature: float = 0.4, top_p: float = 0.95):
    endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
    credential = DefaultAzureCredential()
    client = AIProjectClient(endpoint=endpoint, credential=credential)
    agent = client.agents.create_version(
        agent_name=name,
        definition=PromptAgentDefinition(
            model=os.environ["AZURE_DEPLOYMENT_NAME"],
            instructions=instructions,
            tools=tools,
            temperature=temperature,
            top_p=top_p,
        ),
        description=description,
    )

    logger.info("Created agent: %s (version=%s)", agent.name, agent.version)


def run(name: str, prompt: str) -> str:
    endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
    credential = DefaultAzureCredential()
    client = AIProjectClient(endpoint=endpoint, credential=credential)

    openai = client.get_openai_client(agent_name=name)

    response = openai.responses.create(input=prompt)
    return response.output_text