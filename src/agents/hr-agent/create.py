"""Create the HR prompt agent in Azure AI Foundry.

Prompt-based agent whose system prompt is loaded from a .txt file in ./prompts.
Tools: file_search (ground answers in HR policy docs) + code_interpreter
(compute leave balances, proration, dates).

Env vars:
    AZURE_AI_PROJECT_ENDPOINT   Foundry project endpoint
    AZURE_DEPLOYMENT_NAME       Chat model deployment (e.g. gpt-4-1-nano)
    HR_VECTOR_STORE_ID          Vector store id with HR policy documents

Auth: DefaultAzureCredential (run `az login` first).
Note: file_search requires the vector store to exist in the project.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from azure.ai.projects.models import (
    CodeInterpreterTool,
    FileSearchTool,
)

# Make the shared ``agent`` module (src/agent.py) importable when this script is
# run directly (src/ is two levels above this agent's folder).
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from agent import create  # noqa: E402  (import needs the sys.path setup above)

# --- Foundry Skills (preview) helpers -----------------------------------------
# Inlined from the former shared ``skills_util`` module so each agent script is
# self-contained. Each agent keeps a local ``skills/`` directory; every skill is
# a ``SKILL.md`` file (Agent Skills spec: https://agentskills.io) with YAML front
# matter (``name``, ``description``) plus a Markdown instruction body.
# Skills API: https://learn.microsoft.com/azure/foundry/agents/how-to/tools/skills
import re
from dataclasses import dataclass


def apply_skills(agent_dir: Path, base_instructions: str) -> str:
    """Discover local ``skills/<name>/SKILL.md`` files and inject them into the
    agent's system prompt (direct-injection mode). Central registration with the
    Foundry Skills API now lives in ``src/skills.py``.
    """

    name_pattern = re.compile(r"^[a-z0-9]([a-z0-9\-]*[a-z0-9])?$")

    @dataclass
    class LocalSkill:
        """A skill authored locally as ``skills/<name>/SKILL.md``."""

        name: str
        body: str

    skills_root = Path(agent_dir) / "skills"
    skills: list[LocalSkill] = []
    if skills_root.is_dir():
        for skill_md in sorted(skills_root.glob("*/SKILL.md")):
            text = skill_md.read_text(encoding="utf-8")

            # Parse a minimal ``key: value`` YAML front matter block (avoids a
            # hard PyYAML dependency; SKILL.md front matter uses simple unquoted
            # scalar fields).
            meta: dict[str, str] = {}
            parts = text.split("---", 2)
            if text.startswith("---") and len(parts) >= 3:
                _, front, body = parts
                body = body.strip()
                for line in front.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#") or ":" not in line:
                        continue
                    key, _, value = line.partition(":")
                    meta[key.strip().lower()] = value.strip().strip('"').strip("'")
            else:
                body = text.strip()

            name = meta.get("name", skill_md.parent.name)
            if not name_pattern.match(name):
                print(f"  ! Skipping skill '{name}' ({skill_md}): invalid name pattern")
                continue
            skills.append(LocalSkill(name=name, body=body))

    if not skills:
        return base_instructions
    print(f"  Found {len(skills)} local skill(s): {', '.join(s.name for s in skills)}")

    blocks = [base_instructions.strip(), "", "# Attached skills (Foundry preview)", ""]
    blocks.append(
        "The following skills provide reusable behavioral guidelines. Apply them "
        "consistently in every response.",
    )
    for skill in skills:
        blocks.extend(["", f"<skill name=\"{skill.name}\">", skill.body.strip(), "</skill>"])
    return "\n".join(blocks).strip()
# --- end Foundry Skills helpers -----------------------------------------------


def main() -> None:
    
    # Which prompt to register the agent with. Swap for any file in ./prompts.
    PROMPTS_DIR = Path(__file__).parent / "prompts"
    PROMPT_FILE = PROMPTS_DIR / "hr_assistant.txt"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    )

    instructions = apply_skills(
        Path(__file__).parent,
        PROMPT_FILE.read_text(encoding="utf-8").strip(),
    )

    create(
        name="hr-assistant",
        instructions=instructions,
        description="Conversational HR assistant for employee policy and benefits questions.",
        tools=[
            FileSearchTool(
                vector_store_ids=[os.environ.get("HR_VECTOR_STORE_ID", "")],
            ),
            CodeInterpreterTool(),
        ],
    )


if __name__ == "__main__":
    main()
