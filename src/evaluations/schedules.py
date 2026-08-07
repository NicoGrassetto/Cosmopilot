import argparse
import logging
import os

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import Schedule, ScheduleRun, ScheduleTaskType
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)

def create_or_update(schedule_id: str, schedule: Schedule) -> Schedule:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return client.beta.schedules.create_or_update(
            schedule_id=schedule_id,
            schedule=schedule,
        )

def get(schedule_id: str) -> Schedule:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return client.beta.schedules.get(schedule_id=schedule_id)

def list_schedules(
    *,
    enabled: bool | None = None,
    schedule_type: str | ScheduleTaskType | None = None,
) -> list[Schedule]:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return [
            schedule
            for schedule in client.beta.schedules.list(
                enabled=enabled,
                type=schedule_type,
            )
        ]

def delete(schedule_id: str) -> None:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return client.beta.schedules.delete(schedule_id=schedule_id)

def get_run(schedule_id: str, run_id: str) -> ScheduleRun:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return client.beta.schedules.get_run(
            schedule_id=schedule_id,
            run_id=run_id,
        )

def list_runs(
    schedule_id: str,
    *,
    enabled: bool | None = None,
    schedule_type: str | ScheduleTaskType | None = None,
) -> list[ScheduleRun]:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return [
            run
            for run in client.beta.schedules.list_runs(
                schedule_id=schedule_id,
                enabled=enabled,
                type=schedule_type,
            )
        ]

def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)

    get_command = commands.add_parser("get")
    get_command.add_argument("-s", "--schedule-id", required=True)

    list_schedules_command = commands.add_parser("list-schedules")
    list_schedules_command.add_argument(
        "--enabled",
        action=argparse.BooleanOptionalAction,
        default=None,
    )
    list_schedules_command.add_argument("-t", "--type", dest="schedule_type")

    delete_command = commands.add_parser("delete")
    delete_command.add_argument("-s", "--schedule-id", required=True)

    get_run_command = commands.add_parser("get-run")
    get_run_command.add_argument("-s", "--schedule-id", required=True)
    get_run_command.add_argument("-r", "--run-id", required=True)

    list_runs_command = commands.add_parser("list-runs")
    list_runs_command.add_argument("-s", "--schedule-id", required=True)
    list_runs_command.add_argument(
        "--enabled",
        action=argparse.BooleanOptionalAction,
        default=None,
    )
    list_runs_command.add_argument("-t", "--type", dest="schedule_type")

    args = parser.parse_args()

    try:
        if args.command == "get":
            print(get(schedule_id=args.schedule_id))

        elif args.command == "list-schedules":
            for schedule in list_schedules(
                enabled=args.enabled,
                schedule_type=args.schedule_type,
            ):
                print(schedule)

        elif args.command == "delete":
            print(delete(schedule_id=args.schedule_id))

        elif args.command == "get-run":
            print(
                get_run(
                    schedule_id=args.schedule_id,
                    run_id=args.run_id,
                )
            )

        elif args.command == "list-runs":
            for run in list_runs(
                schedule_id=args.schedule_id,
                enabled=args.enabled,
                schedule_type=args.schedule_type,
            ):
                print(run)
        else:
            raise ValueError(f"Unsupported schedule command: {args.command}")
    except Exception:
        logger.exception("Schedule command failed command=%s", args.command)
        raise SystemExit(1)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    )
    main()
