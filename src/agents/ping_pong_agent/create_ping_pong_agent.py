from __future__ import annotations

# import argparse
# import json
# import logging
import os
from pathlib import Path
# from tempfile import TemporaryDirectory
# from time import monotonic, perf_counter, sleep
# from typing import Any
# from zipfile import ZIP_DEFLATED, ZipFile

from agent_framework_declarative import AgentFactory
from agent_framework_foundry_hosting import ResponsesHostServer
# from azure.ai.projects import AIProjectClient, models
from azure.identity import DefaultAzureCredential
# from ruamel.yaml import YAML

# logger = logging.getLogger(__name__)

AGENT_DIR = Path(__file__).resolve().parent
# RUNTIME_FILES = ("run_ping_pong_agent.py", "agent.yaml", "requirements.txt")


def main() -> None:
    project_endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
    with DefaultAzureCredential() as credential:
        factory = AgentFactory(
            client=None,  # Let the YAML model declaration select the native Foundry client.
            bindings=None,  # Do not bind any local function tools.
            connections=None,  # Do not provide named connection overrides.
            client_kwargs={  # Supply authentication and configuration outside the YAML document.
                "credential": credential,
                "project_endpoint": project_endpoint,
            },
            additional_mappings=None,  # Use the built-in provider mappings.
            default_provider="Foundry",  # Resolve Foundry models through FoundryChatClient.
            safe_mode=True,  # Disallow YAML expressions from accessing environment variables.
            env_file_path=os.devnull,  # Do not implicitly load a workspace dotenv file.
            env_file_encoding="utf-8",  # Preserve the factory's default text encoding.
        )
        agent = factory.create_agent_from_yaml_path(
            yaml_path=AGENT_DIR / "agent.yaml",  # Load the native declaration independently of the working directory.
        )
        ResponsesHostServer(agent).run()



if __name__ == "__main__":
    main()