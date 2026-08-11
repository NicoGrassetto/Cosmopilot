import argparse
import json
import logging
from pathlib import Path

from __future__ import annotations

import os

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import EvaluationRule, EvaluationRuleActionType
from azure.identity import DefaultAzureCredential
logger = logging.getLogger(__name__)

def create_or_update(
    rule_id: str,
    evaluation_rule: EvaluationRule,
    *,
    allow_preview: bool = False,
) -> EvaluationRule:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
            allow_preview=allow_preview,
        ) as client,
    ):
        return client.evaluation_rules.create_or_update(
            id=rule_id,
            evaluation_rule=evaluation_rule,
        )


def get(rule_id: str) -> EvaluationRule:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return client.evaluation_rules.get(id=rule_id)


def list_rules(
    *,
    action_type: str | EvaluationRuleActionType | None = None,
    agent_name: str | None = None,
    enabled: bool | None = None,
) -> list[EvaluationRule]:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return list(
            client.evaluation_rules.list(
                action_type=action_type,
                agent_name=agent_name,
                enabled=enabled,
            )
        )


def delete(rule_id: str) -> None:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return client.evaluation_rules.delete(id=rule_id)
    
def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)

    create_command = commands.add_parser("create-or-update")
    create_command.add_argument("-r", "--rule-id", required=True)
    create_command.add_argument(
        "-f", "--definition", type=Path, required=True
    )
    create_command.add_argument(
        "--allow-preview",
        action="store_true",
    )

    get_command = commands.add_parser("get")
    get_command.add_argument("-r", "--rule-id", required=True)

    list_command = commands.add_parser("list-rules")
    list_command.add_argument(
        "--action-type",
        choices=("continuousEvaluation", "humanEvaluationPreview"),
    )
    list_command.add_argument("--agent-name")
    list_command.add_argument(
        "--enabled",
        action=argparse.BooleanOptionalAction,
        default=None,
    )

    delete_command = commands.add_parser("delete")
    delete_command.add_argument("-r", "--rule-id", required=True)

    args = parser.parse_args()

    try:
        if args.command == "create-or-update":
            definition = json.loads(
                args.definition.read_text(encoding="utf-8")
            )
            print(
                create_or_update(
                    rule_id=args.rule_id,
                    evaluation_rule=EvaluationRule(definition),
                    allow_preview=args.allow_preview,
                )
            )

        elif args.command == "get":
            print(get(rule_id=args.rule_id))

        elif args.command == "list-rules":
            for rule in list_rules(
                action_type=args.action_type,
                agent_name=args.agent_name,
                enabled=args.enabled,
            ):
                print(rule)

        elif args.command == "delete":
            print(delete(rule_id=args.rule_id))

        else:
            raise ValueError(
                f"Unsupported evaluation-rule command: {args.command}"
            )
    except Exception:
        logger.exception(
            "Evaluation-rule command failed command=%s",
            args.command,
        )
        raise SystemExit(1)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    )
    main()