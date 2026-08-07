import argparse
import logging
import os

from azure.core.exceptions import ResourceNotFoundError
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import (
    DispatchRoutineResult,
    Routine,
    RoutineAction,
    RoutineDispatchPayload,
    RoutineRun,
    RoutineTrigger,
)

logger = logging.getLogger(__name__)

def create(
    routine_name: str,
    description: str,
    enabled: bool,
    triggers: dict[str, RoutineTrigger],
    action: RoutineAction,
) -> Routine:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return client.beta.routines.create_or_update(
            routine_name=routine_name,
            description=description,
            enabled=enabled,
            triggers=triggers,
            action=action,
        )

def update(
    routine_name: str,
    description: str,
    enabled: bool,
    triggers: dict[str, RoutineTrigger],
    action: RoutineAction,
) -> Routine:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        try:
            client.beta.routines.get(routine_name=routine_name)

            return client.beta.routines.create_or_update(
                routine_name=routine_name,
                description=description,
                enabled=enabled,
                triggers=triggers,
                action=action,
            )
        except ResourceNotFoundError:
            raise ValueError(f"Routine '{routine_name}' does not exist") from None

def get(routine_name: str) -> Routine:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return client.beta.routines.get(routine_name=routine_name)

def list_routines(
    *,
    limit: int | None = None,
    order: str | None = None,
    before: str | None = None,
) -> list[Routine]:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return [
            routine
            for routine in client.beta.routines.list(
                limit=limit,
                order=order,
                before=before,
            )
        ]

def delete(routine_name: str) -> None:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return client.beta.routines.delete(routine_name=routine_name)

def disable(routine_name: str) -> Routine:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return client.beta.routines.disable(routine_name=routine_name)

def enable(routine_name: str) -> Routine:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return client.beta.routines.enable(routine_name=routine_name)

def dispatch(
    routine_name: str,
    *,
    payload: RoutineDispatchPayload | None = None,
) -> DispatchRoutineResult:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return client.beta.routines.dispatch(
            routine_name=routine_name,
            payload=payload,
        )

def list_runs(
    routine_name: str,
    *,
    limit: int | None = None,
    order: str | None = None,
    before: str | None = None,
    filter: str | None = None,
) -> list[RoutineRun]:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return [
            run
            for run in client.beta.routines.list_runs(
                routine_name=routine_name,
                limit=limit,
                order=order,
                before=before,
                filter=filter,
            )
        ]

def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("get").add_argument(
        "-n", "--routine-name", required=True
    )
    list_routines_command = commands.add_parser("list-routines")
    list_routines_command.add_argument("--limit", type=int)
    list_routines_command.add_argument("--order", choices=("asc", "desc"))
    list_routines_command.add_argument("--before")
    commands.add_parser("delete").add_argument(
        "-n", "--routine-name", required=True
    )
    commands.add_parser("disable").add_argument(
        "-n", "--routine-name", required=True
    )
    commands.add_parser("enable").add_argument(
        "-n", "--routine-name", required=True
    )
    commands.add_parser("dispatch").add_argument(
        "-n", "--routine-name", required=True
    )
    list_runs_command = commands.add_parser("list-runs")
    list_runs_command.add_argument(
        "-n", "--routine-name", required=True
    )
    list_runs_command.add_argument("--limit", type=int)
    list_runs_command.add_argument("--order", choices=("asc", "desc"))
    list_runs_command.add_argument("--before")
    list_runs_command.add_argument("--filter")

    args = parser.parse_args()

    try:
        if args.command == "get":
            print(get(routine_name=args.routine_name))

        elif args.command == "list-routines":
            for routine in list_routines(
                limit=args.limit,
                order=args.order,
                before=args.before,
            ):
                print(routine)

        elif args.command == "delete":
            print(delete(routine_name=args.routine_name))

        elif args.command == "disable":
            print(disable(routine_name=args.routine_name))

        elif args.command == "enable":
            print(enable(routine_name=args.routine_name))

        elif args.command == "dispatch":
            print(dispatch(routine_name=args.routine_name))

        elif args.command == "list-runs":
            for run in list_runs(
                routine_name=args.routine_name,
                limit=args.limit,
                order=args.order,
                before=args.before,
                filter=args.filter,
            ):
                print(run)
        else:
            raise ValueError(f"Unsupported routine command: {args.command}")
    except Exception:
        logger.exception("Routine command failed command=%s", args.command)
        raise SystemExit(1)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    )
    main()
