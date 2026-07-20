"""Create the devops-assistant prompt agent in Azure AI Foundry.

Tools: shell, apply_patch (Codex-family — require a Codex model such as
gpt-5.3-codex; verified working there).
(local_shell is deprecated and removed from the Responses API; azure_function
is currently
disabled — see build_tools.)

Env vars:
    AZURE_AI_PROJECT_ENDPOINT   Foundry project endpoint
    AZURE_DEPLOYMENT_NAME       Chat model deployment (must be a Codex model,
                                e.g. gpt-5-3-codex, for shell/apply_patch)

Auth: DefaultAzureCredential (run `az login` first).
Note: azure_function (disabled) requires a configured Azure Function binding.
"""

from __future__ import annotations

import os
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    ApplyPatchToolParam,
    # azure_function disabled for now (see build_tools).
    # AzureFunctionTool,
    FunctionShellToolParam,
    FunctionShellToolParamEnvironmentLocalEnvironmentParam,
    # local_shell is deprecated (removed from the Responses API) — see build_tools.
    # LocalShellToolParam,
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

AGENT_NAME = "devops-assistant"
PROMPT_FILE = Path(__file__).parent / "prompts" / "devops.txt"


def build_tools() -> list:
    return [
        # local_shell is deprecated: the Responses API rejects it for every model
        # with "The local_shell tool is no longer supported." Use shell instead.
        # LocalShellToolParam(),
        # shell + apply_patch are Codex-family tools: they require a Codex model
        # such as gpt-5.3-codex (verified). Older gpt-5-codex and the non-Codex
        # models (gpt-4.1, gpt-4.1-nano, model-router, Phi-4-mini-reasoning) all
        # reject them. The deprecated "name" field must be omitted from shell.
        FunctionShellToolParam(
            environment=FunctionShellToolParamEnvironmentLocalEnvironmentParam(),
        ),
        ApplyPatchToolParam(),
        # azure_function disabled for now. Re-enable once an Azure Function
        # binding (function + input_binding + output_binding) is configured.
        # AzureFunctionTool(azure_function={}),
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
            temperature=0.2,
            top_p=0.95,
        ),
        description="DevOps automation assistant for shell, patching, and functions.",
    )

    print(f"Created agent: {agent.name} (version={agent.version})")


if __name__ == "__main__":
    main()
