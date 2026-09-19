from __future__ import annotations

import os
from pathlib import Path

from agent_framework_declarative import AgentFactory
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.identity import DefaultAzureCredential

AGENT_DIR = Path(__file__).resolve().parent


def main() -> None:
    project_endpoint = (
        os.environ.get("FOUNDRY_PROJECT_ENDPOINT")
        or os.environ["AZURE_AI_PROJECT_ENDPOINT"]
    )

    with DefaultAzureCredential() as credential:
        factory = AgentFactory(
            client=None,
            bindings=None,
            connections=None,
            client_kwargs={
                "credential": credential,
                "project_endpoint": project_endpoint,
            },
            additional_mappings=None,
            default_provider="Foundry",
            safe_mode=True,
            env_file_path=os.devnull,
            env_file_encoding="utf-8",
        )
        agent = factory.create_agent_from_yaml_path(
            yaml_path=AGENT_DIR / "agent.yaml",
        )
        ResponsesHostServer(agent).run()


if __name__ == "__main__":
    main()