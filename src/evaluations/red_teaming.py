from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import RedTeam
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)


def create(red_team: RedTeam) -> RedTeam:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return client.beta.red_teams.create(red_team=red_team)


def get(name: str) -> RedTeam:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return client.beta.red_teams.get(name=name)


def list_red_teams() -> list[RedTeam]:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return list(client.beta.red_teams.list())


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
            print(create(red_team=RedTeam(definition)))

        elif args.command == "get":
            print(get(name=args.name))

        elif args.command == "list-red-teams":
            for red_team in list_red_teams():
                print(red_team)

        else:
            raise ValueError(
                f"Unsupported red-team command: {args.command}"
            )
    except Exception:
        logger.exception(
            "Red-team command failed command=%s",
            args.command,
        )
        raise SystemExit(1)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    )
    main()