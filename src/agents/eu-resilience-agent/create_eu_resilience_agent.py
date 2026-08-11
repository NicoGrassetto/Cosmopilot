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


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    )

    project_endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"].rstrip("/")
    toolbox_endpoint = (
        f"{project_endpoint}/toolboxes/{TOOLBOX_NAME}/mcp?api-version=v1"
    )
    toolbox_connection_id = os.environ.get(TOOLBOX_CONNECTION_ENV)
    if not toolbox_connection_id:
        raise RuntimeError(
            f"{TOOLBOX_CONNECTION_ENV} must name a remote-tool project connection "
            f"targeting {toolbox_endpoint} with user Entra token audience "
            "https://ai.azure.com"
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

    if not skill_references:
        raise RuntimeError(f"No skills found under {AGENT_DIR / 'skills'}")

    instructions = "\n\n".join(
        [
            base_instructions,
            "# Attached skills\n\n" + "\n\n".join(skill_blocks),
        ]
    )

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
    tools.append(
        MCPTool(
            server_label="eu_resilience_skills",
            server_url=toolbox_endpoint,
            project_connection_id=toolbox_connection_id,
            require_approval="never",
        )
    )

    create_prompt_agent(
        agent_name=AGENT_NAME,
        model=os.environ["AZURE_DEPLOYMENT_NAME"],
        instructions=instructions,
        description=(
            "Turns governed EU resilience evidence into approved cross-agency "
            "coordination actions."
        ),
        tools=tools,
        tool_choice="auto",
        temperature=0.1,
        metadata={
            "usecase": AGENT_NAME,
            "prompt_version": "v2",
            "toolbox": TOOLBOX_NAME,
            "toolbox_version": toolbox_version.version,
        },
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