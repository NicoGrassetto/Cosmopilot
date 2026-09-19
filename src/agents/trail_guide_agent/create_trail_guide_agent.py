from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from time import perf_counter

from azure.ai.projects import AIProjectClient, models
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)

AGENT_DIR = Path(__file__).resolve().parent
AGENT_NAME = "trail-guide-agent"
PROMPT_VERSION = "v1"


def create_trail_guide_agent() -> models.AgentVersionDetails:
    prompt_file = AGENT_DIR / "prompts" / f"{PROMPT_VERSION}_instructions.md"
    instructions = prompt_file.read_text(encoding="utf-8").strip()
    if not instructions:
        raise ValueError(f"Expected nonempty instructions in {prompt_file}")

    endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
    model = os.environ["AZURE_DEPLOYMENT_NAME"]

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=endpoint,  # Select the configured Foundry project.
            credential=credential,  # Authenticate using the default Azure credential chain.
            allow_preview=False,  # Use only stable prompt-agent features.
            api_version="v1",  # Preserve the SDK's documented API version.
            polling_interval=30,  # Preserve the default polling interval in seconds.
        ) as client,
    ):
        definition = models.PromptAgentDefinition(
            model=model,  # Use the existing configured model deployment.
            rai_config=None,  # Retain the project's default content safety configuration.
            harness=None,  # Retain the default managed prompt-agent runtime.
            instructions=instructions,  # Load the versioned trail-guide Markdown prompt.
            skills=None,  # Do not attach runtime skills to this agent.
            temperature=None,  # Preserve the existing default sampling temperature.
            top_p=None,  # Preserve the existing default nucleus-sampling behavior.
            reasoning=None,  # Retain the model's default reasoning settings.
            tools=[],  # Preserve the existing prompt-only agent without tools.
            tool_choice=None,  # Retain the service's default tool-selection behavior.
            text=None,  # Retain the default text response format.
            structured_inputs=None,  # Do not require structured prompt inputs.
        )
        started = perf_counter()
        logger.info(
            "Creating trail guide agent name=%s model=%s tool_count=%d",
            AGENT_NAME,
            model,
            len(definition.tools or []),
        )
        agent = client.agents.create_version(
            agent_name=AGENT_NAME,  # Preserve the registered trail-guide agent name.
            definition=definition,  # Submit the prompt-only agent definition directly to Foundry.
            content_type="application/json",  # Submit the agent definition as JSON.
            metadata={  # Preserve the use-case and prompt-version metadata.
                "usecase": AGENT_NAME,
                "prompt_version": PROMPT_VERSION,
            },
            description=(  # Preserve the existing human-readable agent description.
                "Adventure Works trail recommendations, safety tips, "
                "and gear advice."
            ),
            blueprint_reference=None,  # Do not associate the agent with a blueprint.
            draft=None,  # Retain the service default of creating a released version.
        )
        logger.info(
            "Created trail guide agent name=%s version=%s duration_ms=%.0f",
            agent.name,
            agent.version,
            (perf_counter() - started) * 1000,
        )
        return agent


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    )
    try:
        agent = create_trail_guide_agent()
    except Exception:
        logger.exception("Trail guide agent creation failed name=%s", AGENT_NAME)
        raise SystemExit(1)
    print(json.dumps({"name": agent.name, "version": agent.version}, indent=2))


if __name__ == "__main__":
    main()
