from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from time import perf_counter

from azure.ai.projects import AIProjectClient, models
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)

AGENT_NAME = "weather-agent"
AGENT_DIR = Path(__file__).resolve().parent
SKILL_NAME = "severe-weather-safety"
ROUTINE_NAME = "weekday-weather-brussels"


def create_weather_agent() -> models.AgentVersionDetails:
    prompt_file = AGENT_DIR / "prompts" / "v1_instructions.md"
    instructions = prompt_file.read_text(encoding="utf-8").strip()
    if not instructions:
        raise ValueError(f"Expected nonempty instructions in {prompt_file}")

    skill_file = AGENT_DIR / "skills" / SKILL_NAME / "SKILL.md"
    skill_content = skill_file.read_text(encoding="utf-8")
    if not skill_content.strip():
        raise ValueError(f"Expected nonempty skill content in {skill_file}")

    endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
    model = os.environ["AZURE_DEPLOYMENT_NAME"]

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=endpoint,  # Select the configured Foundry project.
            credential=credential,  # Authenticate using the default Azure credential chain.
            allow_preview=True,  # Permit preview skill features on the agent definition.
            api_version="v1",  # Preserve the SDK's documented API version.
            polling_interval=30,  # Preserve the default polling interval in seconds.
        ) as client,
    ):
        started = perf_counter()
        logger.info("Creating weather skill name=%s", SKILL_NAME)
        skill = client.beta.skills.create_from_files(
            name=SKILL_NAME,  # Register a new version of the weather safety skill.
            content=models.CreateSkillVersionFromFilesBody(  # Use Foundry's native file-upload format.
                files=[  # Upload the original Markdown for Foundry to parse and validate.
                    ("SKILL.md", skill_content, "text/markdown"),
                ],
                default=False,  # Leave the skill's shared default version unchanged.
            ),
        )
        logger.info(
            "Created weather skill name=%s version=%s duration_ms=%.0f",
            skill.name,
            skill.version,
            (perf_counter() - started) * 1000,
        )

        definition = models.PromptAgentDefinition(
            model=model,  # Use the existing configured weather model deployment.
            rai_config=None,  # Retain the project's default content safety configuration.
            harness=None,  # Retain the default managed prompt-agent runtime.
            instructions=instructions,  # Load the weather instructions from the Markdown prompt.
            skills=[  # Make the newly registered safety skill available at runtime.
                models.SkillReference(
                    name=skill.name,  # Reference the skill name returned by Foundry.
                    version=skill.version,  # Pin the exact skill version registered above.
                ),
            ],
            temperature=0.1,  # Preserve the existing weather agent's sampling temperature.
            top_p=0.95,  # Preserve the legacy helper's nucleus-sampling setting.
            reasoning=None,  # Retain the model's default reasoning settings.
            tools=[  # Keep current weather retrieval grounded in web search.
                models.WebSearchTool(
                    external_web_access=True,  # Allow retrieval of fresh weather and alert data.
                    filters=None,  # Do not restrict the searchable domains.
                    user_location=None,  # Resolve location from the user's request.
                    search_context_size="medium",  # Preserve the default search context size.
                    name=None,  # Leave the deprecated tool name unset.
                    description=None,  # Leave the deprecated tool description unset.
                    tool_configs=None,  # Leave deprecated tool configuration unset.
                    custom_search_configuration=None,  # Do not require a custom search connection.
                ),
            ],
            tool_choice="required",  # Require Web Search, currently the only configured tool.
            text=None,  # Retain the default text response format.
            structured_inputs=None,  # Do not require structured prompt inputs.
        )
        started = perf_counter()
        logger.info(
            "Creating weather agent name=%s model=%s tool_count=%d skill_count=%d",
            AGENT_NAME,
            model,
            len(definition.tools or []),
            len(definition.skills or []),
        )
        agent = client.agents.create_version(
            agent_name=AGENT_NAME,  # Preserve the existing weather agent's identity.
            definition=definition,  # Submit the prompt, web search tool, and pinned safety skill.
            content_type="application/json",  # Submit the agent definition as JSON.
            metadata=None,  # Do not attach additional agent metadata.
            description=(  # Preserve the existing human-readable agent description.
                "Provides current weather conditions and forecasts for a requested location."
            ),
            blueprint_reference=None,  # Do not associate the agent with a blueprint.
            digital_worker_type=None,  # Do not enable a digital-worker integration.
            draft=None,  # Retain the service default of creating a released version.
        )
        logger.info(
            "Created weather agent name=%s version=%s duration_ms=%.0f",
            agent.name,
            agent.version,
            (perf_counter() - started) * 1000,
        )

        started = perf_counter()
        logger.info(
            "Creating or updating weather routine name=%s agent_name=%s enabled=%s",
            ROUTINE_NAME,
            agent.name,
            True,
        )
        routine = client.beta.routines.create_or_update(
            routine_name=ROUTINE_NAME,  # Preserve the existing named Brussels weather routine.
            content_type="application/json",  # Submit the routine definition as JSON.
            description="Provides a weekday morning weather report.",  # Preserve the existing description.
            enabled=True,  # Enable the daily 09:30 Brussels schedule.
            triggers={  # Preserve the existing single scheduled trigger.
                "daily-morning": models.ScheduleRoutineTrigger(
                    cron_expression="30 9 * * *",  # Preserve the existing daily 09:30 schedule.
                    time_zone="Europe/Brussels",  # Interpret the schedule in Brussels local time.
                ),
            },
            action=models.InvokeAgentResponsesApiRoutineAction(  # Invoke the weather agent through the Responses API.
                agent_name=agent.name,  # Target the agent successfully created above.
                agent_endpoint_id=None,  # Use the project-scoped name instead of a legacy endpoint.
                input="Report today's weather for Brussels, Belgium.",  # Preserve the scheduled weather request.
                conversation=None,  # Do not continue an existing conversation.
            ),
            authorization=None,  # Preserve the service's default dispatch authorization.
        )
        logger.info(
            "Created or updated weather routine name=%s enabled=%s duration_ms=%.0f",
            routine.name,
            routine.enabled,
            (perf_counter() - started) * 1000,
        )
        return agent


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    )
    try:
        agent = create_weather_agent()
    except Exception:
        logger.exception("Weather agent creation failed name=%s", AGENT_NAME)
        raise SystemExit(1)
    print(json.dumps({"name": agent.name, "version": agent.version}, indent=2))


if __name__ == "__main__":
    main()