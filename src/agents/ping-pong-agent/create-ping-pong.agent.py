from pathlib import Path

import yaml
from azure.ai.projects.models import PromptAgentDefinition

from agents.agents import create_agent_version

spec = yaml.safe_load(
    Path(__file__).with_name("ping-pong.yaml").read_text(encoding="utf-8")
)

agent = create_agent_version(
    agent_name=spec["name"],
    definition=PromptAgentDefinition(spec["definition"]),
)

print(f"Created {agent.name}, version {agent.version}")