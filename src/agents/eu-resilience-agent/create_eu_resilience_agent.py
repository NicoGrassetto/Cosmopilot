from __future__ import annotations

import logging
import os
from pathlib import Path

from agents.agents import create_prompt_agent

AGENT_DIR = Path(__file__).resolve().parent
AGENT_NAME = "eu-resilience-agent"
PROMPT_VERSION = "v3"


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    )

    instructions = (
        AGENT_DIR / "prompts" / f"{PROMPT_VERSION}_instructions.md"
    ).read_text(encoding="utf-8").strip()

    create_prompt_agent(
        agent_name=AGENT_NAME,
        model=os.environ["AZURE_DEPLOYMENT_NAME"],
        instructions=instructions,
        description="Provides evidence-grounded EU resilience analysis.",
        tools=[],
        temperature=0.1,
        metadata={
            "usecase": AGENT_NAME,
            "prompt_version": PROMPT_VERSION,
        },
    )


if __name__ == "__main__":
    main()