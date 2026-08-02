import argparse
import os

from azure.core.exceptions import ResourceNotFoundError
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import RoutineAction
from azure.ai.projects.models import (
    InvokeAgentResponsesApiRoutineAction,
    ScheduleRoutineTrigger,
)

def create(routine_name: str, description: str, enabled: bool, triggers: dict, action: RoutineAction):
    client = AIProjectClient(
        endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
        credential=DefaultAzureCredential(),
        allow_preview=True,
    )

    client.beta.routines.create_or_update(
        routine_name=routine_name,
        description=description,
        enabled=enabled,
        triggers=triggers,
        action=action
    )
def update(routine_name: str, description: str, enabled: bool,triggers: dict, action: RoutineAction):
    client = AIProjectClient(
        endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
        credential=DefaultAzureCredential(),
        allow_preview=True,
    )

    try:
        client.beta.routines.get(routine_name=routine_name)

        client.beta.routines.create_or_update(
            routine_name=routine_name,
            description=description,
            enabled=enabled,
            triggers=triggers,
            action=action,
        )
    except ResourceNotFoundError:
        raise ValueError(f"Routine '{routine_name}' does not exist") from None

def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)

    # commands.add_parser("create")
    # commands.add_parser("update").add_argument("routine_name")
    commands.add_parser("get").add_argument("routine_name")
    commands.add_parser("list")
    commands.add_parser("delete").add_argument("routine_name")
    commands.add_parser("disable").add_argument("routine_name")
    commands.add_parser("enable").add_argument("routine_name")
    commands.add_parser("dispatch").add_argument("routine_name")
    commands.add_parser("list-runs").add_argument("routine_name")

    args = parser.parse_args()

    client = AIProjectClient(
        endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
        credential=DefaultAzureCredential(),
        allow_preview=True,
    )

    # if args.command == "create":
    #     create()

    # elif args.command == "update":
    #     update()

    if args.command == "get":
        client.beta.routines.get(routine_name=args.routine_name)

    elif args.command == "list":
        for routine in client.beta.routines.list():
            print(routine)

    elif args.command == "delete":
        client.beta.routines.delete(routine_name=args.routine_name)

    elif args.command == "disable":
        client.beta.routines.disable(routine_name=args.routine_name)

    elif args.command == "enable":
        client.beta.routines.enable(routine_name=args.routine_name)

    elif args.command == "dispatch":
        print(client.beta.routines.dispatch(routine_name=args.routine_name))

    elif args.command == "list-runs":
        for run in client.beta.routines.list_runs(routine_name=args.routine_name):
            print(run)

if __name__ == "__main__":
    main()
