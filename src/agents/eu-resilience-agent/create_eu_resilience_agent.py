from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any

from azure.ai.projects.models import FunctionTool, Tool

from agents.agents import create_prompt_agent

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    )

    instructions = (Path(__file__).parent / "prompts" / "v2_instructions.md").read_text(encoding="utf-8").strip()
    
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

    create_prompt_agent(
        agent_name="eu-resilience-agent",
        model=os.environ["AZURE_DEPLOYMENT_NAME"],
        instructions=instructions,
        description="Turns governed EU resilience evidence into approved cross-agency coordination actions.",
        tools=tools,
        tool_choice="auto",
        metadata={
            "usecase": "eu-resilience-agent",
            "prompt_version": "v2",
        }
    )
    

if __name__ == "__main__":
    main()