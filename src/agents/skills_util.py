"""Shared helpers for Foundry *Skills* (preview) across the Cosmopilot agents.

Each agent keeps a local ``skills/`` directory. Every skill lives in its own
subdirectory as a ``SKILL.md`` file following the Agent Skills spec
(https://agentskills.io): a YAML front matter block with ``name`` and
``description`` plus a Markdown body of instructions.

This module offers two things (matching the two Foundry consumption modes):

1. ``register_skills`` — push each local ``SKILL.md`` to Foundry as a versioned
   skill through the preview Skills API (``project.beta.skills``). Best-effort:
   the preview API is not GA, so any failure is logged and swallowed so agent
   creation still succeeds.
2. ``inject_into_instructions`` — the *direct injection* mode. Fold the skill
   bodies into the agent's system prompt so the guidelines take effect at
   runtime even while the Skills API is in preview.

Skills API reference:
https://learn.microsoft.com/azure/foundry/agents/how-to/tools/skills
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# Preview header required on every Skills API call.
SKILLS_PREVIEW_FEATURE = "Skills=V1Preview"

_NAME_PATTERN = re.compile(r"^[a-z0-9]([a-z0-9\-]*[a-z0-9])?$")


@dataclass
class LocalSkill:
    """A skill authored locally as ``skills/<name>/SKILL.md``."""

    name: str
    description: str
    body: str
    path: Path


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
        skills.append(
            LocalSkill(
                name=name,
                description=meta.get("description", ""),
                body=body,
                path=skill_md,
            )
        )
    return skills


def register_skills(endpoint: str, credential, skills: list[LocalSkill], *, set_default: bool = True) -> None:
    """Register each local skill as a Foundry skill version (preview, best-effort).

    Builds its own ``AIProjectClient(..., allow_preview=True)`` so the caller's
    agent-creation client is never affected. Any error (older SDK without the
    preview kwarg, preview not enabled, missing RBAC) is logged and swallowed so
    it never blocks agent creation.
    """

    if not skills:
        return

    try:
        from azure.ai.projects import AIProjectClient
        from azure.ai.projects.models import SkillInlineContent
    except Exception as exc:  # noqa: BLE001 - SDK too old / preview models absent
        print(f"  ! Skills API unavailable, skipping registration: {exc}")
        return

    try:
        project = AIProjectClient(endpoint=endpoint, credential=credential, allow_preview=True)
    except TypeError as exc:  # allow_preview unsupported on this SDK version
        print(f"  ! SDK does not support the Skills preview client, skipping: {exc}")
        return
    except Exception as exc:  # noqa: BLE001
        print(f"  ! Could not create preview client, skipping skills: {exc}")
        return

    beta = getattr(project, "beta", None)
    skills_client = getattr(beta, "skills", None) if beta else None
    if skills_client is None:
        print("  ! project.beta.skills not available; skipping skill registration")
        return

    for skill in skills:
        try:
            created = skills_client.create(
                name=skill.name,
                inline_content=SkillInlineContent(
                    description=skill.description,
                    instructions=skill.body,
                ),
            )
            version = getattr(created, "version", None)
            if set_default and version:
                skills_client.update(skill.name, default_version=version)
            print(f"  ✓ Registered skill '{skill.name}' (version={version})")
        except Exception as exc:  # noqa: BLE001 - preview API, degrade gracefully
            print(f"  ! Could not register skill '{skill.name}': {exc}")


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


def apply_skills(agent_dir: Path, base_instructions: str, endpoint: str | None = None, credential=None) -> str:
    """Convenience wrapper: discover, (optionally) register, and inject skills.

    Pass ``endpoint`` and ``credential`` to also register the skills with Foundry
    through the preview Skills API. Registration is best-effort; this function
    always returns the augmented instructions (direct-injection mode).
    """

    skills = discover_skills(agent_dir)
    if not skills:
        return base_instructions
    print(f"  Found {len(skills)} local skill(s): {', '.join(s.name for s in skills)}")
    if endpoint and credential is not None:
        register_skills(endpoint, credential, skills)
    return inject_into_instructions(base_instructions, skills)
