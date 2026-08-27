from uuid import uuid4

import pytest
from azure.ai.projects.models import AzureAISearchIndex

import indexes_management


@pytest.mark.integration
def test_create_or_update_index(request):
	index_name = f"pytest-index-{uuid4().hex[:8]}"

	created_index = indexes_management.create_or_update_index(
		name=index_name,
		version="1",
		index=AzureAISearchIndex(
			connection_name="aisearch",
			index_name=index_name,
		),
	)
	request.addfinalizer(
		lambda: indexes_management.delete_index(index_name, "1")
	)

	assert created_index.name == index_name
	assert created_index.version == "1"


@pytest.mark.integration
def test_get_index(request):
	index_name = f"pytest-index-{uuid4().hex[:8]}"

	indexes_management.create_or_update_index(
		name=index_name,
		version="1",
		index=AzureAISearchIndex(
			connection_name="aisearch",
			index_name=index_name,
		),
	)
	request.addfinalizer(
		lambda: indexes_management.delete_index(index_name, "1")
	)

	retrieved_index = indexes_management.get_index(index_name, "1")

	assert retrieved_index.name == index_name
	assert retrieved_index.version == "1"


@pytest.mark.integration
def test_list_indexes():
	listed_indexes = indexes_management.list_indexes()

	assert isinstance(listed_indexes, list)


@pytest.mark.integration
def test_list_index_versions(request):
	index_name = f"pytest-index-{uuid4().hex[:8]}"

	indexes_management.create_or_update_index(
		name=index_name,
		version="1",
		index=AzureAISearchIndex(
			connection_name="aisearch",
			index_name=index_name,
		),
	)
	request.addfinalizer(
		lambda: indexes_management.delete_index(index_name, "1")
	)

	versions = indexes_management.list_index_versions(index_name)

	assert any(index.version == "1" for index in versions)


@pytest.mark.integration
def test_delete_index():
	index_name = f"pytest-index-{uuid4().hex[:8]}"

	indexes_management.create_or_update_index(
		name=index_name,
		version="1",
		index=AzureAISearchIndex(
			connection_name="aisearch",
			index_name=index_name,
		),
	)

	deleted_index = indexes_management.delete_index(index_name, "1")

	assert deleted_index is None