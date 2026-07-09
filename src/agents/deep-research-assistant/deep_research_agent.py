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

_AZURE_AI_SCOPE = "https://ai.azure.com/.default"
_PROMPTS = Path(__file__).parent / "prompts"
MAX_ITERATIONS = 2  # reflection loops before forcing synthesis

_credential = DefaultAzureCredential()
_project = AIProjectClient(
    endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"].rstrip("/"),
    credential=_credential,
)
_openai_client = _project.get_openai_client()
_deployment = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4-1-nano")


def _prompt(name: str) -> str:
    return (_PROMPTS / name).read_text(encoding="utf-8").strip()


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
            ("system", _prompt("reflect.txt")),
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
            ("system", _prompt("synthesize.txt")),
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
    port = int(os.environ.get("PORT", "8088"))
    ResponsesHostServer(build_graph()).run(port=port)


if __name__ == "__main__":
    main()
