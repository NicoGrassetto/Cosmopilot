from uuid import uuid4

import pytest

import skills

#Note: I intentioanlly decided to omit the repow-wide skills registration

@pytest.mark.integration
def test_create_skill(request):
    skill_name = f"pytest-skill-{uuid4().hex[:8]}"

    created_skill = skills.create(
        name=skill_name,
        description="Temporary skill created by pytest.",
        instructions="Respond with a concise answer.",
    )
    request.addfinalizer(lambda: skills.delete(name=skill_name))

    assert created_skill is not None

@pytest.mark.integration
def test_get_skill(request):
    skill_name = f"pytest-skill-{uuid4().hex[:8]}"

    skills.create(
        name=skill_name,
        description="Temporary skill created by pytest.",
        instructions="Respond with a concise answer.",
    )
    request.addfinalizer(lambda: skills.delete(name=skill_name))

    retrieved_skill = skills.get(name=skill_name)

    assert retrieved_skill is not None

@pytest.mark.integration
def test_list_skills():
    listed_skills = skills.list_skills()
    #just checking here if the SDK/API works.. 
    assert isinstance(listed_skills, list)

@pytest.mark.integration
def test_list_versions(request):
    skill_name = f"pytest-skill-{uuid4().hex[:8]}"

    skills.create(
        name=skill_name,
        description="Temporary skill created by pytest.",
        instructions="Respond with a concise answer.",
    )
    request.addfinalizer(lambda: skills.delete(name=skill_name))

    versions = skills.list_versions(name=skill_name)

    assert versions

@pytest.mark.integration
def test_update_skill(request):
    skill_name = f"pytest-skill-{uuid4().hex[:8]}"

    created_skill = skills.create(
        name=skill_name,
        description="Temporary skill created by pytest.",
        instructions="Respond with a concise answer.",
    )
    request.addfinalizer(lambda: skills.delete(name=skill_name))

    updated_skill = skills.update(
        name=skill_name,
        version=created_skill.version,
    )

    assert updated_skill is not None

@pytest.mark.integration
def test_delete_skill():
    skill_name = f"pytest-skill-{uuid4().hex[:8]}"

    skills.create(
        name=skill_name,
        description="Temporary skill created by pytest.",
        instructions="Respond with a concise answer.",
    )

    deleted_skill = skills.delete(name=skill_name)

    assert deleted_skill is not None

@pytest.mark.integration
def test_download_skill(request, tmp_path):
    skill_name = f"pytest-skill-{uuid4().hex[:8]}"

    skills.create(
        name=skill_name,
        description="Temporary skill created by pytest.",
        instructions="Respond with a concise answer.",
    )
    request.addfinalizer(lambda: skills.delete(name=skill_name))

    downloaded_path = skills.download(
        name=skill_name,
        output_path=tmp_path / "downloaded-skill.zip",
    )

    assert downloaded_path.is_file()

@pytest.mark.integration
def test_create_skill_from_files(request, tmp_path):
    skill_name = f"pytest-skill-{uuid4().hex[:8]}"
    skill_directory = tmp_path / skill_name
    skill_directory.mkdir()

    (skill_directory / "SKILL.md").write_text(
        f"""---
name: {skill_name}
description: Temporary skill created by pytest
---

# Instructions

Respond with a concise answer.
""",
        encoding="utf-8",
    )

    created_skill = skills.create_from_files(
        name=skill_name,
        skill_directory=skill_directory,
    )
    request.addfinalizer(lambda: skills.delete(name=skill_name))

    assert created_skill is not None