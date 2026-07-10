"""Create the orchestrator-assistant prompt agent in Azure AI Foundry.

Tools: a2a_preview, tool_search, namespace, toolbox_search_preview.

Env vars:
    AZURE_AI_PROJECT_ENDPOINT   Foundry project endpoint
    AZURE_DEPLOYMENT_NAME       Chat model deployment (e.g. gpt-4-1-nano)
    A2A_BASE_URL                Base URL of the peer agent (A2A)
    A2A_AGENT_CARD_PATH         Agent card path (default: /.well-known/agent.json)

Auth: DefaultAzureCredential (run `az login` first).
Note: a2a_preview requires a reachable peer agent.
"""

import os
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    A2APreviewTool,
    NamespaceToolParam,
    PromptAgentDefinition,
    ToolboxSearchPreviewToolboxTool,
    ToolSearchToolParam,
)
from azure.identity import DefaultAzureCredential

import sys  # noqa: E402 - path setup for the sibling skills helper

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from skills_util import apply_skills  # noqa: E402

AGENT_NAME = "orchestrator-assistant"
PROMPT_FILE = Path(__file__).parent / "prompts" / "orchestrator.txt"


def build_tools() -> list:
    return [
        A2APreviewTool(
            base_url=os.environ.get("A2A_BASE_URL", ""),
            agent_card_path=os.environ.get(
                "A2A_AGENT_CARD_PATH", "/.well-known/agent.json"
            ),
        ),
        ToolSearchToolParam(),
        NamespaceToolParam(name="specialists", tools=[]),
        ToolboxSearchPreviewToolboxTool(name="toolbox-search"),
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
        description="Orchestrator that routes work to specialist agents and tools.",
    )

    print(f"Created agent: {agent.name} (version={agent.version})")


if __name__ == "__main__":
    main()
