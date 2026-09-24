from pathlib import Path

import yaml
from azure.ai.projects.models import PromptAgentDefinition

from agents.agents import create_agent_version
from memory_storage import ensure_agent_memory_store

spec = yaml.safe_load(
    Path(__file__).with_name("agent.yaml").read_text(encoding="utf-8")
)

# ------- Memory store--------
ensure_agent_memory_store(spec["name"])
# --------

agent = create_agent_version(
    agent_name=spec["name"],
    definition=PromptAgentDefinition(spec["definition"]),
    allow_preview=True,
)

print(f"Created {agent.name}, version {agent.version}")