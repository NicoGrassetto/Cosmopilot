import logging
import os
from pathlib import Path

from azure.ai.projects.models import MemorySearchPreviewTool, WebSearchTool

from agents.agents import create_prompt_agent
from memory_storage import ensure_agent_memory_store

AGENT_NAME = "weather-agent"


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    )

    prompt_file = Path(__file__).parent / "prompts" / "v1_instructions.md"
    instructions = prompt_file.read_text(encoding="utf-8").strip()

    # ------- Memory store--------
    memory_store = ensure_agent_memory_store(AGENT_NAME)
    memory_tool = MemorySearchPreviewTool(
        memory_store_name=memory_store.name,
        scope="{{$userId}}",
        update_delay=300,
    )
    # --------

    create_prompt_agent(
        agent_name=AGENT_NAME,
        model=os.environ["AZURE_DEPLOYMENT_NAME"],
        instructions=instructions,
        description="Provides current weather conditions and forecasts for a requested location.",
        tools=[
            WebSearchTool(),
            memory_tool,
        ],
        temperature=0.1,
        top_p=0.95,
        allow_preview=True,
    )


if __name__ == "__main__":
    main()