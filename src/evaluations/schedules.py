import argparse
import os

from azure.core.exceptions import ResourceNotFoundError
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)

    # commands.add_parser("create")
    # commands.add_parser("update").add_argument("routine_name")
    commands.add_parser("get").add_argument("schedule_id")
    commands.add_parser("list")
    commands.add_parser("delete").add_argument("schedule_id")
    commands.add_parser("get-run").add_argument("schedule_id")
    commands.add_parser("get-run").add_argument("run_id")
    commands.add_parser("list-runs").add_argument("schedule_id")

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
        client.beta.schedules.get(schedule_id=args.schedule_id)

    elif args.command == "list":
        for schedule in client.beta.schedules.list():
            print(schedule)

    elif args.command == "delete":
        client.beta.schedules.delete(schedule_id=args.schedule_id)

    elif args.command == "get-run":
        print(
            client.beta.schedules.get_run(
                schedule_id=args.schedule_id,
                run_id=args.run_id,
            )
        )

    elif args.command == "list-runs":
        for run in client.beta.schedules.list_runs(
            schedule_id=args.schedule_id,
        ):
            print(run)

if __name__ == "__main__":
    main()
