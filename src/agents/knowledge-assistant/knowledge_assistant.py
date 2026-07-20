"""Create the knowledge-assistant prompt agent in Azure AI Foundry.

Tools: azure_ai_search.
(memory_search_preview, SharePoint grounding, and Work IQ are currently disabled —
see build_tools. The memory store is still provisioned so it is ready to re-enable.)

Env vars:
    AZURE_AI_PROJECT_ENDPOINT   Foundry project endpoint
    AZURE_DEPLOYMENT_NAME       Chat model deployment (e.g. gpt-4-1-nano)
    SEARCH_CONNECTION_ID        Foundry connection id for the Azure AI Search service
    SEARCH_INDEX_NAME           Search index the agent queries (default: knowledge-docs)
    MEMORY_STORE_NAME           Name of the memory store (default: knowledge-memory)

Auth: DefaultAzureCredential (run `az login` first).
Note: these grounding tools require the matching connections in the project.
"""

from __future__ import annotations

import os
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    AISearchIndexResource,
    AzureAISearchTool,
    AzureAISearchToolResource,
    PromptAgentDefinition,
    # Memory search disabled for now (see build_tools).
    # MemorySearchPreviewTool,
    # SharePoint grounding disabled for now.
    # SharepointGroundingToolParameters,
    # SharepointPreviewTool,
    # Work IQ grounding disabled for now.
    # WorkIQPreviewTool,
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

AGENT_NAME = "knowledge-assistant"
PROMPT_FILE = Path(__file__).parent / "prompts" / "knowledge.txt"


def build_tools() -> list:
    search_connection_id = os.environ["SEARCH_CONNECTION_ID"]
    search_index_name = os.environ.get("SEARCH_INDEX_NAME", "knowledge-docs")

    return [
        AzureAISearchTool(
            azure_ai_search=AzureAISearchToolResource(
                indexes=[
                    AISearchIndexResource(
                        project_connection_id=search_connection_id,
                        index_name=search_index_name,
                        query_type="simple",
                        top_k=5,
                    ),
                ],
            ),
        ),
        # SharePoint grounding disabled for now.
        # SharepointPreviewTool(
        #     sharepoint_grounding_preview=SharepointGroundingToolParameters(
        #         project_connections=[],
        #     ),
        # ),
        # Work IQ grounding disabled for now.
        # WorkIQPreviewTool(
        #     project_connection_id=os.environ.get("WORK_IQ_CONNECTION_ID", ""),
        # ),
        # Memory search (preview) disabled for now. The preview memory tool
        # monopolizes the turn in the current Responses runtime: when attached it
        # is called on every request and prevents azure_ai_search from ever firing,
        # so answers are no longer grounded in the search index. The memory store
        # is still provisioned (see provision_memory_store.py) so this can be
        # re-enabled once the preview tool coexists with azure_ai_search.
        # MemorySearchPreviewTool(
        #     memory_store_name=os.environ.get("MEMORY_STORE_NAME", "knowledge-memory"),
        #     # Scope isolates memories per user. {{$userId}} binds to the signed-in
        #     # user at runtime; it is a required field on this tool.
        #     scope="{{$userId}}",
        # ),
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
        description="Enterprise knowledge assistant grounded in internal data.",
    )

    print(f"Created agent: {agent.name} (version={agent.version})")


if __name__ == "__main__":
    main()
