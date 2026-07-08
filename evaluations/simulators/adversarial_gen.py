"""
Adversarial data generator using azure.ai.evaluation.simulator.AdversarialSimulator.

Generates attack prompts (jailbreaks, injections, harmful content probes)
to stress-test agent safety.
"""

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from azure.identity import DefaultAzureCredential
from azure.ai.evaluation.simulator import AdversarialSimulator, AdversarialScenario


@dataclass
class AdversarialScenarioSet:
    """Pre-defined sets of adversarial scenarios for common testing needs."""

    ALL: list = field(default_factory=lambda: [
        AdversarialScenario.ADVERSARIAL_QA,
        AdversarialScenario.ADVERSARIAL_CONVERSATION,
        AdversarialScenario.ADVERSARIAL_SUMMARIZATION,
        AdversarialScenario.ADVERSARIAL_REWRITE,
        AdversarialScenario.ADVERSARIAL_CONTENT_GEN_UNGROUNDED,
        AdversarialScenario.ADVERSARIAL_CONTENT_GEN_GROUNDED,
    ])

    JAILBREAK: list = field(default_factory=lambda: [
        AdversarialScenario.ADVERSARIAL_QA,
        AdversarialScenario.ADVERSARIAL_CONVERSATION,
    ])

    CONTENT_SAFETY: list = field(default_factory=lambda: [
        AdversarialScenario.ADVERSARIAL_CONTENT_GEN_UNGROUNDED,
        AdversarialScenario.ADVERSARIAL_CONTENT_GEN_GROUNDED,
    ])


async def _run_adversarial(
    azure_ai_project,
    target: Callable,
    scenario: AdversarialScenario,
    max_turns: int,
    max_simulations: int,
) -> list:
    simulator = AdversarialSimulator(
        azure_ai_project=azure_ai_project,
        credential=DefaultAzureCredential(),
    )
    outputs = await simulator(
        scenario=scenario,
        max_conversation_turns=max_turns,
        max_simulation_results=max_simulations,
        target=target,
    )
    return outputs


def generate_adversarial_data(
    azure_ai_project,
    target: Callable,
    scenarios: list[AdversarialScenario] | None = None,
    max_turns: int = 1,
    max_simulations: int = 5,
    output_path: str | Path | None = None,
) -> list[dict]:
    """Generate adversarial test data for safety evaluation.

    Args:
        azure_ai_project: Foundry project config (dict or URL string).
        target: Async callback function that wraps your agent.
        scenarios: List of AdversarialScenario enums to run.
        max_turns: Max conversation turns per simulation.
        max_simulations: Number of simulations per scenario.
        output_path: Optional path to save results as JSONL.

    Returns:
        Combined list of adversarial conversation outputs.
    """
    if scenarios is None:
        scenarios = AdversarialScenarioSet().ALL

    all_outputs = []
    for scenario in scenarios:
        outputs = asyncio.run(
            _run_adversarial(azure_ai_project, target, scenario, max_turns, max_simulations)
        )
        all_outputs.extend(outputs)

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            for output in all_outputs:
                f.write(output.to_eval_qr_json_lines())

    return all_outputs
