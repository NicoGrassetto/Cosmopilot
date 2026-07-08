"""
Synthetic conversation generator using azure.ai.evaluation.simulator.Simulator.

Generates multi-turn conversations from seed topics that can be fed directly
into the evaluate() API.
"""

import asyncio
import json
from pathlib import Path
from typing import Callable

from azure.ai.evaluation.simulator import Simulator


async def _run_simulator(
    model_config: dict,
    target: Callable,
    conversation_starters: list[list[str]],
    max_turns: int,
) -> list:
    simulator = Simulator(model_config=model_config)
    outputs = await simulator(
        target=target,
        conversation_turns=conversation_starters,
        max_conversation_turns=max_turns,
    )
    return outputs


def generate_synthetic_conversations(
    model_config: dict,
    target: Callable,
    conversation_starters: list[list[str]],
    max_turns: int = 3,
    output_path: str | Path | None = None,
) -> list[dict]:
    """Generate synthetic multi-turn conversations.

    Args:
        model_config: Azure OpenAI config for the simulator's LLM.
        target: Async callback function that wraps your agent.
        conversation_starters: List of conversation seed messages.
        max_turns: Maximum conversation turns per starter.
        output_path: Optional path to save results as JSONL.

    Returns:
        List of conversation dicts ready for evaluate().
    """
    outputs = asyncio.run(
        _run_simulator(model_config, target, conversation_starters, max_turns)
    )

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            for output in outputs:
                f.write(output.to_eval_qr_json_lines())

    return outputs
