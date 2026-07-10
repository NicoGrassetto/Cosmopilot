"""Create the browser-assistant prompt agent in Azure AI Foundry.

Tools: computer_use_preview, browser_automation_preview, image_generation.

Env vars:
    AZURE_AI_PROJECT_ENDPOINT   Foundry project endpoint
    AZURE_DEPLOYMENT_NAME       Chat model deployment (e.g. gpt-4-1-nano)

Auth: DefaultAzureCredential (run `az login` first).
Note: computer/browser tools require a configured automation environment.
"""

import os
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    BrowserAutomationPreviewTool,
    BrowserAutomationToolParameters,
    ComputerUsePreviewTool,
    ImageGenTool,
    PromptAgentDefinition,
)
from azure.identity import DefaultAzureCredential

import sys  # noqa: E402 - path setup for the sibling skills helper

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from skills_util import apply_skills  # noqa: E402

AGENT_NAME = "browser-assistant"
PROMPT_FILE = Path(__file__).parent / "prompts" / "operator.txt"


def build_tools() -> list:
    return [
        ComputerUsePreviewTool(
            display_width=1280,
            display_height=720,
            environment="browser",
        ),
        BrowserAutomationPreviewTool(
            browser_automation_preview=BrowserAutomationToolParameters(),
        ),
        ImageGenTool(),
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
        description="Browser/computer operator assistant with image generation.",
    )

    print(f"Created agent: {agent.name} (version={agent.version})")


if __name__ == "__main__":
    main()
