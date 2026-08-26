from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import RedTeam
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)


def create(red_team: RedTeam, **kwargs: Any) -> RedTeam:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return client.beta.red_teams.create(red_team=red_team, **kwargs)


def get(name: str, **kwargs: Any) -> RedTeam:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return client.beta.red_teams.get(name=name, **kwargs)


def list_red_teams(**kwargs: Any) -> list[RedTeam]:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return list(client.beta.red_teams.list(**kwargs))


def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)

    create_command = commands.add_parser("create")
    create_command.add_argument(
        "-f", "--definition", type=Path, required=True
    )

    get_command = commands.add_parser("get")
    get_command.add_argument("-n", "--name", required=True)

    commands.add_parser("list-red-teams")

    args = parser.parse_args()

    try:
        if args.command == "create":
            definition = json.loads(
                args.definition.read_text(encoding="utf-8")
            )
            result = create(red_team=RedTeam(definition))
            output = result.as_dict()

        elif args.command == "get":
            result = get(name=args.name)
            output = result.as_dict()

        elif args.command == "list-red-teams":
            output = [red_team.as_dict() for red_team in list_red_teams()]

        else:
            raise AssertionError(
                f"Unsupported red-team command: {args.command}"
            )
    except Exception:
        logger.exception(
            "Red-team command failed command=%s",
            args.command,
        )
        raise SystemExit(1)

    print(json.dumps(output, indent=2, default=str))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    )
    main()