"""deep-research-assistant — a hosted LangGraph agent for Azure AI Foundry.

An iterative deep-research agent built on LangGraph and surfaced as a Foundry
*hosted agent* over the OpenAI-compatible Responses protocol
(`langchain_azure_ai.agents.hosting.ResponsesHostServer`).

Flow (StateGraph):

    plan  ->  search  ->  reflect  --(MORE)-->  search
                              |
                           (SUFFICIENT)
                              v
                          synthesize  ->  END

Web search is performed with Foundry's built-in `web_search` tool, invoked
through the project's OpenAI-compatible Responses API — no third-party search
key. Web search must be enabled/connected on the Foundry project.

Environment variables (injected by Foundry at runtime, set locally for dev):
    FOUNDRY_PROJECT_ENDPOINT        Foundry project endpoint
    AZURE_AI_MODEL_DEPLOYMENT_NAME  Chat model deployment (e.g. gpt-4-1-nano)
    PORT                            Host port (default 8088)

Auth: DefaultAzureCredential (run `az login` for local dev).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated, TypedDict

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from langchain_azure_ai.agents.hosting import ResponsesHostServer

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

_AZURE_AI_SCOPE = "https://ai.azure.com/.default"
_PROMPTS = Path(__file__).parent / "prompts"
MAX_ITERATIONS = 2  # reflection loops before forcing synthesis

_credential = DefaultAzureCredential()
_endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"].rstrip("/")
_project = AIProjectClient(
    endpoint=_endpoint,
    credential=_credential,
)
_openai_client = _project.get_openai_client()
_deployment = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4-1-nano")

# Foundry Skills (preview): loaded from ./skills and injected into the prompts
# that produce reasoning and the final answer (direct-injection mode).
_SKILLS = discover_skills(Path(__file__).parent)


def _prompt(name: str) -> str:
    return (_PROMPTS / name).read_text(encoding="utf-8").strip()


def _prompt_with_skills(name: str) -> str:
    """Return a system prompt augmented with the agent's attached skills."""
    return inject_into_instructions(_prompt(name), _SKILLS)


def _build_chat_model() -> ChatOpenAI:
    token_provider = get_bearer_token_provider(_credential, _AZURE_AI_SCOPE)
    return ChatOpenAI(
        model=_deployment,
        base_url=str(_openai_client.base_url),
        api_key=token_provider,
    )


_model = _build_chat_model()


def _foundry_web_search(query: str) -> str:
    """Run a grounded web search via Foundry's built-in web_search tool."""
    try:
        response = _openai_client.responses.create(
            model=_deployment,
            tools=[{"type": "web_search"}],
            input=query,
        )
        return (getattr(response, "output_text", "") or "").strip()
    except Exception as exc:  # noqa: BLE001 - degrade gracefully on tool errors
        return f"[search failed for '{query}': {exc}]"


class ResearchState(TypedDict):
    messages: Annotated[list, add_messages]
    question: str
    subquestions: list[str]
    notes: list[str]
    iterations: int


def plan_node(state: ResearchState) -> dict:
    question = ""
    for message in reversed(state["messages"]):
        if isinstance(message, HumanMessage):
            question = message.content
            break
    result = _model.invoke(
        [
            ("system", _prompt("planner.txt")),
            ("human", question),
        ]
    )
    subquestions = [line.strip() for line in result.content.splitlines() if line.strip()]
    return {
        "question": question,
        "subquestions": subquestions or [question],
        "notes": [],
        "iterations": 0,
    }


def search_node(state: ResearchState) -> dict:
    new_notes = list(state.get("notes", []))
    for subquestion in state["subquestions"]:
        new_notes.append(f"## {subquestion}\n{_foundry_web_search(subquestion)}")
    return {"notes": new_notes}


def reflect_node(state: ResearchState) -> dict:
    notes_blob = "\n\n".join(state["notes"])
    result = _model.invoke(
        [
            ("system", _prompt_with_skills("reflect.txt")),
            ("human", f"Question:\n{state['question']}\n\nNotes:\n{notes_blob}"),
        ]
    )
    lines = [line.strip() for line in result.content.splitlines() if line.strip()]
    decision = lines[0].upper() if lines else "SUFFICIENT"
    follow_ups = lines[1:]
    update: dict = {"iterations": state["iterations"] + 1}
    if decision.startswith("MORE") and follow_ups:
        update["subquestions"] = follow_ups
    else:
        update["subquestions"] = []
    return update


def _should_continue(state: ResearchState) -> str:
    if state["subquestions"] and state["iterations"] < MAX_ITERATIONS:
        return "search"
    return "synthesize"


def synthesize_node(state: ResearchState) -> dict:
    notes_blob = "\n\n".join(state["notes"])
    result = _model.invoke(
        [
            ("system", _prompt_with_skills("synthesize.txt")),
            ("human", f"Question:\n{state['question']}\n\nNotes:\n{notes_blob}"),
        ]
    )
    return {"messages": [AIMessage(content=result.content)]}


def build_graph():
    graph = StateGraph(ResearchState)
    graph.add_node("plan", plan_node)
    graph.add_node("search", search_node)
    graph.add_node("reflect", reflect_node)
    graph.add_node("synthesize", synthesize_node)

    graph.add_edge(START, "plan")
    graph.add_edge("plan", "search")
    graph.add_edge("search", "reflect")
    graph.add_conditional_edges(
        "reflect",
        _should_continue,
        {"search": "search", "synthesize": "synthesize"},
    )
    graph.add_edge("synthesize", END)
    return graph.compile()


def main() -> None:
    # Register the local skills with Foundry (preview, best-effort) at startup.
    register_skills(_endpoint, _credential, _SKILLS)
    port = int(os.environ.get("PORT", "8088"))
    ResponsesHostServer(build_graph()).run(port=port)


if __name__ == "__main__":
    main()
