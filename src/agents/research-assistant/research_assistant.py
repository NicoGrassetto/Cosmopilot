"""Create the research-assistant prompt agent in Azure AI Foundry.

Tools: web_search, bing_grounding, file_search.
(bing_custom_search_preview is currently disabled - see build_tools for why.)

Env vars:
    AZURE_AI_PROJECT_ENDPOINT   Foundry project endpoint
    AZURE_DEPLOYMENT_NAME       Chat model deployment (e.g. gpt-4-1-nano)
    BING_CONNECTION_ID          Foundry connection id for Bing grounding
    FILE_SEARCH_VECTOR_STORE_ID Vector store id for file search

Auth: DefaultAzureCredential (run `az login` first).
Note: grounding tools require the matching connections to exist in the project.
"""

from __future__ import annotations

import os
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    # BingCustomSearchConfiguration,      # noqa: ERA001 - custom search disabled (see below)
    # BingCustomSearchPreviewTool,        # noqa: ERA001
    # BingCustomSearchToolParameters,     # noqa: ERA001
    BingGroundingSearchConfiguration,
    BingGroundingSearchToolParameters,
    BingGroundingTool,
    FileSearchTool,
    PromptAgentDefinition,
    WebSearchTool,
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
# --- end Foundry Skills helpers -----------------------------------------------

AGENT_NAME = "research-assistant"
PROMPT_FILE = Path(__file__).parent / "prompts" / "researcher.txt"


def build_tools() -> list:
    bing_connection_id = os.environ["BING_CONNECTION_ID"]
    vector_store_id = os.environ["FILE_SEARCH_VECTOR_STORE_ID"]

    # NOTE: bing_custom_search_preview is disabled. The Foundry Responses runtime
    # rejects it with a hard HTTP 400 (unsupported tool type), which blocks *every*
    # query to the agent while it is attached. Re-enable once the preview tool is
    # supported by the runtime and a Bing Custom Search configuration exists.
    # custom_connection_id = os.environ.get("BING_CUSTOM_CONNECTION_ID", "")
    # custom_instance_name = os.environ.get("BING_CUSTOM_INSTANCE_NAME", "")
    # custom_search_configs = []
    # if custom_connection_id and custom_instance_name:
    #     custom_search_configs.append(
    #         BingCustomSearchConfiguration(
    #             project_connection_id=custom_connection_id,
    #             instance_name=custom_instance_name,
    #         ),
    #     )

    return [
        WebSearchTool(),
        BingGroundingTool(
            bing_grounding=BingGroundingSearchToolParameters(
                search_configurations=[
                    BingGroundingSearchConfiguration(
                        project_connection_id=bing_connection_id,
                    ),
                ],
            ),
        ),
        # BingCustomSearchPreviewTool(
        #     bing_custom_search_preview=BingCustomSearchToolParameters(
        #         search_configurations=custom_search_configs,
        #     ),
        # ),
        FileSearchTool(
            vector_store_ids=[vector_store_id],
        ),
    ]


def main() -> None:
    endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
    credential = DefaultAzureCredential()
    client = AIProjectClient(endpoint=endpoint, credential=credential)

    instructions = apply_skills(
        Path(__file__).parent,
        PROMPT_FILE.read_text(encoding="utf-8").strip(),
        endpoint=endpoint,
        credential=credential,
    )

    agent = client.agents.create_version(
        agent_name=AGENT_NAME,
        definition=PromptAgentDefinition(
            model=os.environ["AZURE_DEPLOYMENT_NAME"],
            instructions=instructions,
            tools=build_tools(),
            temperature=0.4,
            top_p=0.95,
        ),
        description="Web and document research assistant with grounded citations.",
    )

    print(f"Created agent: {agent.name} (version={agent.version})")


if __name__ == "__main__":
    main()
