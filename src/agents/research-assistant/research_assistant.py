"""Create the research-assistant prompt agent in Azure AI Foundry.

Tools: web_search, bing_grounding, file_search.
(bing_custom_search_preview is currently disabled - see build_tools for why.)

Env vars:
    AZURE_AI_PROJECT_ENDPOINT   Foundry project endpoint
    AZURE_DEPLOYMENT_NAME       Chat model deployment (e.g. gpt-4-1-nano)
    BING_CONNECTION_ID          Foundry connection id for Bing grounding
    FILE_SEARCH_VECTOR_STORE_ID Vector store id for file search

Auth: DefaultAzureCredential (run `az login` first).
Note: grounding tools require the matching connections to exist in the project.
"""

import os
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    # BingCustomSearchConfiguration,      # noqa: ERA001 - custom search disabled (see below)
    # BingCustomSearchPreviewTool,        # noqa: ERA001
    # BingCustomSearchToolParameters,     # noqa: ERA001
    BingGroundingSearchConfiguration,
    BingGroundingSearchToolParameters,
    BingGroundingTool,
    FileSearchTool,
    PromptAgentDefinition,
    WebSearchTool,
)
from azure.identity import DefaultAzureCredential

import sys  # noqa: E402 - path setup for the sibling skills helper

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from skills_util import apply_skills  # noqa: E402

AGENT_NAME = "research-assistant"
PROMPT_FILE = Path(__file__).parent / "prompts" / "researcher.txt"


def build_tools() -> list:
    bing_connection_id = os.environ["BING_CONNECTION_ID"]
    vector_store_id = os.environ["FILE_SEARCH_VECTOR_STORE_ID"]

    # NOTE: bing_custom_search_preview is disabled. The Foundry Responses runtime
    # rejects it with a hard HTTP 400 (unsupported tool type), which blocks *every*
    # query to the agent while it is attached. Re-enable once the preview tool is
    # supported by the runtime and a Bing Custom Search configuration exists.
    # custom_connection_id = os.environ.get("BING_CUSTOM_CONNECTION_ID", "")
    # custom_instance_name = os.environ.get("BING_CUSTOM_INSTANCE_NAME", "")
    # custom_search_configs = []
    # if custom_connection_id and custom_instance_name:
    #     custom_search_configs.append(
    #         BingCustomSearchConfiguration(
    #             project_connection_id=custom_connection_id,
    #             instance_name=custom_instance_name,
    #         ),
    #     )

    return [
        WebSearchTool(),
        BingGroundingTool(
            bing_grounding=BingGroundingSearchToolParameters(
                search_configurations=[
                    BingGroundingSearchConfiguration(
                        project_connection_id=bing_connection_id,
                    ),
                ],
            ),
        ),
        # BingCustomSearchPreviewTool(
        #     bing_custom_search_preview=BingCustomSearchToolParameters(
        #         search_configurations=custom_search_configs,
        #     ),
        # ),
        FileSearchTool(
            vector_store_ids=[vector_store_id],
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
            temperature=0.4,
            top_p=0.95,
        ),
        description="Web and document research assistant with grounded citations.",
    )

    print(f"Created agent: {agent.name} (version={agent.version})")


if __name__ == "__main__":
    main()
