from agents.agent import create 
from pathlib import Path
from azure.ai.projects.models import WebSearchTool
import logging

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    )

    prompt_file = Path(__file__).parent / "prompts" / "v1_instructions.md"
    instructions = prompt_file.read_text(encoding="utf-8").strip()

    create(
        name="weather-agent",
        instructions=instructions,
        description="Provides current weather conditions and forecasts for a requested location.",
        tools=[
            WebSearchTool(),
        ],
        temperature=0.1,
    )

if __name__ == "__main__":
    main()