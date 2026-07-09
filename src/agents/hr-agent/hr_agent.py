"""Create the HR prompt agent in Azure AI Foundry.

Prompt-based agent whose system prompt is loaded from a .txt file in ./prompts.
Tools: file_search (ground answers in HR policy docs) + code_interpreter
(compute leave balances, proration, dates).

Env vars:
    AZURE_AI_PROJECT_ENDPOINT   Foundry project endpoint
    AZURE_DEPLOYMENT_NAME       Chat model deployment (e.g. gpt-4-1-nano)
    HR_VECTOR_STORE_ID          Vector store id with HR policy documents

Auth: DefaultAzureCredential (run `az login` first).
Note: file_search requires the vector store to exist in the project.
"""

import os
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    CodeInterpreterTool,
    FileSearchTool,
    PromptAgentDefinition,
)
from azure.identity import DefaultAzureCredential

AGENT_NAME = "hr-assistant"

# Which prompt to register the agent with. Swap for any file in ./prompts.
PROMPTS_DIR = Path(__file__).parent / "prompts"
PROMPT_FILE = PROMPTS_DIR / "hr_assistant.txt"


def load_instructions(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def build_tools() -> list:
    return [
        FileSearchTool(
            vector_store_ids=[os.environ.get("HR_VECTOR_STORE_ID", "")],
        ),
        CodeInterpreterTool(),
    ]


def main() -> None:
    instructions = load_instructions(PROMPT_FILE)

    client = AIProjectClient(
        endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
        credential=DefaultAzureCredential(),
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
        description="Conversational HR assistant for employee policy and benefits questions.",
    )

    print(f"Created agent: {agent.name} (version={agent.version})")


if __name__ == "__main__":
    main()
