"""Create the integration-assistant prompt agent in Azure AI Foundry.

Tools: openapi, mcp, function, custom.

Env vars:
    AZURE_AI_PROJECT_ENDPOINT   Foundry project endpoint
    AZURE_DEPLOYMENT_NAME       Chat model deployment (e.g. gpt-4-1-nano)
    MCP_SERVER_URL              URL of the MCP server to connect
    MCP_SERVER_LABEL            Label for the MCP server (default: cosmos-mcp)

Auth: DefaultAzureCredential (run `az login` first).
Note: openapi requires a valid OpenAPI spec; mcp requires a reachable server.
"""

import os
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    CustomToolParam,
    FunctionTool,
    MCPTool,
    OpenApiTool,
    PromptAgentDefinition,
)
from azure.identity import DefaultAzureCredential

import sys  # noqa: E402 - path setup for the sibling skills helper

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from skills_util import apply_skills  # noqa: E402

AGENT_NAME = "integration-assistant"
PROMPT_FILE = Path(__file__).parent / "prompts" / "integration.txt"


def build_tools() -> list:
    return [
        OpenApiTool(openapi={}),
        MCPTool(
            server_label=os.environ.get("MCP_SERVER_LABEL", "cosmos-mcp"),
            server_url=os.environ.get("MCP_SERVER_URL", ""),
        ),
        FunctionTool(
            name="lookup_record",
            description="Look up a record by id in an external system.",
            parameters={
                "type": "object",
                "properties": {"id": {"type": "string"}},
                "required": ["id"],
            },
        ),
        CustomToolParam(
            name="custom_connector",
            description="Placeholder custom tool for a bespoke integration.",
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
        description="Integration assistant for REST APIs, MCP, and custom connectors.",
    )

    print(f"Created agent: {agent.name} (version={agent.version})")


if __name__ == "__main__":
    main()
