"""Register local ``SKILL.md`` skills with the Foundry project (preview Skills API).

Discovers every ``agents/<agent>/skills/<skill>/SKILL.md`` in this repo and uploads
it as a versioned Foundry skill, promoting each new version to the default.

Env vars:
    AZURE_AI_PROJECT_ENDPOINT   Foundry project endpoint

Auth: DefaultAzureCredential (run ``az login`` first).
Skills API: https://learn.microsoft.com/azure/foundry/agents/how-to/tools/skills
"""

from __future__ import annotations

import io
import logging
import os
import zipfile
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)


def create() -> None:
    """Discover and register every local skill as a versioned Foundry skill."""
    endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=endpoint, credential=credential, allow_preview=True) as project,
    ):
        for skill_md in sorted((Path(__file__).parent / "agents").glob("*/skills/*/SKILL.md")):
            name = skill_md.parent.name  # directory name == SKILL.md front-matter `name`

            # Zip the skill folder in memory (SKILL.md + any sibling assets); the server
            # parses the front matter to populate the version description and instructions.
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
                for file in sorted(skill_md.parent.rglob("*")):
                    if file.is_file():
                        archive.write(file, file.relative_to(skill_md.parent))

            try:
                version = project.beta.skills.create(name=name, file=buffer.getvalue())
                project.beta.skills.update(name, default_version=version.version)
                logger.info("Registered skill %s (version=%s)", version.name, version.version)
            except Exception:  # noqa: BLE001 - keep registering the rest of the batch
                logger.exception("Failed to register skill %s", name)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    )
    create()
