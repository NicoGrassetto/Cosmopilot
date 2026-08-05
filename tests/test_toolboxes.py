from uuid import uuid4

import pytest
from azure.ai.projects.models import WebSearchToolboxTool

import toolboxes

@pytest.mark.integration
def test_create_toolbox(request):
	toolbox_name = f"pytest-toolbox-{uuid4().hex[:8]}"

	created_toolbox = toolboxes.create_toolbox(
		name=toolbox_name,
		description="Temporary toolbox created by pytest.",
		tools=[
			WebSearchToolboxTool(
				name="web_search",
				description="Search the public web.",
			)
		],
	)
	request.addfinalizer(lambda: toolboxes.delete_toolbox(name=toolbox_name))

	assert created_toolbox is not None

@pytest.mark.integration
def test_create_toolbox_version_from_definition(request):
	toolbox_name = f"pytest-toolbox-{uuid4().hex[:8]}"
	web_search_tool = WebSearchToolboxTool(
		name="web_search",
		description="Search the public web.",
	)

	created_toolbox = toolboxes.create_toolbox_version_from_definition(
		name=toolbox_name,
		definition={
			"description": "Temporary toolbox created by pytest.",
			"tools": [web_search_tool.as_dict()],
		},
	)
	request.addfinalizer(lambda: toolboxes.delete_toolbox(name=toolbox_name))

	assert created_toolbox is not None

@pytest.mark.integration
def test_get_toolbox(request):
	toolbox_name = f"pytest-toolbox-{uuid4().hex[:8]}"

	toolboxes.create_toolbox(
		name=toolbox_name,
		description="Temporary toolbox created by pytest.",
		tools=[
			WebSearchToolboxTool(
				name="web_search",
				description="Search the public web.",
			)
		],
	)
	request.addfinalizer(lambda: toolboxes.delete_toolbox(name=toolbox_name))

	retrieved_toolbox = toolboxes.get_toolbox(name=toolbox_name)

	assert retrieved_toolbox is not None

@pytest.mark.integration
def test_list_toolboxes():
	listed_toolboxes = toolboxes.list_toolboxes()
	#just checking here if the SDK/API works..
	assert isinstance(listed_toolboxes, list)

@pytest.mark.integration
def test_update_toolbox(request):
	toolbox_name = f"pytest-toolbox-{uuid4().hex[:8]}"

	created_toolbox = toolboxes.create_toolbox(
		name=toolbox_name,
		description="Temporary toolbox created by pytest.",
		tools=[
			WebSearchToolboxTool(
				name="web_search",
				description="Search the public web.",
			)
		],
	)
	request.addfinalizer(lambda: toolboxes.delete_toolbox(name=toolbox_name))

	updated_toolbox = toolboxes.update_toolbox(
		name=toolbox_name,
		default_version=created_toolbox.version,
	)

	assert updated_toolbox is not None

@pytest.mark.integration
def test_delete_toolbox():
	toolbox_name = f"pytest-toolbox-{uuid4().hex[:8]}"

	toolboxes.create_toolbox(
		name=toolbox_name,
		description="Temporary toolbox created by pytest.",
		tools=[
			WebSearchToolboxTool(
				name="web_search",
				description="Search the public web.",
			)
		],
	)

	deleted_toolbox = toolboxes.delete_toolbox(name=toolbox_name)

	assert deleted_toolbox is None

@pytest.mark.integration
def test_get_toolbox_version(request):
	toolbox_name = f"pytest-toolbox-{uuid4().hex[:8]}"

	created_toolbox = toolboxes.create_toolbox(
		name=toolbox_name,
		description="Temporary toolbox created by pytest.",
		tools=[
			WebSearchToolboxTool(
				name="web_search",
				description="Search the public web.",
			)
		],
	)
	request.addfinalizer(lambda: toolboxes.delete_toolbox(name=toolbox_name))

	retrieved_version = toolboxes.get_toolbox_version(
		name=toolbox_name,
		version=created_toolbox.version,
	)

	assert retrieved_version is not None

@pytest.mark.integration
def test_list_toolbox_versions(request):
	toolbox_name = f"pytest-toolbox-{uuid4().hex[:8]}"

	toolboxes.create_toolbox(
		name=toolbox_name,
		description="Temporary toolbox created by pytest.",
		tools=[
			WebSearchToolboxTool(
				name="web_search",
				description="Search the public web.",
			)
		],
	)
	request.addfinalizer(lambda: toolboxes.delete_toolbox(name=toolbox_name))

	versions = toolboxes.list_toolbox_versions(name=toolbox_name)

	assert versions

@pytest.mark.integration
def test_delete_toolbox_version(request):
	toolbox_name = f"pytest-toolbox-{uuid4().hex[:8]}"

	created_toolbox = toolboxes.create_toolbox(
		name=toolbox_name,
		description="Temporary toolbox created by pytest.",
		tools=[
			WebSearchToolboxTool(
				name="web_search",
				description="Search the public web.",
			)
		],
	)
	request.addfinalizer(lambda: toolboxes.delete_toolbox(name=toolbox_name))

	created_version = toolboxes.create_toolbox(
		name=toolbox_name,
		description="Temporary toolbox version created by pytest.",
		tools=[
			WebSearchToolboxTool(
				name="web_search",
				description="Search the public web.",
			)
		],
	)
	toolboxes.update_toolbox(
		name=toolbox_name,
		default_version=created_toolbox.version,
	)

	deleted_version = toolboxes.delete_toolbox_version(
		name=toolbox_name,
		version=created_version.version,
	)

	assert deleted_version is None
