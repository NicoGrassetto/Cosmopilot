"""
Load Foundry skills as extra system instructions for the hosted agent.

Skills are ``SKILL.md`` behavioral guidelines managed in a Microsoft Foundry
project (the agentskills.io format). This helper resolves them in one of two
modes and returns their Markdown bodies concatenated, so the hosted agent can
append them to its own instructions at startup — the "direct injection" pattern
from the Foundry docs.

- ``local``   (default): read the SKILL.md sources bundled in ``agents/skills/``.
- ``foundry``          : download the active (default) version of each named
                         skill from the Foundry Skills API and read its
                         SKILL.md from the returned ZIP.

Select the mode with the ``FOUNDRY_SKILLS_SOURCE`` env var (``local`` | ``foundry``).

Docs: https://learn.microsoft.com/azure/foundry/agents/how-to/tools/skills
"""

from __future__ import annotations

import io
import os
import zipfile
from dataclasses import dataclass
from pathlib import Path

# The shared skill sources live one level up, in agents/skills/.
LOCAL_SKILLS_ROOT = Path(__file__).resolve().parent.parent / "skills"

# Skills that shape this data-insights agent: how it queries Cosmos DB and how
# it formats event summaries. (incident-triage-policy is used by the multi-agent.)
DEFAULT_SKILLS: tuple[str, ...] = (
    "cosmos-query-standards",
    "change-feed-summary-format",
)


@dataclass
class SkillDoc:
    name: str
    description: str
    body: str


def _parse_skill_md(text: str) -> SkillDoc:
    if not text.startswith("---"):
        raise ValueError("SKILL.md must start with a YAML front-matter block")
    _, front, body = text.split("---", 2)
    meta: dict[str, str] = {}
    for line in front.strip().splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return SkillDoc(meta.get("name", ""), meta.get("description", ""), body.strip())


def _load_local(names: tuple[str, ...]) -> list[SkillDoc]:
    docs: list[SkillDoc] = []
    for name in names:
        path = LOCAL_SKILLS_ROOT / name / "SKILL.md"
        if path.exists():
            docs.append(_parse_skill_md(path.read_text(encoding="utf-8")))
    return docs


def _download_from_foundry(names: tuple[str, ...]) -> list[SkillDoc]:
    from azure.identity import DefaultAzureCredential
    from azure.ai.projects import AIProjectClient

    endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
    docs: list[SkillDoc] = []
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=endpoint, credential=credential, allow_preview=True
        ) as project,
    ):
        for name in names:
            zip_bytes = b"".join(project.beta.skills.download_content(name))
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
                skill_file = next(
                    entry for entry in archive.namelist() if entry.endswith("SKILL.md")
                )
                text = archive.read(skill_file).decode("utf-8")
            docs.append(_parse_skill_md(text))
    return docs


def load_skills(
    names: tuple[str, ...] = DEFAULT_SKILLS, source: str | None = None
) -> list[SkillDoc]:
    """Resolve the named skills from the selected source."""
    source = (source or os.getenv("FOUNDRY_SKILLS_SOURCE", "local")).lower()
    if source == "foundry":
        return _download_from_foundry(names)
    return _load_local(names)


def build_skill_instructions(
    names: tuple[str, ...] = DEFAULT_SKILLS, source: str | None = None
) -> str:
    """Return the skill bodies formatted for appending to agent instructions."""
    docs = load_skills(names, source)
    if not docs:
        return ""
    blocks = [
        "\n\n# Applied skills\n\n"
        "The following organization skills apply to every response:"
    ]
    for doc in docs:
        blocks.append(f"\n## Skill: {doc.name}\n{doc.body}")
    return "\n".join(blocks)
