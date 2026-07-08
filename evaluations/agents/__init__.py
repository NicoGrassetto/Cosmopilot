"""Pluggable agent targets for evaluation."""

from .base import AgentTarget
from .foundry_agent import FoundryAgentTarget

__all__ = ["AgentTarget", "FoundryAgentTarget"]
