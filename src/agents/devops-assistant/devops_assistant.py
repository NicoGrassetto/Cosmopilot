"""Create the devops-assistant prompt agent in Azure AI Foundry.

Tools: local_shell, shell, apply_patch, azure_function.

Env vars:
    AZURE_AI_PROJECT_ENDPOINT   Foundry project endpoint
    AZURE_DEPLOYMENT_NAME       Chat model deployment (e.g. gpt-4-1-nano)

Auth: DefaultAzureCredential (run `az login` first).
Note: azure_function requires a configured Azure Function binding.
"""

import os
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    ApplyPatchToolParam,
    AzureFunctionTool,
    FunctionShellToolParam,
    FunctionShellToolParamEnvironmentLocalEnvironmentParam,
    LocalShellToolParam,
    PromptAgentDefinition,
)
from azure.identity import DefaultAzureCredential

AGENT_NAME = "devops-assistant"
PROMPT_FILE = Path(__file__).parent / "prompts" / "devops.txt"


def build_tools() -> list:
    return [
        LocalShellToolParam(),
        FunctionShellToolParam(
            name="shell",
            environment=FunctionShellToolParamEnvironmentLocalEnvironmentParam(),
        ),
        ApplyPatchToolParam(),
        AzureFunctionTool(azure_function={}),
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
        description="DevOps automation assistant for shell, patching, and functions.",
    )

    print(f"Created agent: {agent.name} (version={agent.version})")


if __name__ == "__main__":
    main()
