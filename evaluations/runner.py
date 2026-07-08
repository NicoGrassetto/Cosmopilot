"""
Evaluation runner — CLI entrypoint.

Usage:
    python runner.py --agent adventure-works --suites quality,safety,agentic
    python runner.py --agent adventure-works --suites all
    python runner.py --agent adventure-works --suites nlp --dataset datasets/per_agent/adventure-works.jsonl
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import yaml
from azure.ai.evaluation import evaluate

from agents import FoundryAgentTarget
from evals import quality_suite, safety_suite, agentic_suite, nlp_suite, grader_suite


def load_config():
    """Load model and project configuration from YAML files."""
    config_dir = Path(__file__).parent / "config"

    with open(config_dir / "model_config.yaml") as f:
        raw = f.read()
    # Resolve environment variables in YAML
    for key, val in os.environ.items():
        raw = raw.replace(f"${{{key}}}", val)
    model_cfg = yaml.safe_load(raw)

    with open(config_dir / "project_config.yaml") as f:
        raw = f.read()
    for key, val in os.environ.items():
        raw = raw.replace(f"${{{key}}}", val)
    project_cfg = yaml.safe_load(raw)

    return model_cfg, project_cfg


def build_evaluators(suite_names: list[str], model_config: dict, azure_ai_project: dict) -> dict:
    """Compose evaluator dict from requested suite names."""
    suite_map = {
        "quality": lambda: quality_suite(model_config),
        "safety": lambda: safety_suite(azure_ai_project),
        "agentic": lambda: agentic_suite(model_config),
        "nlp": lambda: nlp_suite(),
        "graders": lambda: grader_suite(model_config),
    }

    evaluators = {}
    for name in suite_names:
        if name == "all":
            for builder in suite_map.values():
                evaluators.update(builder())
            break
        if name not in suite_map:
            print(f"Warning: Unknown suite '{name}', skipping. Available: {list(suite_map.keys())}")
            continue
        evaluators.update(suite_map[name]())

    return evaluators


def run_evaluation(agent_name: str, suite_names: list[str], dataset: str | None = None):
    """Run evaluation for a given agent and suite combination."""
    model_cfg, project_cfg = load_config()
    model_config = model_cfg["judge_model"]
    azure_ai_project = project_cfg["azure_ai_project"]

    # Build evaluators
    evaluators = build_evaluators(suite_names, model_config, azure_ai_project)
    if not evaluators:
        print("Error: No evaluators selected.")
        sys.exit(1)

    print(f"Agent: {agent_name}")
    print(f"Suites: {', '.join(suite_names)}")
    print(f"Evaluators: {', '.join(evaluators.keys())}")
    print("=" * 60)

    # Determine output path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(__file__).parent / "results" / f"{agent_name}_{timestamp}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Run with dataset only (no live target) or with live target
    eval_kwargs = {
        "evaluators": evaluators,
        "azure_ai_project": azure_ai_project,
        "output_path": str(output_path),
    }

    if dataset:
        eval_kwargs["data"] = dataset
    else:
        # Use live agent as target
        target = FoundryAgentTarget(agent_name=agent_name)
        eval_kwargs["target"] = target
        # Need a dataset even with target for the queries
        default_dataset = Path(__file__).parent / "datasets" / "per_agent" / f"{agent_name}.jsonl"
        if default_dataset.exists():
            eval_kwargs["data"] = str(default_dataset)
        else:
            print(f"Error: No dataset found at {default_dataset}. Provide --dataset or create the file.")
            sys.exit(1)

    result = evaluate(**eval_kwargs)

    print(f"\nResults saved to: {output_path}")
    print(f"\nMetric summary:")
    print(json.dumps(result.get("metrics", result), indent=2, default=str))

    return result


def main():
    parser = argparse.ArgumentParser(description="Run evaluations against a Foundry agent.")
    parser.add_argument("--agent", required=True, help="Agent name (as deployed in Foundry)")
    parser.add_argument(
        "--suites",
        required=True,
        help="Comma-separated suite names: quality,safety,agentic,nlp,graders,all",
    )
    parser.add_argument("--dataset", help="Path to JSONL dataset (overrides default per-agent dataset)")
    args = parser.parse_args()

    suite_names = [s.strip() for s in args.suites.split(",")]
    run_evaluation(args.agent, suite_names, args.dataset)


if __name__ == "__main__":
    main()
