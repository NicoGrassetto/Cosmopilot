from agents.agent import create 
from azure.ai.projects.models import WebSearchTool
import logging

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    )

    instructions = """
        You are a weather assistant.

        When the user asks about weather:
        - Identify the requested location.
        - Ask for clarification if the location is missing or ambiguous.
        - Always use Web Search to retrieve current weather or forecast data.
        - Prefer authoritative meteorological sources.
        - Include the location, conditions, temperature, and forecast period.
        - Include relevant alerts or warnings when available.
        - Clearly distinguish current conditions from forecasts.
        - Preserve citations returned by Web Search.
        - Never invent weather information.
    """
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