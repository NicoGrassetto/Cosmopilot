from __future__ import annotations

import argparse
import json
import logging
import os
from time import perf_counter
from typing import Any

from azure.ai.projects import AIProjectClient
import azure.ai.projects.models as models
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)


def create_prompt_agent(
    agent_name: str,
    *,
    model: str,
    rai_config: models.RaiConfig | None = None,
    instructions: str | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    reasoning: models.Reasoning | None = None,
    tools: list[models.Tool] | None = None,
    tool_choice: str | models.ToolChoiceParam | None = None,
    text: models.PromptAgentDefinitionTextOptions | None = None,
    structured_inputs: dict[str, models.StructuredInputDefinition] | None = None,
    content_type: str = "application/json",
    metadata: dict[str, str] | None = None,
    description: str | None = None,
    blueprint_reference: models.AgentBlueprintReference | None = None,
    draft: bool | None = None,
    allow_preview: bool = False,
    **kwargs: Any,
) -> models.AgentVersionDetails:
    started = perf_counter()
    logger.info(
        "Creating prompt agent name=%s model=%s draft=%s tool_count=%d",
        agent_name,
        model,
        bool(draft),
        len(tools or []),
    )

    definition = models.PromptAgentDefinition(
        model=model,
        rai_config=rai_config,
        instructions=instructions,
        temperature=temperature,
        top_p=top_p,
        reasoning=reasoning,
        tools=tools,
        tool_choice=tool_choice,
        text=text,
        structured_inputs=structured_inputs,
    )

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        result = client.agents.create_version(
            agent_name=agent_name,
            definition=definition,
            content_type=content_type,
            metadata=metadata,
            description=description,
            blueprint_reference=blueprint_reference,
            draft=draft,
            **kwargs,
        )
        logger.info(
            "Created prompt agent name=%s version=%s duration_ms=%.0f",
            result.name,
            result.version,
            (perf_counter() - started) * 1000,
        )
        return result

def get_agent(
    agent_name: str,
    *,
    allow_preview: bool = False,
    **kwargs: Any,
) -> models.AgentDetails:
    started = perf_counter()
    logger.info("Getting agent name=%s", agent_name)

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        result = client.agents.get(agent_name=agent_name, **kwargs)
        logger.info(
            "Retrieved agent name=%s state=%s duration_ms=%.0f",
            result.name,
            result.state,
            (perf_counter() - started) * 1000,
        )
        return result
    
def list_agents(
    *,
    kind: str | models.AgentKind | None = None,
    limit: int | None = None,
    order: str | models.PageOrder | None = None,
    before: str | None = None,
    allow_preview: bool = False,
    **kwargs: Any,
) -> list[models.AgentDetails]:
    started = perf_counter()
    logger.info(
        "Listing agents kind=%s limit=%s order=%s cursor_present=%s",
        kind,
        limit,
        order,
        before is not None,
    )

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        result = list(
            client.agents.list(
                kind=kind,
                limit=limit,
                order=order,
                before=before,
                **kwargs,
            )
        )
        logger.info(
            "Listed agents count=%d duration_ms=%.0f",
            len(result),
            (perf_counter() - started) * 1000,
        )
        return result

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    )

    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)

    get_command = commands.add_parser("get-agent")
    get_command.add_argument("-n", "--agent-name", required=True)

    list_command = commands.add_parser("list-agents")
    list_command.add_argument("-k", "--kind", choices=("prompt", "hosted", "workflow", "external"),)

    args = parser.parse_args()

    try:
        if args.command == "get-agent":
            result = get_agent(
                agent_name=args.agent_name,
            )
            output = result.as_dict()
        else:
            result = list_agents(
                kind=args.kind,
            )
            output = [agent.as_dict() for agent in result]
    except Exception:
        logger.exception("Agent command failed command=%s", args.command)
        raise SystemExit(1)

    print(json.dumps(output, indent=2, default=str))

if __name__ == "__main__":
    main()


# Versions	get_version	Read one exact version.
# Versions	list_versions	List versions of one agent.
# Endpoint	update_details	Change endpoint routing, protocols, or the agent card.
# Endpoint	enable	Allow new requests and sessions.
# Endpoint	disable	Stop accepting new requests and sessions.
# Delete	delete	Delete an agent and its versions.
# Delete	delete_version	Delete one version.