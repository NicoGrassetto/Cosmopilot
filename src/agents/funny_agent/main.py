"""Serve Funny Agent through Microsoft Foundry's Responses protocol."""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from time import perf_counter

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from langchain.agents import create_agent
from langchain_azure_ai.agents.hosting import ResponsesHostServer
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)
AGENT_DIR = Path(__file__).resolve().parent


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    )
    try:
        project_endpoint = (
            os.environ.get("FOUNDRY_PROJECT_ENDPOINT")
            or os.environ["AZURE_AI_PROJECT_ENDPOINT"]
        )
        model_deployment = (
            os.environ.get("FOUNDRY_MODEL_NAME")
            or os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME")
            or os.environ["AZURE_DEPLOYMENT_NAME"]
        )
        port = int(os.environ.get("PORT", "8088"))
        instructions = (AGENT_DIR / "prompts" / "instructions.md").read_text(encoding="utf-8")
        skill = (AGENT_DIR / "skills" / "joke-writing" / "SKILL.md").read_text(encoding="utf-8")

        with (
            DefaultAzureCredential() as credential,
            AIProjectClient(
                endpoint=project_endpoint,  # Select the configured Foundry project.
                credential=credential,  # Keep Azure authentication alive while serving requests.
                allow_preview=False,  # Model inference uses the stable project API.
            ) as project,
            project.get_openai_client(
                agent_name=None,  # Connect to model inference rather than another agent.
            ) as openai_client,
        ):
            model = ChatOpenAI(
                model=model_deployment,  # Use the configured Foundry model deployment.
                base_url=str(openai_client.base_url),  # Use the SDK's project inference endpoint.
                api_key=get_bearer_token_provider(
                    credential,  # Refresh model access tokens through the managed credential.
                    "https://ai.azure.com/.default",  # Request the Foundry inference audience.
                ),  # Obtain access tokens on demand instead of storing a static key.
                client=openai_client.chat.completions,  # Reuse the context-managed synchronous client.
                root_client=openai_client,  # Reuse its Responses API operations as well.
                use_responses_api=True,  # Invoke the model through the Responses API.
                output_version="responses/v1",  # Preserve LangChain's Responses content format.
                timeout=60,  # Bound each model request to sixty seconds.
                max_retries=2,  # Retry transient inference failures at most twice.
            )
            async with model.root_async_client:
                agent = create_agent(
                    model=model,  # Generate jokes using the configured chat model.
                    tools=[],  # Joke writing does not require external tools.
                    system_prompt=f"{instructions}\n\n{skill}",  # Attach both authored runtime assets.
                    middleware=(),  # Use the standard LangChain agent loop.
                    response_format=None,  # Return plain text rather than a structured schema.
                    state_schema=None,  # Use LangChain's default message state.
                    context_schema=None,  # Do not require additional invocation context.
                    checkpointer=None,  # Let the Responses host manage conversation history.
                    store=None,  # Do not configure an additional persistent store.
                    interrupt_before=None,  # Do not interrupt before graph nodes.
                    interrupt_after=None,  # Do not interrupt after graph nodes.
                    debug=False,  # Avoid logging user messages through graph debugging.
                    name="funny-agent",  # Identify this graph in the hosting adapter.
                    cache=None,  # Generate a fresh response for each request.
                    transformers=None,  # Preserve the standard graph behavior.
                )
                started = perf_counter()
                logger.info("Starting hosted agent name=funny-agent model=%s port=%d", model_deployment, port)
                server = ResponsesHostServer(
                    graph=agent,  # Serve the compiled LangChain agent graph.
                    app=None,  # Let the adapter create its standard Responses application.
                    options=None,  # Preserve the adapter's standard protocol behavior.
                    store=None,  # Use Foundry storage when hosted and local defaults otherwise.
                    prefix="",  # Expose the standard unprefixed Responses routes.
                    applicationinsights_connection_string=None,  # Leave telemetry to environment configuration.
                    graceful_shutdown_timeout=None,  # Use the host's default shutdown timeout.
                )
                await server.run_async(
                    host="0.0.0.0",  # Listen on the interface required by the hosted runtime.
                    port=port,  # Honor the platform or local PORT configuration.
                )
                logger.info(
                    "Stopped hosted agent name=funny-agent duration_ms=%.0f",
                    (perf_counter() - started) * 1000,
                )
    except Exception:
        logger.exception("Hosted agent failed name=funny-agent")
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())