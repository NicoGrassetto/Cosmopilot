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

    commands.add_parser("register-all")

    create_command = commands.add_parser("create")
    create_command.add_argument("-n", "--name", required=True)
    create_command.add_argument("-d", "--description", required=True)
    create_command.add_argument("-i", "--instructions", required=True)

    get_command = commands.add_parser("get")
    get_command.add_argument("-n", "--name", required=True)
    get_command.add_argument("-v", "--version")

    list_skills_command = commands.add_parser("list-skills")
    list_skills_command.add_argument("--limit", type=int)
    list_skills_command.add_argument("--order", choices=("asc", "desc"))
    list_skills_command.add_argument("--before")

    list_versions_command = commands.add_parser("list-versions")
    list_versions_command.add_argument("-n", "--name", required=True)
    list_versions_command.add_argument("--limit", type=int)
    list_versions_command.add_argument("--order", choices=("asc", "desc"))
    list_versions_command.add_argument("--before")

    update_command = commands.add_parser("update")
    update_command.add_argument("-n", "--name", required=True)
    update_command.add_argument("-v", "--version", required=True)

    delete_command = commands.add_parser("delete")
    delete_command.add_argument("-n", "--name", required=True)
    delete_command.add_argument("-v", "--version")

    download_command = commands.add_parser("download")
    download_command.add_argument("-n", "--name", required=True)
    download_command.add_argument("-o", "--output-path", type=Path, required=True)
    download_command.add_argument("-v", "--version")

    create_files_command = commands.add_parser("create-from-files")
    create_files_command.add_argument("-n", "--name", required=True)
    create_files_command.add_argument(
        "-s", "--skill-directory", type=Path, required=True
    )
    create_files_command.add_argument(
        "--make-default",
        action=argparse.BooleanOptionalAction,
        default=True,
    )

    args = parser.parse_args()

    try:
        if args.command == "register-all":
            for version in register_all():
                print(version)

        elif args.command == "create":
            print(create(args.name, args.description, args.instructions))

        elif args.command == "get":
            print(get(args.name, version=args.version))

        elif args.command == "list-skills":
            for skill in list_skills(
                limit=args.limit,
                order=args.order,
                before=args.before,
            ):
                print(skill)

        elif args.command == "list-versions":
            for version in list_versions(
                args.name,
                limit=args.limit,
                order=args.order,
                before=args.before,
            ):
                print(version)

        elif args.command == "update":
            print(update(args.name, args.version))

        elif args.command == "delete":
            print(delete(args.name, version=args.version))

        elif args.command == "download":
            print(download(args.name, args.output_path, version=args.version))

        elif args.command == "create-from-files":
            print(
                create_from_files(
                    args.name,
                    args.skill_directory,
                    make_default=args.make_default,
                )
            )
        else:
            raise ValueError(f"Unsupported skill command: {args.command}")
    except Exception:
        logger.exception("Skill command failed command=%s", args.command)
        raise SystemExit(1)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    )
    main()