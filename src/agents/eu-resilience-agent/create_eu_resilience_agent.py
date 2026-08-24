from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parent
SRC_DIR = AGENT_DIR.parents[1]
sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(AGENT_DIR))

from azure.ai.projects import AIProjectClient  # noqa: E402
from azure.ai.projects.models import (  # noqa: E402
    FunctionTool,
    MCPTool,
    Tool,
    ToolboxSkillReference,
)
from azure.identity import DefaultAzureCredential  # noqa: E402

from agents.agents import create_prompt_agent  # noqa: E402
from functions import call_local_function  # noqa: E402
from skills import create_from_files  # noqa: E402
from toolboxes import create_toolbox, update_toolbox  # noqa: E402


AGENT_NAME = "eu-resilience-agent"
TOOLBOX_NAME = "eu-resilience-skills"
TOOLBOX_CONNECTION_ENV = "AZURE_TOOLBOX_CONNECTION_ID"
MAX_TOOL_ITERATIONS = 8
logger = logging.getLogger("eu_resilience_agent")


def _resolve_deployed_configuration(
    project_endpoint: str,
    toolbox_endpoint: str,
) -> tuple[str, str | None]:
    configured_model = os.environ.get("AZURE_DEPLOYMENT_NAME")
    configured_connection = os.environ.get(TOOLBOX_CONNECTION_ENV)

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=project_endpoint,
            credential=credential,
            allow_preview=True,
        ) as client,
    ):
        model = configured_model
        if not model:
            latest_agent = next(
                iter(
                    client.agents.list_versions(
                        agent_name=AGENT_NAME,
                        order="desc",
                    )
                ),
                None,
            )
            definition = getattr(latest_agent, "definition", None)
            model = getattr(definition, "model", None)

        if not model:
            deployment_names = [
                str(deployment.name)
                for deployment in client.deployments.list()
                if getattr(deployment, "name", None)
            ]
            model = (
                "gpt-4-1-nano"
                if "gpt-4-1-nano" in deployment_names
                else None
            )
        if not model:
            raise RuntimeError(
                "Unable to resolve an existing model deployment. Set "
                "AZURE_DEPLOYMENT_NAME explicitly."
            )

        connections = list(client.connections.list())
        connection_id = None
        if configured_connection:
            matched = next(
                (
                    connection
                    for connection in connections
                    if configured_connection
                    in {
                        str(getattr(connection, "id", "")),
                        str(getattr(connection, "name", "")),
                    }
                ),
                None,
            )
            connection_id = (
                str(matched.id) if matched is not None else configured_connection
            )
        else:
            matched = next(
                (
                    connection
                    for connection in connections
                    if str(getattr(connection, "target", "")).rstrip("/")
                    == toolbox_endpoint.rstrip("/")
                ),
                None,
            )
            if matched is not None:
                connection_id = str(matched.id)

    return str(model), connection_id


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    )

    project_endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"].rstrip("/")
    toolbox_endpoint = (
        f"{project_endpoint}/toolboxes/{TOOLBOX_NAME}/mcp?api-version=v1"
    )
    model, toolbox_connection_id = _resolve_deployed_configuration(
        project_endpoint,
        toolbox_endpoint,
    )

    base_instructions = (
        AGENT_DIR / "prompts" / "v2_instructions.md"
    ).read_text(encoding="utf-8").strip()
    skill_references = []
    skill_blocks = []
    for skill_md in sorted((AGENT_DIR / "skills").glob("*/SKILL.md")):
        skill_text = skill_md.read_text(encoding="utf-8")
        skill_parts = skill_text.split("---", 2)
        if not skill_text.startswith("---") or len(skill_parts) != 3:
            raise ValueError(f"Skill file has invalid front matter: {skill_md}")

        skill_name = skill_md.parent.name
        if toolbox_connection_id:
            skill_version = create_from_files(
                name=skill_name,
                skill_directory=skill_md.parent,
            )
            skill_references.append(
                ToolboxSkillReference(
                    name=skill_name,
                    version=skill_version.version,
                )
            )
        skill_blocks.extend(
            [
                f'<skill name="{skill_name}">',
                skill_parts[2].strip(),
                "</skill>",
            ]
        )

    if not skill_blocks:
        raise RuntimeError(f"No skills found under {AGENT_DIR / 'skills'}")

    instructions = "\n\n".join(
        [
            base_instructions,
            "# Attached skills\n\n" + "\n\n".join(skill_blocks),
        ]
    )

    toolbox_version = None
    if toolbox_connection_id:
        toolbox_version = create_toolbox(
            name=TOOLBOX_NAME,
            description="Governed skills for the EU resilience coordination agent.",
            tools=[],
            skills=skill_references,
            metadata={"usecase": AGENT_NAME},
            allow_preview=True,
        )
        update_toolbox(
            name=TOOLBOX_NAME,
            default_version=toolbox_version.version,
            allow_preview=True,
        )
    else:
        logger.info(
            "No project connection targets %s; using embedded skills without MCP.",
            toolbox_endpoint,
        )

    tools: list[Tool] = [
        FunctionTool(
            name="get_resilience_priorities",
            description=(
                "Return ranked country priorities from the curated EU27 "
                "resilience snapshot."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 27,
                        "description": "Maximum number of countries to return.",
                    },
                },
                "required": ["limit"],
                "additionalProperties": False,
            },
            strict=True,
        ),
        FunctionTool(
            name="get_country_resilience_evidence",
            description="Return the resilience evidence package for one EU country.",
            parameters={
                "type": "object",
                "properties": {
                    "country": {
                        "type": "string",
                        "description": "EU country name or ISO country code.",
                    },
                },
                "required": ["country"],
                "additionalProperties": False,
            },
            strict=True,
        ),
        FunctionTool(
            name="generate_resilience_report",
            description=(
                "Generate a styled downloadable DOCX report with charts from "
                "current country evidence or an EU leadership-priority ranking."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "report_type": {
                        "type": "string",
                        "enum": ["country", "eu_priorities"],
                    },
                    "country": {
                        "type": ["string", "null"],
                        "description": (
                            "Canonical EU country name for a country report; "
                            "null for an EU priorities report."
                        ),
                    },
                    "limit": {
                        "type": ["integer", "null"],
                        "minimum": 1,
                        "maximum": 10,
                        "description": (
                            "Priority count for an EU priorities report; null "
                            "for a country report."
                        ),
                    },
                },
                "required": ["report_type", "country", "limit"],
                "additionalProperties": False,
            },
            strict=True,
        ),
        FunctionTool(
            name="evaluate_coordination_playbook",
            description=(
                "Deterministically evaluate the illustrative coordination "
                "playbook against a country evidence package."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "country": {"type": "string"},
                    "evidence_package_id": {"type": "string"},
                },
                "required": ["country", "evidence_package_id"],
                "additionalProperties": False,
            },
            strict=True,
        ),
        FunctionTool(
            name="open_coordination_case",
            description=(
                "Open an internal coordination case from an approved decision "
                "card. The application must verify approval before execution."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "country": {"type": "string"},
                    "evidence_package_id": {"type": "string"},
                    "playbook_version": {"type": "string"},
                    "reason": {"type": "string"},
                    "lead_agency": {"type": "string"},
                    "participating_agencies": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "review_steps": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": [
                    "country",
                    "evidence_package_id",
                    "playbook_version",
                    "reason",
                    "lead_agency",
                    "participating_agencies",
                    "review_steps",
                ],
                "additionalProperties": False,
            },
            strict=True,
        ),
    ]
    if toolbox_connection_id:
        tools.append(
            MCPTool(
                server_label="eu_resilience_skills",
                server_url=toolbox_endpoint,
                project_connection_id=toolbox_connection_id,
                require_approval="never",
            )
        )

    metadata = {
        "usecase": AGENT_NAME,
        "prompt_version": "v2",
        "prompt_revision": "realtime-docx-reports-v3",
    }
    if toolbox_version is not None:
        metadata.update(
            {
                "toolbox": TOOLBOX_NAME,
                "toolbox_version": toolbox_version.version,
            }
        )

    create_prompt_agent(
        agent_name=AGENT_NAME,
        model=model,
        instructions=instructions,
        description=(
            "Turns governed EU resilience evidence into approved cross-agency "
            "coordination actions and downloadable evidence briefings."
        ),
        tools=tools,
        tool_choice="auto",
        temperature=0.1,
        metadata=metadata,
        allow_preview=True,
    )


