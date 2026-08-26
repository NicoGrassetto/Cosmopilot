import sys
from unittest.mock import MagicMock, call

import pytest

import memory_storage


def test_memory_store_wrappers_delegate_to_beta_memory_stores(monkeypatch):
    endpoint = "https://example.services.ai.azure.com/api/projects/test"
    monkeypatch.setenv("AZURE_AI_PROJECT_ENDPOINT", endpoint)

    credential_context = MagicMock()
    credential = object()
    credential_context.__enter__.return_value = credential
    credential_factory = MagicMock(return_value=credential_context)

    client = MagicMock()
    client.__enter__.return_value = client
    client_factory = MagicMock(return_value=client)
    sdk_memory_stores = client.beta.memory_stores

    monkeypatch.setattr(
        memory_storage,
        "DefaultAzureCredential",
        credential_factory,
    )
    monkeypatch.setattr(memory_storage, "AIProjectClient", client_factory)

    created_store = object()
    definition = object()
    sdk_memory_stores.create.return_value = created_store
    assert memory_storage.create_memory_store(
        name="support-memory",
        definition=definition,
        description="Customer support memory",
        metadata={"environment": "test"},
    ) is created_store
    sdk_memory_stores.create.assert_called_once_with(
        name="support-memory",
        definition=definition,
        description="Customer support memory",
        metadata={"environment": "test"},
    )

    retrieved_store = object()
    sdk_memory_stores.get.return_value = retrieved_store
    assert memory_storage.get_memory_store("support-memory") is retrieved_store
    sdk_memory_stores.get.assert_called_once_with(name="support-memory")

    stores = [object(), object()]
    sdk_memory_stores.list.return_value = iter(stores)
    assert memory_storage.list_memory_stores(
        limit=10,
        order="asc",
        before="store-2",
    ) == stores
    sdk_memory_stores.list.assert_called_once_with(
        limit=10,
        order="asc",
        before="store-2",
    )

    updated_store = object()
    sdk_memory_stores.update.return_value = updated_store
    assert memory_storage.update_memory_store(
        "support-memory",
        description="Updated",
        metadata={"environment": "production"},
    ) is updated_store
    sdk_memory_stores.update.assert_called_once_with(
        name="support-memory",
        description="Updated",
        metadata={"environment": "production"},
    )

    deleted_store = object()
    sdk_memory_stores.delete.return_value = deleted_store
    assert memory_storage.delete_memory_store("support-memory") is deleted_store
    sdk_memory_stores.delete.assert_called_once_with(name="support-memory")

    messages = [
        {
            "role": "user",
            "type": "message",
            "content": "I prefer concise answers.",
        }
    ]
    update_result = object()
    update_poller = MagicMock()
    update_poller.result.return_value = update_result
    sdk_memory_stores.begin_update_memories.return_value = update_poller
    assert memory_storage.begin_update_memories(
        "support-memory",
        scope="user-123",
        items=messages,
        previous_update_id="update-1",
        update_delay=0,
    ) is update_result
    sdk_memory_stores.begin_update_memories.assert_called_once_with(
        name="support-memory",
        scope="user-123",
        items=messages,
        previous_update_id="update-1",
        update_delay=0,
    )
    update_poller.result.assert_called_once_with()

    search_result = object()
    search_options = object()
    sdk_memory_stores.search_memories.return_value = search_result
    assert memory_storage.search_memories(
        "support-memory",
        scope="user-123",
        items=messages,
        previous_search_id="search-1",
        options=search_options,
    ) is search_result
    sdk_memory_stores.search_memories.assert_called_once_with(
        name="support-memory",
        scope="user-123",
        items=messages,
        previous_search_id="search-1",
        options=search_options,
    )

    deleted_scope = object()
    sdk_memory_stores.delete_scope.return_value = deleted_scope
    assert memory_storage.delete_scope(
        "support-memory",
        scope="user-123",
    ) is deleted_scope
    sdk_memory_stores.delete_scope.assert_called_once_with(
        name="support-memory",
        scope="user-123",
    )

    created_memory = object()
    sdk_memory_stores.create_memory.return_value = created_memory
    assert memory_storage.create_memory(
        "support-memory",
        scope="user-123",
        content="User prefers concise answers.",
        kind="user_profile",
    ) is created_memory
    sdk_memory_stores.create_memory.assert_called_once_with(
        name="support-memory",
        scope="user-123",
        content="User prefers concise answers.",
        kind="user_profile",
    )

    retrieved_memory = object()
    sdk_memory_stores.get_memory.return_value = retrieved_memory
    assert memory_storage.get_memory(
        "support-memory",
        "memory-1",
    ) is retrieved_memory
    sdk_memory_stores.get_memory.assert_called_once_with(
        name="support-memory",
        memory_id="memory-1",
    )

    memories = [object()]
    sdk_memory_stores.list_memories.return_value = iter(memories)
    assert memory_storage.list_memories(
        "support-memory",
        scope="user-123",
        kind="user_profile",
        limit=5,
        order="desc",
        before="memory-2",
    ) == memories
    sdk_memory_stores.list_memories.assert_called_once_with(
        name="support-memory",
        scope="user-123",
        kind="user_profile",
        limit=5,
        order="desc",
        before="memory-2",
    )

    updated_memory = object()
    sdk_memory_stores.update_memory.return_value = updated_memory
    assert memory_storage.update_memory(
        "support-memory",
        "memory-1",
        content="User prefers detailed answers.",
    ) is updated_memory
    sdk_memory_stores.update_memory.assert_called_once_with(
        name="support-memory",
        memory_id="memory-1",
        content="User prefers detailed answers.",
    )

    deleted_memory = object()
    sdk_memory_stores.delete_memory.return_value = deleted_memory
    assert memory_storage.delete_memory(
        "support-memory",
        "memory-1",
    ) is deleted_memory
    sdk_memory_stores.delete_memory.assert_called_once_with(
        name="support-memory",
        memory_id="memory-1",
    )

    assert credential_factory.call_count == 13
    assert client_factory.call_args_list == [
        call(endpoint=endpoint, credential=credential)
    ] * 13


def test_cli_registers_every_public_memory_store_operation(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(sys, "argv", ["memory-storage", "--help"])

    with pytest.raises(SystemExit) as error:
        memory_storage.main()

    assert error.value.code == 0
    help_text = capsys.readouterr().out
    for command in (
        "create",
        "get",
        "list",
        "update",
        "delete",
        "begin-update-memories",
        "search-memories",
        "delete-scope",
        "create-memory",
        "get-memory",
        "list-memories",
        "update-memory",
        "delete-memory",
    ):
        assert command in help_text