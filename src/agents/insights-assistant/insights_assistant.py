"""Create the insights-assistant prompt agent in Azure AI Foundry.

Tools: fabric_iq_preview, code_interpreter, capture_structured_outputs,
plus a Microsoft Fabric data agent.

Env vars:
    AZURE_AI_PROJECT_ENDPOINT   Foundry project endpoint
    AZURE_DEPLOYMENT_NAME       Chat model deployment (e.g. gpt-4-1-nano)
    FABRIC_CONNECTION_ID        Foundry connection id for Microsoft Fabric
    FABRIC_IQ_SERVER_URL        Fabric IQ server URL
    FABRIC_IQ_CONNECTION_ID     Foundry connection id for Fabric IQ

Auth: DefaultAzureCredential (run `az login` first).
Note: Fabric tools require the matching connections in the project.
"""

import os
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    CaptureStructuredOutputsTool,
    CodeInterpreterTool,
    FabricIQPreviewTool,
    MicrosoftFabricPreviewTool,
    PromptAgentDefinition,
)
from azure.identity import DefaultAzureCredential

AGENT_NAME = "insights-assistant"
PROMPT_FILE = Path(__file__).parent / "prompts" / "analyst.txt"


def build_tools() -> list:
    return [
        MicrosoftFabricPreviewTool(),
        FabricIQPreviewTool(
            server_url=os.environ.get("FABRIC_IQ_SERVER_URL", ""),
            server_label="fabric-iq",
            project_connection_id=os.environ.get("FABRIC_IQ_CONNECTION_ID", ""),
        ),
        CodeInterpreterTool(),
        CaptureStructuredOutputsTool(name="capture_insights", outputs={}),
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
            temperature=0.2,
            top_p=0.95,
        ),
        description="Data insights assistant over Microsoft Fabric with computation.",
    )

    print(f"Created agent: {agent.name} (version={agent.version})")


if __name__ == "__main__":
    main()
