"""
Cosmopilot Multi-Agent Orchestrator (MAF)

Implements the incident triage multi-agent scenario using the Microsoft Agent
Framework. Coordinates detector, diagnostician, remediator, and reporter agents
in a sequential workflow with human-in-the-loop gates.
"""

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from azure.ai.projects import FoundryClient
from azure.identity import DefaultAzureCredential

# Shared, single-source-of-truth tool definitions (see agents/_shared).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared import tools as build_tools  # noqa: E402


@dataclass
class AgentConfig:
    name: str
    instructions: str
    tools: list


AGENTS = {
    "detector": AgentConfig(
        name="cosmopilot-detector",
        instructions=(
            "You are the Anomaly Detector agent. Analyze incoming telemetry data "
            "and identify anomalies, threshold breaches, and unusual patterns. "
            "Output a structured JSON assessment with: metric_name, current_value, "
            "expected_range, deviation_pct, and anomaly_type."
        ),
        tools=build_tools("code_interpreter"),
    ),
    "diagnostician": AgentConfig(
        name="cosmopilot-diagnostician",
        instructions=(
            "You are the Root Cause Diagnostician. Given an anomaly assessment, "
            "investigate possible root causes by correlating with recent changes. "
            "Output: probable_causes (ranked), confidence_score, supporting_evidence, "
            "and affected_components as JSON."
        ),
        tools=build_tools("code_interpreter"),
    ),
    "remediator": AgentConfig(
        name="cosmopilot-remediator",
        instructions=(
            "You are the Remediation Advisor. Based on the diagnosis, suggest "
            "concrete remediation steps. For each: action, risk_level, "
            "estimated_impact, rollback_plan, and human_approval required."
        ),
        tools=build_tools("code_interpreter"),
    ),
    "reporter": AgentConfig(
        name="cosmopilot-reporter",
        instructions=(
            "You are the Incident Reporter. Synthesize all findings into a clear "
            "incident report with: title, severity, timeline, root cause, "
            "recommended actions, and status. Format as markdown."
        ),
        tools=build_tools("code_interpreter"),
    ),
}


class MultiAgentOrchestrator:
    """Orchestrates the multi-agent incident triage pipeline."""

    def __init__(self, client: FoundryClient, model: str = "gpt-4o-mini"):
        self.client = client
        self.model = model
        self._agent_ids: dict[str, str] = {}

    def setup(self):
        """Create all agents in Foundry."""
        for key, config in AGENTS.items():
            agent = self.client.agents.create(
                name=config.name,
                model=self.model,
                instructions=config.instructions,
                tools=config.tools,
            )
            self._agent_ids[key] = agent.id
            print(f"  Created agent '{config.name}' -> {agent.id}")

    def _run_agent(self, agent_key: str, message: str) -> str:
        """Run a single agent and return its response."""
        agent_id = self._agent_ids[agent_key]
        thread = self.client.agents.threads.create()

        self.client.agents.messages.create(
            thread_id=thread.id, role="user", content=message
        )

        run = self.client.agents.runs.create_and_wait(
            thread_id=thread.id, agent_id=agent_id
        )

        if run.status == "failed":
            raise RuntimeError(
                f"Agent '{agent_key}' failed: {run.last_error}"
            )

        messages = self.client.agents.messages.list(thread_id=thread.id)
        return messages.data[0].content[0].text.value

    def run_triage(self, telemetry_data: str) -> dict[str, str]:
        """Execute the full incident triage pipeline."""
        results = {}

        # Step 1: Detect anomalies
        print("Step 1/4: Running anomaly detection...")
        results["anomaly"] = self._run_agent(
            "detector",
            f"Analyze this telemetry data for anomalies:\n\n{telemetry_data}",
        )

        # Step 2: Diagnose root cause
        print("Step 2/4: Diagnosing root cause...")
        results["diagnosis"] = self._run_agent(
            "diagnostician",
            f"Diagnose the root cause of these anomalies:\n\n"
            f"Anomaly Assessment:\n{results['anomaly']}\n\n"
            f"Raw Telemetry:\n{telemetry_data}",
        )

        # Step 3: Recommend remediation
        print("Step 3/4: Generating remediation plan...")
        results["remediation"] = self._run_agent(
            "remediator",
            f"Suggest remediation for this diagnosis:\n\n"
            f"Diagnosis:\n{results['diagnosis']}\n\n"
            f"Anomaly:\n{results['anomaly']}",
        )

        # Step 4: Generate incident report
        print("Step 4/4: Generating incident report...")
        results["report"] = self._run_agent(
            "reporter",
            f"Create an incident report from these findings:\n\n"
            f"Anomaly Assessment:\n{results['anomaly']}\n\n"
            f"Diagnosis:\n{results['diagnosis']}\n\n"
            f"Remediation Plan:\n{results['remediation']}",
        )

        return results

    def cleanup(self):
        """Delete all created agents."""
        for key, agent_id in self._agent_ids.items():
            self.client.agents.delete(agent_id)
            print(f"  Deleted agent '{key}' ({agent_id})")
        self._agent_ids.clear()


def main():
    """Run the multi-agent triage scenario with sample data."""
    credential = DefaultAzureCredential()
    client = FoundryClient(
        endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
        credential=credential,
    )

    sample_telemetry = """
    [2026-07-08T12:00:00Z] container=conversations RU/s=2450 (limit=400) latency_p99=3200ms
    [2026-07-08T12:01:00Z] container=conversations RU/s=3100 (limit=400) latency_p99=4500ms
    [2026-07-08T12:02:00Z] container=conversations RU/s=4200 (limit=400) latency_p99=8900ms
    [2026-07-08T12:03:00Z] container=conversations errors=429 (TooManyRequests) count=147
    [2026-07-08T12:04:00Z] container=conversations errors=429 (TooManyRequests) count=312
    """

    orchestrator = MultiAgentOrchestrator(client)

    try:
        print("Setting up agents...")
        orchestrator.setup()

        print("\nRunning incident triage...\n")
        results = orchestrator.run_triage(sample_telemetry)

        print("\n" + "=" * 60)
        print("INCIDENT REPORT")
        print("=" * 60)
        print(results["report"])

    finally:
        print("\nCleaning up agents...")
        orchestrator.cleanup()


if __name__ == "__main__":
    main()
