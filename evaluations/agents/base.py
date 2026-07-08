"""
Base protocol for agent targets.

Any agent that implements this protocol can be plugged into the evaluation runner.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class AgentTarget(Protocol):
    """Protocol that all agent targets must satisfy for the evaluation runner."""

    name: str

    def __call__(self, query: str, **kwargs) -> dict:
        """Run the agent on a single query.

        Must return at minimum: {"response": str}
        Optionally: {"response": str, "context": str, "tool_calls": [...]}
        """
        ...
