"""Package and register the LangChain funny agent using the current environment."""

from __future__ import annotations

import json
import logging
import os
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
from zipfile import ZIP_DEFLATED, ZipFile

from azure.ai.projects import AIProjectClient, models
from azure.identity import DefaultAzureCredential
from ruamel.yaml import YAML

logger = logging.getLogger(__name__)
AGENT_DIR = Path(__file__).resolve().parent
AGENT_NAME = "funny-agent"
RUNTIME_REQUIREMENTS = "\n".join(
    (
        "azure-ai-projects==2.7.0",
        "azure-identity==1.25.3",
        "langchain==1.4.0",
        "langchain-azure-ai[hosting]==1.2.9",
        "langchain-openai==1.6.2",
        "openai==3.0.0",
        "",
    )
)


def create_funny_agent() -> models.AgentVersionDetails:
    project_endpoint = (
        os.environ.get("FOUNDRY_PROJECT_ENDPOINT")
        or os.environ["AZURE_AI_PROJECT_ENDPOINT"]
    )
    model_deployment = (
        os.environ.get("FOUNDRY_MODEL_NAME")
        or os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME")
        or os.environ["AZURE_DEPLOYMENT_NAME"]
    )
    instructions = (AGENT_DIR / "prompts" / "instructions.md").read_text(encoding="utf-8")
    skill = (AGENT_DIR / "skills" / "joke-writing" / "SKILL.md").read_text(encoding="utf-8")
    sections = skill.split("---", 2)
    if not instructions.strip() or len(sections) != 3 or sections[0].strip():
        raise ValueError("The agent requires a nonempty prompt and a skill with YAML frontmatter.")
    metadata = YAML(typ="safe").load(sections[1])
    if (
        not isinstance(metadata, dict)
        or metadata.get("name") != "joke-writing"
        or not isinstance(metadata.get("description"), str)
        or not 1 <= len(metadata["description"].strip()) <= 1024
        or not sections[2].strip()
    ):
        raise ValueError("The joke-writing skill requires its matching name, description, and instructions.")

    with TemporaryDirectory() as directory:
        package_path = Path(directory) / "funny-agent.zip"
        with ZipFile(package_path, "w", compression=ZIP_DEFLATED) as archive:
            for filename in (
                "main.py",
                "prompts/instructions.md",
                "skills/joke-writing/SKILL.md",
            ):
                archive.write(AGENT_DIR / filename, arcname=filename)
            archive.writestr("requirements.txt", RUNTIME_REQUIREMENTS)

        with (
            DefaultAzureCredential() as credential,
            AIProjectClient(
                endpoint=project_endpoint,  # Select the configured Foundry project.
                credential=credential,  # Authenticate through the standard Azure credential chain.
                allow_preview=True,  # Allow the repository's hosted-agent preview features.
            ) as client,
            package_path.open("rb") as code,
        ):
            started = perf_counter()
            logger.info("Creating hosted agent name=%s model=%s", AGENT_NAME, model_deployment)
            version = client.agents.create_version_from_code(
                agent_name=AGENT_NAME,  # Register a new version under this stable agent name.
                definition=models.HostedAgentDefinition(
                    cpu="0.5",  # Allocate half a CPU to the hosted runtime.
                    memory="1Gi",  # Allocate one GiB of memory to the hosted runtime.
                    rai_config=None,  # Preserve the project's default responsible-AI configuration.
                    environment_variables={
                        "AZURE_AI_PROJECT_ENDPOINT": project_endpoint,
                        "AZURE_AI_MODEL_DEPLOYMENT_NAME": model_deployment,
                    },  # Pass non-secret model configuration to the hosted process.
                    container_configuration=None,  # Use source-code hosting instead of an image.
                    protocol_versions=[
                        models.ProtocolVersionRecord(
                            protocol="responses",  # Expose the standard Responses protocol.
                            version="2.0.0",  # Match the LangChain hosting adapter's protocol version.
                        )
                    ],  # Advertise the runtime's supported protocol.
                    code_configuration=models.CodeConfiguration(
                        runtime="python_3_13",  # Use the supported Python 3.13 hosted runtime.
                        entry_point=["python", "main.py"],  # Start the agent's runtime entrypoint.
                        dependency_resolution="remote_build",  # Install the packaged dependency pins remotely.
                    ),  # Build the hosted process from the uploaded ZIP.
                    telemetry_config=None,  # Leave telemetry configuration at the project default.
                    session_configuration=None,  # Preserve the service's default session settings.
                ),  # Describe the hosted LangChain agent.
                code=code,  # Upload the complete runtime and its Markdown assets.
                code_zip_sha256=sha256(package_path.read_bytes()).hexdigest(),  # Verify the uploaded package content.
                description="A LangChain agent that tells short, original, family-friendly jokes.",  # Describe the agent in Foundry.
                metadata={"framework": "langchain", "purpose": "jokes"},  # Label the version for discovery.
            )
            logger.info(
                "Created hosted agent name=%s version=%s duration_ms=%.0f",
                version.name,
                version.version,
                (perf_counter() - started) * 1000,
            )
            return version


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    )
    try:
        version = create_funny_agent()
        print(json.dumps({"name": version.name, "version": version.version, "status": version.status}))
    except Exception:
        logger.exception("Hosted agent creation failed name=%s", AGENT_NAME)
        raise SystemExit(1)


if __name__ == "__main__":
    main()