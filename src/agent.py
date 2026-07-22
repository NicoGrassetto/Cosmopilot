from __future__ import annotations

import logging
import os
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, Tool
from azure.identity import DefaultAzureCredential
from opentelemetry import trace

logger = logging.getLogger(__name__)

# --- Foundry client-side tracing (preview) ------------------------------------
# These opt-in flags must be set before AIProjectInstrumentor().instrument() is
# called. This module doesn't load a .env, so default them here (a real
# environment value still wins). OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT
# records the prompt/response text in each trace — great for a demo, but it is
# PII, so keep it off in production.
os.environ.setdefault("AZURE_EXPERIMENTAL_ENABLE_GENAI_TRACING", "true")
os.environ.setdefault("OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", "true")

tracer = trace.get_tracer(__name__)
_tracing_ready = False


def _enable_tracing(client: AIProjectClient) -> None:
    """Send OpenTelemetry spans to the Application Insights connected to the
    Foundry project. Runs once per process; safe to call on every run()."""
    global _tracing_ready
    if _tracing_ready:
        return
    from azure.ai.projects.telemetry import AIProjectInstrumentor
    from azure.monitor.opentelemetry import configure_azure_monitor

    conn = client.telemetry.get_application_insights_connection_string()
    configure_azure_monitor(connection_string=conn)  # export spans to App Insights
    AIProjectInstrumentor().instrument()              # auto-instrument the Responses API
    _tracing_ready = True

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
    endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
    credential = DefaultAzureCredential()
    client = AIProjectClient(endpoint=endpoint, credential=credential)

    _enable_tracing(client)

    # Resolve the agent's latest version so its id can go in agent_reference.
    # Passing name + id lets Foundry correlate the trace to this exact agent.
    agent = next(iter(client.agents.list_versions(agent_name=name, order="desc")))

    openai = client.get_openai_client()
    with tracer.start_as_current_span("run"):
        response = openai.responses.create(
            input=prompt,
            extra_body={
                "agent_reference": {
                    "type": "agent_reference",
                    "name": agent.name,
                    "id": agent.id,
                }
            },
        )
    return response.output_text