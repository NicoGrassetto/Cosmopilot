import json
import sys
from unittest.mock import MagicMock, call

import indexes_management


def test_index_wrappers_delegate_to_indexes(monkeypatch):
	endpoint = "https://example.services.ai.azure.com/api/projects/test"
	monkeypatch.setenv("AZURE_AI_PROJECT_ENDPOINT", endpoint)

	credential_context = MagicMock()
	credential = object()
	credential_context.__enter__.return_value = credential
	credential_factory = MagicMock(return_value=credential_context)

	client = MagicMock()
	client.__enter__.return_value = client
	client_factory = MagicMock(return_value=client)
	sdk_indexes = client.indexes

	monkeypatch.setattr(
		indexes_management,
		"DefaultAzureCredential",
		credential_factory,
	)
	monkeypatch.setattr(
		indexes_management,
		"AIProjectClient",
		client_factory,
	)

	definition = {
		"type": "AzureSearch",
		"connectionName": "search-connection",
		"indexName": "product-documents",
	}
	created = object()
	sdk_indexes.create_or_update.return_value = created
	assert indexes_management.create_or_update_index(
		"product-documents",
		"1",
		definition,
	) is created
	sdk_indexes.create_or_update.assert_called_once_with(
		name="product-documents",
		version="1",
		index=definition,
	)

	retrieved = object()
	sdk_indexes.get.return_value = retrieved
	assert indexes_management.get_index(
		"product-documents",
		"1",
	) is retrieved
	sdk_indexes.get.assert_called_once_with(
		name="product-documents",
		version="1",
	)

	latest_indexes = [object(), object()]
	sdk_indexes.list.return_value = iter(latest_indexes)
	assert indexes_management.list_indexes() == latest_indexes
	sdk_indexes.list.assert_called_once_with()

	versions = [object(), object()]
	sdk_indexes.list_versions.return_value = iter(versions)
	assert indexes_management.list_index_versions(
		"product-documents"
	) == versions
	sdk_indexes.list_versions.assert_called_once_with(
		name="product-documents"
	)

	assert indexes_management.delete_index(
		"product-documents",
		"1",
	) is None
	sdk_indexes.delete.assert_called_once_with(
		name="product-documents",
		version="1",
	)

	assert credential_factory.call_count == 5
	assert client_factory.call_args_list == [
		call(endpoint=endpoint, credential=credential)
	] * 5


def test_create_or_update_command_loads_index_json(
	monkeypatch,
	tmp_path,
	capsys,
):
	definition = {
		"type": "AzureSearch",
		"connectionName": "search-connection",
		"indexName": "product-documents",
	}
	definition_path = tmp_path / "index.json"
	definition_path.write_text(json.dumps(definition), encoding="utf-8")

	result = MagicMock()
	result.as_dict.return_value = {
		"name": "product-documents",
		"version": "1",
	}
	create_or_update_index = MagicMock(return_value=result)
	monkeypatch.setattr(
		indexes_management,
		"create_or_update_index",
		create_or_update_index,
	)
	monkeypatch.setattr(
		sys,
		"argv",
		[
			"indexes-management",
			"create-or-update",
			"--name",
			"product-documents",
			"--version",
			"1",
			"--index",
			str(definition_path),
		],
	)

	indexes_management.main()

	create_or_update_index.assert_called_once_with(
		"product-documents",
		"1",
		definition,
	)
	assert json.loads(capsys.readouterr().out) == {
		"name": "product-documents",
		"version": "1",
	}


def test_get_and_list_commands(monkeypatch, capsys):
	retrieved = MagicMock()
	retrieved.as_dict.return_value = {
		"name": "product-documents",
		"version": "1",
	}
	get_index = MagicMock(return_value=retrieved)
	monkeypatch.setattr(indexes_management, "get_index", get_index)
	monkeypatch.setattr(
		sys,
		"argv",
		[
			"indexes-management",
			"get",
			"--name",
			"product-documents",
			"--version",
			"1",
		],
	)

	indexes_management.main()

	get_index.assert_called_once_with("product-documents", "1")
	assert json.loads(capsys.readouterr().out) == {
		"name": "product-documents",
		"version": "1",
	}

	listed = MagicMock()
	listed.as_dict.return_value = {
		"name": "product-documents",
		"version": "2",
	}
	list_indexes = MagicMock(return_value=[listed])
	monkeypatch.setattr(indexes_management, "list_indexes", list_indexes)
	monkeypatch.setattr(
		sys,
		"argv",
		["indexes-management", "list"],
	)

	indexes_management.main()

	list_indexes.assert_called_once_with()
	assert json.loads(capsys.readouterr().out) == [
		{"name": "product-documents", "version": "2"}
	]


def test_list_versions_and_delete_commands(monkeypatch, capsys):
	version = MagicMock()
	version.as_dict.return_value = {
		"name": "product-documents",
		"version": "1",
	}
	list_index_versions = MagicMock(return_value=[version])
	monkeypatch.setattr(
		indexes_management,
		"list_index_versions",
		list_index_versions,
	)
	monkeypatch.setattr(
		sys,
		"argv",
		[
			"indexes-management",
			"list-versions",
			"--name",
			"product-documents",
		],
	)

	indexes_management.main()

	list_index_versions.assert_called_once_with("product-documents")
	assert json.loads(capsys.readouterr().out) == [
		{"name": "product-documents", "version": "1"}
	]

	delete_index = MagicMock()
	monkeypatch.setattr(indexes_management, "delete_index", delete_index)
	monkeypatch.setattr(
		sys,
		"argv",
		[
			"indexes-management",
			"delete",
			"--name",
			"product-documents",
			"--version",
			"1",
		],
	)

	indexes_management.main()

	delete_index.assert_called_once_with("product-documents", "1")
	assert json.loads(capsys.readouterr().out) == {
		"name": "product-documents",
		"version": "1",
		"deleted": True,
	}