def run_agent(prompt: str, *, approve_coordination_case: bool = False) -> str:
    """Invoke the latest agent version and execute requested functions locally."""
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt must be a non-empty string")

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=True,
        ) as client,
    ):
        agent = next(
            iter(client.agents.list_versions(agent_name=AGENT_NAME, order="desc")),
            None,
        )
        if agent is None:
            raise RuntimeError(f"No version of {AGENT_NAME!r} is available")

        openai = client.get_openai_client()
        try:
            agent_reference = {
                "agent_reference": {
                    "type": "agent_reference",
                    "name": agent.name,
                    "id": agent.id,
                }
            }
            response = openai.responses.create(
                input=prompt,
                extra_body=agent_reference,
            )
            coordination_case_attempted = False

            for _ in range(MAX_TOOL_ITERATIONS):
                tool_outputs = []
                for item in response.output:
                    if getattr(item, "type", None) != "function_call":
                        continue

                    function_name = getattr(item, "name", "")
                    allow_side_effects = (
                        function_name == "open_coordination_case"
                        and approve_coordination_case
                        and not coordination_case_attempted
                    )
                    if function_name == "open_coordination_case":
                        coordination_case_attempted = True

                    tool_outputs.append(
                        {
                            "type": "function_call_output",
                            "call_id": getattr(item, "call_id", ""),
                            "output": call_local_function(
                                function_name,
                                getattr(item, "arguments", None) or "{}",
                                allow_side_effects=allow_side_effects,
                            ),
                        }
                    )

                if not tool_outputs:
                    return response.output_text

                response = openai.responses.create(
                    input=tool_outputs,
                    previous_response_id=response.id,
                    extra_body=agent_reference,
                )
        finally:
            openai.close()

    raise RuntimeError(
        f"Agent exceeded the limit of {MAX_TOOL_ITERATIONS} local tool iterations"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--prompt",
        help="Invoke the latest agent version instead of creating a new version.",
    )
    parser.add_argument(
        "--approve-coordination-case",
        action="store_true",
        help="Allow one approved open_coordination_case call for this invocation.",
    )
    arguments = parser.parse_args()

    if arguments.prompt:
        print(
            run_agent(
                arguments.prompt,
                approve_coordination_case=arguments.approve_coordination_case,
            )
        )
    else:
        main()