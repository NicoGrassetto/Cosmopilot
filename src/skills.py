from __future__ import annotations

import io
import logging
import argparse
import os
import zipfile
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    CreateSkillVersionFromFilesBody,
    DeleteSkillResult,
    DeleteSkillVersionResult,
    SkillDetails,
    SkillInlineContent,
    SkillVersion,
)
from azure.identity import DefaultAzureCredential

from agents.agents_old import Agent

logger = logging.getLogger(__name__)

def register_all() -> list[SkillVersion]:
    versions = []

    for skill_md in sorted(
        (Path(__file__).parent / "agents").glob("*/skills/*/SKILL.md")
    ):
        versions.append(
            create_from_files(
                name=skill_md.parent.name,
                skill_directory=skill_md.parent,
            )
        )

    return versions

def create(name: str, description: str, instructions: str) -> SkillVersion:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return client.beta.skills.create(
            name=name,
            inline_content=SkillInlineContent(
                description=description,
                instructions=instructions,
            ),
        )

def get(name: str, version: str | None = None) -> SkillDetails | SkillVersion:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        if version is not None:
            return client.beta.skills.get_version(name=name, version=version)

        return client.beta.skills.get(name=name)

def list_skills(
    *,
    limit: int | None = None,
    order: str | None = None,
    before: str | None = None,
) -> list[SkillDetails]:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return [
            skill
            for skill in client.beta.skills.list(
                limit=limit,
                order=order,
                before=before,
            )
        ]

def list_versions(
    name: str,
    *,
    limit: int | None = None,
    order: str | None = None,
    before: str | None = None,
) -> list[SkillVersion]:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return [
            version
            for version in client.beta.skills.list_versions(
                name=name,
                limit=limit,
                order=order,
                before=before,
            )
        ]

def update(name:str, version: str):
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return client.beta.skills.update(name=name, default_version=version)

def delete(name: str, version: str | None = None) -> DeleteSkillResult | DeleteSkillVersionResult:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        if version is not None:
            return client.beta.skills.delete_version(
                name=name,
                version=version,
            )

        return client.beta.skills.delete(name=name)
    
def download(
    name: str,
    output_path: str | Path,
    *,
    version: str | None = None,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        if version is not None:
            content = client.beta.skills.download_version(name=name, version=version)
        else:
            content = client.beta.skills.download(name=name)

        output_path.write_bytes(b"".join(content))

    return output_path

def create_from_files(
    name: str,
    skill_directory: str | Path,
    *,
    make_default: bool = True,
) -> SkillVersion:
    skill_directory = Path(skill_directory)

    if not (skill_directory / "SKILL.md").is_file():
        raise FileNotFoundError(
            f"Missing SKILL.md in {skill_directory}"
        )

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for file_path in sorted(skill_directory.rglob("*")):
            if file_path.is_file():
                archive.write(
                    file_path,
                    file_path.relative_to(skill_directory),
                )

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        version = client.beta.skills.create_from_files(
            name=name,
            content=CreateSkillVersionFromFilesBody(
                files=[
                    (
                        f"{name}.zip",
                        buffer.getvalue(),
                        "application/zip",
                    )
                ]
            ),
        )

        if make_default:
            client.beta.skills.update(
                name=name,
                default_version=version.version,
            )

    return version

def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("create").add_argument("name")
    commands.add_parser("create").add_argument("description")
    commands.add_parser("create").add_argument("instructions")

    commands.add_parser("get").add_argument("name")
    commands.add_parser("get").add_argument("version", nargs="?", default=None)

    commands.add_parser("list-skills").add_argument("name")
    commands.add_parser("list-skills").add_argument("name")
#  list_command.add_argument("limit", nargs="?", type=int, default=None)
#     list_command.add_argument("order", nargs="?", default=None)
#     list_command.add_argument("before", nargs="?", default=None)


    args = parser.parse_args()

    if args.command == "create":
        pass
    elif args.command == "get":
        pass
    elif args.command == "list-skills":
        pass

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    )

    parser = argparse.ArgumentParser(description="Manage Microsoft Foundry skills.")
    commands = parser.add_subparsers(dest="command", required=True)
# This is meant to be used by as a command or to be ran at the data plane as a post provision hook -> 


# commands.add_parser("get").add_argument("routine_name")
#     commands.add_parser("list")
#     commands.add_parser("delete").add_argument("routine_name")


#     args = parser.parse_args()

#     client = AIProjectClient(
#         endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
#         credential=DefaultAzureCredential(),
#         allow_preview=True,
#     )

#     if args.command == "get":
#         client.beta.routines.get(routine_name=args.routine_name)

#     elif args.command == "list":
#         for routine in client.beta.routines.list():
#             print(routine)

#     elif args.command == "delete":
#         client.beta.routines.delete(routine_name=args.routine_name)

#     elif args.command == "disable":
#         client.beta.routines.disable(routine_name=args.routine_name)

#     elif args.command == "enable":
#         client.beta.routines.enable(routine_name=args.routine_name)

#     elif args.command == "dispatch":
#         print(client.beta.routines.dispatch(routine_name=args.routine_name))

#     elif args.command == "list-runs":
#         for run in client.beta.routines.list_runs(routine_name=args.routine_name):
#             print(run)



#     parser = argparse.ArgumentParser()
#     parser.add_argument("--allow-preview", action="store_true")
#     commands = parser.add_subparsers(dest="command", required=True)

#     get_command = commands.add_parser("get-agent")
#     get_command.add_argument("-n", "--agent-name", required=True)

#     list_command = commands.add_parser("list-agents")
#     list_command.add_argument("-k", "--kind", choices=("prompt", "hosted", "workflow", "external"),)

#     list_command.add_argument("--limit", type=int)
#     list_command.add_argument("--order", choices=("asc", "desc"))
#     list_command.add_argument("--before")

#     get_version_command = commands.add_parser("get-agent-version")
#     get_version_command.add_argument("-n", "--agent-name", required=True)
#     get_version_command.add_argument("-v", "--agent-version", required=True)

#     list_versions_command = commands.add_parser("list-agent-versions")
#     list_versions_command.add_argument("-n", "--agent-name", required=True)

#     enable_command = commands.add_parser("enable-agent")
#     enable_command.add_argument("-n", "--agent-name", required=True)

#     disable_command = commands.add_parser("disable-agent")
#     disable_command.add_argument("-n", "--agent-name", required=True)

#     delete_command = commands.add_parser("delete-agent")
#     delete_command.add_argument("-n", "--agent-name", required=True)

#     delete_version_command = commands.add_parser("delete-agent-version")
#     delete_version_command.add_argument("-n", "--agent-name", required=True)

#     args = parser.parse_args()