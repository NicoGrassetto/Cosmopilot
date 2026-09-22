import os
from uuid import uuid4

import pytest
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    CreateSkillVersionFromFilesBody,
    SkillInlineContent,
)
from azure.identity import DefaultAzureCredential


@pytest.mark.integration
def test_create():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        skill_name = f"pytest-skill-{uuid4().hex[:8]}"

        try:
            created_skill = client.beta.skills.create(
                name=skill_name,
                inline_content=SkillInlineContent(
                    description="Temporary skill created by pytest.",
                    instructions="Answer the question and stop.",
                ),
                default=True,
            )

            assert created_skill is not None
        finally:
            client.beta.skills.delete(name=skill_name)


@pytest.mark.integration
def test_create_from_files():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        skill_name = f"pytest-skill-{uuid4().hex[:8]}"

        try:
            created_skill = client.beta.skills.create_from_files(
                name=skill_name,
                content=CreateSkillVersionFromFilesBody(
                    files=[
                        (
                            "SKILL.md",
                            b"---\n"
                            b"name: pytest-skill\n"
                            b"description: Temporary skill created by pytest.\n"
                            b"---\n"
                            b"\n"
                            b"Answer the question and stop.\n",
                        )
                    ],
                    default=True,
                ),
            )

            assert created_skill is not None
        finally:
            client.beta.skills.delete(name=skill_name)


@pytest.mark.integration
def test_delete():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        skill_name = f"pytest-skill-{uuid4().hex[:8]}"
        client.beta.skills.create(
            name=skill_name,
            inline_content=SkillInlineContent(
                description="Temporary skill created by pytest.",
                instructions="Answer the question and stop.",
            ),
            default=True,
        )

        deleted_skill = client.beta.skills.delete(name=skill_name)

        assert deleted_skill is not None


@pytest.mark.integration
def test_delete_version():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        skill_name = f"pytest-skill-{uuid4().hex[:8]}"
        client.beta.skills.create(
            name=skill_name,
            inline_content=SkillInlineContent(
                description="Temporary skill created by pytest.",
                instructions="Answer the question and stop.",
            ),
            default=True,
        )
        second_skill_version = client.beta.skills.create(
            name=skill_name,
            inline_content=SkillInlineContent(
                description="Temporary skill created by pytest.",
                instructions="Answer the question, then stop.",
            ),
            default=False,
        )

        try:
            deleted_skill_version = client.beta.skills.delete_version(
                name=skill_name,
                version=second_skill_version.version,
            )

            assert deleted_skill_version is not None
        finally:
            client.beta.skills.delete(name=skill_name)


@pytest.mark.integration
def test_download():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        skill_name = f"pytest-skill-{uuid4().hex[:8]}"
        client.beta.skills.create(
            name=skill_name,
            inline_content=SkillInlineContent(
                description="Temporary skill created by pytest.",
                instructions="Answer the question and stop.",
            ),
            default=True,
        )

        try:
            downloaded_skill = b"".join(client.beta.skills.download(name=skill_name))

            assert downloaded_skill is not None
        finally:
            client.beta.skills.delete(name=skill_name)


@pytest.mark.integration
def test_download_version():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        skill_name = f"pytest-skill-{uuid4().hex[:8]}"
        created_skill = client.beta.skills.create(
            name=skill_name,
            inline_content=SkillInlineContent(
                description="Temporary skill created by pytest.",
                instructions="Answer the question and stop.",
            ),
            default=True,
        )

        try:
            downloaded_skill_version = b"".join(
                client.beta.skills.download_version(
                    name=skill_name,
                    version=created_skill.version,
                )
            )

            assert downloaded_skill_version is not None
        finally:
            client.beta.skills.delete(name=skill_name)


@pytest.mark.integration
def test_get():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        skill_name = f"pytest-skill-{uuid4().hex[:8]}"
        client.beta.skills.create(
            name=skill_name,
            inline_content=SkillInlineContent(
                description="Temporary skill created by pytest.",
                instructions="Answer the question and stop.",
            ),
            default=True,
        )

        try:
            retrieved_skill = client.beta.skills.get(name=skill_name)

            assert retrieved_skill is not None
        finally:
            client.beta.skills.delete(name=skill_name)


@pytest.mark.integration
def test_get_version():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        skill_name = f"pytest-skill-{uuid4().hex[:8]}"
        created_skill = client.beta.skills.create(
            name=skill_name,
            inline_content=SkillInlineContent(
                description="Temporary skill created by pytest.",
                instructions="Answer the question and stop.",
            ),
            default=True,
        )

        try:
            retrieved_skill_version = client.beta.skills.get_version(
                name=skill_name,
                version=created_skill.version,
            )

            assert retrieved_skill_version is not None
        finally:
            client.beta.skills.delete(name=skill_name)


@pytest.mark.integration
def test_list():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        listed_skills = list(client.beta.skills.list())

        assert isinstance(listed_skills, list)


@pytest.mark.integration
def test_list_versions():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        skill_name = f"pytest-skill-{uuid4().hex[:8]}"
        client.beta.skills.create(
            name=skill_name,
            inline_content=SkillInlineContent(
                description="Temporary skill created by pytest.",
                instructions="Answer the question and stop.",
            ),
            default=True,
        )

        try:
            skill_versions = list(client.beta.skills.list_versions(name=skill_name))

            assert isinstance(skill_versions, list)
        finally:
            client.beta.skills.delete(name=skill_name)


@pytest.mark.integration
def test_update():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        skill_name = f"pytest-skill-{uuid4().hex[:8]}"
        created_skill = client.beta.skills.create(
            name=skill_name,
            inline_content=SkillInlineContent(
                description="Temporary skill created by pytest.",
                instructions="Answer the question and stop.",
            ),
            default=True,
        )

        try:
            updated_skill = client.beta.skills.update(
                name=skill_name,
                default_version=created_skill.version,
            )

            assert updated_skill is not None
        finally:
            client.beta.skills.delete(name=skill_name)
