"""
Provision Cosmopilot skills into a Microsoft Foundry project.

Skills are versioned *behavioral guidelines* authored as ``SKILL.md`` files (the
agentskills.io format). This script reads every skill under ``agents/skills/``,
uploads each one as a new immutable version through the preview Foundry Skills
API, promotes it to the skill's ``default_version``, and can optionally reference
them all from a toolbox so any MCP client discovers them alongside tools.

Docs: https://learn.microsoft.com/azure/foundry/agents/how-to/tools/skills

Prerequisites
-------------
- ``pip install azure-ai-projects azure-identity``
- ``az login`` (authentication uses ``DefaultAzureCredential``)
- ``AZURE_AI_PROJECT_ENDPOINT`` set to your Foundry project endpoint
- RBAC: **Foundry User** on the Foundry project
- The Skills API is preview and is **not** reachable over a private endpoint.

Usage
-----
    python provision_skills.py                       # upload + promote every skill
    python provision_skills.py --toolbox cosmopilot  # ...and add them to a toolbox
    python provision_skills.py --list                # list skills already in project
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import SkillInlineContent, ToolboxSkillReference

SKILLS_ROOT = Path(__file__).resolve().parent


@dataclass
class SkillDoc:
    """A parsed SKILL.md: front-matter metadata plus the Markdown body."""

    name: str
    description: str
    instructions: str


def parse_skill_md(text: str) -> SkillDoc:
    """Parse a SKILL.md file into name, description, and body.

    Expects the agentskills.io front matter: a YAML block delimited by ``---``
    lines with unquoted ``name`` and ``description``, followed by the Markdown
    body that becomes the skill's injected instructions.
    """
    if not text.startswith("---"):
        raise ValueError("SKILL.md must start with a YAML front-matter block")
    _, front, body = text.split("---", 2)
    meta: dict[str, str] = {}
    for line in front.strip().splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    if "name" not in meta or "description" not in meta:
        raise ValueError("SKILL.md front matter needs both `name` and `description`")
    return SkillDoc(
        name=meta["name"],
        description=meta["description"],
        instructions=body.strip(),
    )


def discover_skills(root: Path = SKILLS_ROOT) -> list[SkillDoc]:
    """Read every ``<name>/SKILL.md`` under the skills root."""
    skills: list[SkillDoc] = []
    for skill_md in sorted(root.glob("*/SKILL.md")):
        doc = parse_skill_md(skill_md.read_text(encoding="utf-8"))
        if doc.name != skill_md.parent.name:
            raise ValueError(
                f"Skill name '{doc.name}' must match its directory "
                f"'{skill_md.parent.name}' ({skill_md})"
            )
        skills.append(doc)
    return skills


def make_client() -> AIProjectClient:
    """Build a project client with the Skills preview feature enabled."""
    endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
    return AIProjectClient(
        endpoint=endpoint,
        credential=DefaultAzureCredential(),
        allow_preview=True,  # opts into the Skills=V1Preview feature header
    )


def upload_skill(project: AIProjectClient, doc: SkillDoc) -> str:
    """Create a new immutable version and promote it to default.

    Returns the created version identifier.
    """
    created = project.beta.skills.create(
        name=doc.name,
        inline_content=SkillInlineContent(
            description=doc.description,
            instructions=doc.instructions,
        ),
    )
    # Creating a version does not activate it; repoint default_version to it.
    project.beta.skills.update(doc.name, default_version=created.version)
    return created.version


def add_skills_to_toolbox(
    project: AIProjectClient, toolbox: str, names: list[str]
) -> str:
    """Create a toolbox version that references each skill by name.

    Omitting a pinned version makes the toolbox follow each skill's
    ``default_version``. Returns the created toolbox version.
    """
    toolbox_version = project.beta.toolboxes.create_version(
        name=toolbox,
        description="Cosmopilot skills discoverable over MCP.",
        tools=[],
        skills=[ToolboxSkillReference(name=name) for name in names],
    )
    return toolbox_version.version


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--toolbox",
        metavar="NAME",
        help="Also create a toolbox version referencing every provisioned skill.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List skills already present in the project and exit.",
    )
    args = parser.parse_args()

    project = make_client()

    if args.list:
        for skill in project.beta.skills.list():
            print(f"  {skill.name} (default: {skill.default_version})")
        return

    skills = discover_skills()
    if not skills:
        print(f"No SKILL.md files found under {SKILLS_ROOT}")
        return

    names: list[str] = []
    for doc in skills:
        version = upload_skill(project, doc)
        names.append(doc.name)
        print(f"  uploaded '{doc.name}' -> version {version} (now default)")

    if args.toolbox:
        version = add_skills_to_toolbox(project, args.toolbox, names)
        print(f"  toolbox '{args.toolbox}' version {version} references: {', '.join(names)}")

    print(f"Provisioned {len(names)} skill(s).")


if __name__ == "__main__":
    main()
