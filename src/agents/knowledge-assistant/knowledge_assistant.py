"""Create the knowledge-assistant prompt agent in Azure AI Foundry.

Tools: azure_ai_search, sharepoint_grounding_preview, work_iq_preview,
memory_search_preview.

Env vars:
    AZURE_AI_PROJECT_ENDPOINT   Foundry project endpoint
    AZURE_DEPLOYMENT_NAME       Chat model deployment (e.g. gpt-4-1-nano)
    SHAREPOINT_CONNECTION_ID    Foundry connection id for SharePoint grounding
    WORK_IQ_CONNECTION_ID       Foundry connection id for Work IQ
    MEMORY_STORE_NAME           Name of the memory store

Auth: DefaultAzureCredential (run `az login` first).
Note: these grounding tools require the matching connections in the project.
"""

import os
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    AzureAISearchTool,
    AzureAISearchToolResource,
    MemorySearchPreviewTool,
    PromptAgentDefinition,
    SharepointGroundingToolParameters,
    SharepointPreviewTool,
    WorkIQPreviewTool,
)
from azure.identity import DefaultAzureCredential

import sys  # noqa: E402 - path setup for the sibling skills helper

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from skills_util import apply_skills  # noqa: E402

AGENT_NAME = "knowledge-assistant"
PROMPT_FILE = Path(__file__).parent / "prompts" / "knowledge.txt"


def build_tools() -> list:
    return [
        AzureAISearchTool(azure_ai_search=AzureAISearchToolResource()),
        SharepointPreviewTool(
            sharepoint_grounding_preview=SharepointGroundingToolParameters(
                project_connections=[],
            ),
        ),
        WorkIQPreviewTool(
            project_connection_id=os.environ.get("WORK_IQ_CONNECTION_ID", ""),
        ),
        MemorySearchPreviewTool(
            memory_store_name=os.environ.get("MEMORY_STORE_NAME", "default"),
        ),
    ]


def main() -> None:
    endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
    credential = DefaultAzureCredential()
    client = AIProjectClient(endpoint=endpoint, credential=credential)

    instructions = apply_skills(
        Path(__file__).parent,
        PROMPT_FILE.read_text(encoding="utf-8").strip(),
        endpoint=endpoint,
        credential=credential,
    )

    agent = client.agents.create_version(
        agent_name=AGENT_NAME,
        definition=PromptAgentDefinition(
            model=os.environ["AZURE_DEPLOYMENT_NAME"],
            instructions=instructions,
            tools=build_tools(),
            temperature=0.3,
            top_p=0.95,
        ),
        description="Enterprise knowledge assistant grounded in internal data.",
    )

    print(f"Created agent: {agent.name} (version={agent.version})")


if __name__ == "__main__":
    main()
