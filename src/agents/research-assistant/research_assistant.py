"""Create the research-assistant prompt agent in Azure AI Foundry.

Tools: web_search, bing_grounding, bing_custom_search_preview, file_search.

Env vars:
    AZURE_AI_PROJECT_ENDPOINT   Foundry project endpoint
    AZURE_DEPLOYMENT_NAME       Chat model deployment (e.g. gpt-4-1-nano)
    BING_CONNECTION_ID          Foundry connection id for Bing grounding
    BING_CUSTOM_CONNECTION_ID   Foundry connection id for Bing custom search
    FILE_SEARCH_VECTOR_STORE_ID Vector store id for file search

Auth: DefaultAzureCredential (run `az login` first).
Note: grounding tools require the matching connections to exist in the project.
"""

import os
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    BingCustomSearchPreviewTool,
    BingCustomSearchToolParameters,
    BingGroundingSearchToolParameters,
    BingGroundingTool,
    FileSearchTool,
    PromptAgentDefinition,
    WebSearchTool,
)
from azure.identity import DefaultAzureCredential

AGENT_NAME = "research-assistant"
PROMPT_FILE = Path(__file__).parent / "prompts" / "researcher.txt"


def build_tools() -> list:
    return [
        WebSearchTool(),
        BingGroundingTool(
            bing_grounding=BingGroundingSearchToolParameters(search_configurations=[]),
        ),
        BingCustomSearchPreviewTool(
            bing_custom_search_preview=BingCustomSearchToolParameters(
                search_configurations=[],
            ),
        ),
        FileSearchTool(
            vector_store_ids=[os.environ.get("FILE_SEARCH_VECTOR_STORE_ID", "")],
        ),
    ]


def main() -> None:
    client = AIProjectClient(
        endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
        credential=DefaultAzureCredential(),
    )

    agent = client.agents.create_version(
        agent_name=AGENT_NAME,
        definition=PromptAgentDefinition(
            model=os.environ["AZURE_DEPLOYMENT_NAME"],
            instructions=PROMPT_FILE.read_text(encoding="utf-8").strip(),
            tools=build_tools(),
            temperature=0.4,
            top_p=0.95,
        ),
        description="Web and document research assistant with grounded citations.",
    )

    print(f"Created agent: {agent.name} (version={agent.version})")


if __name__ == "__main__":
    main()
