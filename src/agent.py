from __future__ import annotations

import logging
import os
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, Tool
from azure.identity import DefaultAzureCredential
from opentelemetry import trace

from azure.ai.projects.telemetry import AIProjectInstrumentor
from azure.monitor.opentelemetry import configure_azure_monitor

logger = logging.getLogger(__name__)

# --- Foundry client-side tracing (preview) ------------------------------------
# These opt-in flags must be set before AIProjectInstrumentor().instrument() is
# called. This module doesn't load a .env, so default them here (a real
# environment value still wins). OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT
# records the prompt/response text in each trace — great for a demo, but it is
# PII, so keep it off in production.
os.environ.setdefault("AZURE_EXPERIMENTAL_ENABLE_GENAI_TRACING", "true")
os.environ.setdefault("OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", "true")

_tracing_ready = False


def create(name: str, instructions: str, description: str, tools: list[Tool] | None = None, temperature: float = 0.4, top_p: float = 0.95):
    endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
    credential = DefaultAzureCredential()
    client = AIProjectClient(endpoint=endpoint, credential=credential)
    agent = client.agents.create_version(
        agent_name=name,
        definition=PromptAgentDefinition(
            model=os.environ["AZURE_DEPLOYMENT_NAME"],
            instructions=instructions,
            tools=tools,
            temperature=temperature,
            top_p=top_p,
        ),
        description=description,
    )

    logger.info("Created agent: %s (version=%s)", agent.name, agent.version)


def run(name: str, prompt: str) -> str:
    global _tracing_ready
    client = AIProjectClient(endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=DefaultAzureCredential())

    # Enable Foundry client-side tracing once per process: export spans to the
    # Application Insights connected to the project and auto-instrument the
    # Responses API.
    if not _tracing_ready:
        configure_azure_monitor(
            connection_string=client.telemetry.get_application_insights_connection_string()
        )
        AIProjectInstrumentor().instrument()
        _tracing_ready = True

    tracer = trace.get_tracer(__name__)

    # Resolve the agent's latest version so its id can go in agent_reference.
    # Passing name + id lets Foundry correlate the trace to this exact agent.
    agent = next(iter(client.agents.list_versions(agent_name=name, order="desc")))
    openai = client.get_openai_client()
    body = {
        "input": prompt,
        "extra_body": {
            "agent_reference": {"type": "agent_reference", "name": agent.name, "id": agent.id}
        },
    }

    # The preview GenAI instrumentation occasionally races on the first
    # instrumented call in a fresh process (AttributeError on a NonRecordingSpan);
    # the exporter is warm afterwards, so one retry succeeds.
    try:
        with tracer.start_as_current_span("run"):
            response = openai.responses.create(**body)
    except AttributeError:
        with tracer.start_as_current_span("run"):
            response = openai.responses.create(**body)
    return response.output_text