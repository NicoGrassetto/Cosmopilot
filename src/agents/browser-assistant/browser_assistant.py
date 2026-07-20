"""Create the browser-assistant prompt agent in Azure AI Foundry.

Tools: browser_automation_preview, image_generation.
(computer_use_preview is disabled — see build_tools() for why.)

Env vars:
    AZURE_AI_PROJECT_ENDPOINT          Foundry project endpoint
    AZURE_DEPLOYMENT_NAME              Chat model deployment (any GPT model,
                                       e.g. gpt-4.1 / gpt-4-1-nano)
    BROWSER_AUTOMATION_CONNECTION_ID   Foundry project connection ID for the
                                       Playwright Workspace, of the form
                                       /subscriptions/.../connections/<name>

Auth: DefaultAzureCredential (run `az login` first).
Note: browser automation requires a Playwright Workspace connection in the
project; computer use additionally requires access to the gated
`computer-use-preview` model (https://aka.ms/oai/cuaaccess).
"""

from __future__ import annotations

import os
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    BrowserAutomationPreviewTool,
    BrowserAutomationToolConnectionParameters,
    BrowserAutomationToolParameters,
    # ComputerUsePreviewTool,  # disabled: gated `computer-use-preview` model
    ImageGenTool,
    PromptAgentDefinition,
)
from azure.identity import DefaultAzureCredential

# --- Foundry Skills (preview) helpers -----------------------------------------
# Inlined from the former shared ``skills_util`` module so each agent script is
# self-contained. Each agent keeps a local ``skills/`` directory; every skill is
# a ``SKILL.md`` file (Agent Skills spec: https://agentskills.io) with YAML front
# matter (``name``, ``description``) plus a Markdown instruction body.
# Skills API: https://learn.microsoft.com/azure/foundry/agents/how-to/tools/skills
import re
from dataclasses import dataclass

_NAME_PATTERN = re.compile(r"^[a-z0-9]([a-z0-9\-]*[a-z0-9])?$")


@dataclass
class LocalSkill:
    """A skill authored locally as ``skills/<name>/SKILL.md``."""

    name: str
    body: str


def _parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    """Parse a minimal ``key: value`` YAML front matter block.

    Returns ``(metadata, body)``. Avoids a hard PyYAML dependency because the
    SKILL.md front matter only uses simple unquoted scalar fields.
    """

    if not text.startswith("---"):
        return {}, text.strip()

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text.strip()

    _, front, body = parts
    meta: dict[str, str] = {}
    for line in front.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip().lower()] = value.strip().strip('"').strip("'")
    return meta, body.strip()


def discover_skills(agent_dir: Path) -> list[LocalSkill]:
    """Load every ``skills/*/SKILL.md`` under ``agent_dir``.

    ``agent_dir`` is the directory of the agent script (``Path(__file__).parent``).
    Returns an empty list when no ``skills/`` directory exists.
    """

    skills_root = Path(agent_dir) / "skills"
    if not skills_root.is_dir():
        return []

    skills: list[LocalSkill] = []
    for skill_md in sorted(skills_root.glob("*/SKILL.md")):
        text = skill_md.read_text(encoding="utf-8")
        meta, body = _parse_front_matter(text)
        name = meta.get("name", skill_md.parent.name)
        if not _NAME_PATTERN.match(name):
            print(f"  ! Skipping skill '{name}' ({skill_md}): invalid name pattern")
            continue
        skills.append(LocalSkill(name=name, body=body))
    return skills


def inject_into_instructions(base_instructions: str, skills: list[LocalSkill]) -> str:
    """Fold skill bodies into the agent's system prompt (direct-injection mode)."""

    if not skills:
        return base_instructions

    blocks = [base_instructions.strip(), "", "# Attached skills (Foundry preview)", ""]
    blocks.append(
        "The following skills provide reusable behavioral guidelines. Apply them "
        "consistently in every response.",
    )
    for skill in skills:
        blocks.extend(["", f"<skill name=\"{skill.name}\">", skill.body.strip(), "</skill>"])
    return "\n".join(blocks).strip()


def apply_skills(agent_dir: Path, base_instructions: str) -> str:
    """Discover local skills and inject them into the agent's system prompt
    (direct-injection mode). Central registration with the Foundry Skills API
    now lives in ``src/skills.py``.
    """

    skills = discover_skills(agent_dir)
    if not skills:
        return base_instructions
    print(f"  Found {len(skills)} local skill(s): {', '.join(s.name for s in skills)}")
    return inject_into_instructions(base_instructions, skills)
# --- end Foundry Skills helpers -----------------------------------------------

AGENT_NAME = "browser-assistant"
PROMPT_FILE = Path(__file__).parent / "prompts" / "operator.txt"


def build_tools() -> list:
    # Computer Use (preview) is DISABLED. It only works with the
    # `computer-use-preview` model, which is an access-gated limited model not
    # available to this subscription (ARM rejects deployment with
    # `SpecialFeatureOrQuotaIdRequired`). To enable it: request access at
    # https://aka.ms/oai/cuaaccess, deploy the model, set the agent's model to
    # "computer-use-preview", then restore the tool below.
    #
    # ComputerUsePreviewTool(
    #     display_width=1280,
    #     display_height=720,
    #     environment="browser",
    # ),

    # Browser Automation (preview) needs a Playwright Workspace project
    # connection. Provide it via BROWSER_AUTOMATION_CONNECTION_ID.
    browser_connection_id = os.environ["BROWSER_AUTOMATION_CONNECTION_ID"]
    return [
        BrowserAutomationPreviewTool(
            browser_automation_preview=BrowserAutomationToolParameters(
                connection=BrowserAutomationToolConnectionParameters(
                    project_connection_id=browser_connection_id,
                ),
            ),
        ),
        ImageGenTool(),
    ]


def main() -> None:
    endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
    credential = DefaultAzureCredential()
    client = AIProjectClient(endpoint=endpoint, credential=credential)

    instructions = apply_skills(
        Path(__file__).parent,
        PROMPT_FILE.read_text(encoding="utf-8").strip(),
    )

    agent = client.agents.create_version(
        agent_name=AGENT_NAME,
        definition=PromptAgentDefinition(
            model=os.environ["AZURE_DEPLOYMENT_NAME"],
            instructions=instructions,
            tools=build_tools(),
            temperature=0.3,
            top_p=0.95,
        ),
        description="Browser/computer operator assistant with image generation.",
    )

    print(f"Created agent: {agent.name} (version={agent.version})")


if __name__ == "__main__":
    main()
