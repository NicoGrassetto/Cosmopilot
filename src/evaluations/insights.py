from __future__ import annotations

import argparse
import json
import logging
import os
from collections.abc import MutableMapping
from pathlib import Path
from typing import IO, Any

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import Insight, InsightType
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)


def generate_insight(
	insight: Insight | MutableMapping[str, Any] | IO[bytes],
) -> Insight:
	with (
		DefaultAzureCredential() as credential,
		AIProjectClient(
			endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
			credential=credential,
		) as client,
	):
		return client.beta.insights.generate(insight=insight)


def get_insight(
	insight_id: str,
	*,
	include_coordinates: bool | None = None,
) -> Insight:
	with (
		DefaultAzureCredential() as credential,
		AIProjectClient(
			endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
			credential=credential,
		) as client,
	):
		return client.beta.insights.get(
			insight_id=insight_id,
			include_coordinates=include_coordinates,
		)


def list_insights(
	*,
	insight_type: str | InsightType | None = None,
	eval_id: str | None = None,
	run_id: str | None = None,
	agent_name: str | None = None,
	include_coordinates: bool | None = None,
) -> list[Insight]:
	with (
		DefaultAzureCredential() as credential,
		AIProjectClient(
			endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
			credential=credential,
		) as client,
	):
		return list(
			client.beta.insights.list(
				type=insight_type,
				eval_id=eval_id,
				run_id=run_id,
				agent_name=agent_name,
				include_coordinates=include_coordinates,
			)
		)


def main() -> None:
	parser = argparse.ArgumentParser(
		description="Generate and retrieve Microsoft Foundry insight reports.",
	)
	commands = parser.add_subparsers(dest="command", required=True)

	generate_command = commands.add_parser("generate")
	generate_command.add_argument(
		"-i",
		"--insight",
		type=Path,
		required=True,
		help="Path to a serialized Insight JSON object.",
	)

	get_command = commands.add_parser("get")
	get_command.add_argument("--insight-id", required=True)
	get_command.add_argument(
		"--include-coordinates",
		action=argparse.BooleanOptionalAction,
		default=None,
	)

	list_command = commands.add_parser("list")
	list_command.add_argument(
		"--type",
		choices=(
			"EvaluationRunClusterInsight",
			"AgentClusterInsight",
			"EvaluationComparison",
		),
	)
	list_command.add_argument("--eval-id")
	list_command.add_argument("--run-id")
	list_command.add_argument("--agent-name")
	list_command.add_argument(
		"--include-coordinates",
		action=argparse.BooleanOptionalAction,
		default=None,
	)

	args = parser.parse_args()

	try:
		if args.command == "generate":
			insight = json.loads(args.insight.read_text(encoding="utf-8"))
			output = generate_insight(insight).as_dict()

		elif args.command == "get":
			output = get_insight(
				args.insight_id,
				include_coordinates=args.include_coordinates,
			).as_dict()

		elif args.command == "list":
			output = [
				insight.as_dict()
				for insight in list_insights(
					insight_type=args.type,
					eval_id=args.eval_id,
					run_id=args.run_id,
					agent_name=args.agent_name,
					include_coordinates=args.include_coordinates,
				)
			]

		else:
			raise AssertionError(f"Unhandled command: {args.command}")

		print(json.dumps(output, indent=2, default=str))
	except Exception:
		logger.exception("Insight command failed command=%s", args.command)
		raise SystemExit(1)


if __name__ == "__main__":
	logging.basicConfig(
		level=logging.INFO,
		format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
	)
	main()
