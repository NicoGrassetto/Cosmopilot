import os
from uuid import uuid4

import pytest
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import MemoryItemKind, MemoryStoreDefaultDefinition
from azure.identity import DefaultAzureCredential


@pytest.mark.integration
def test_begin_update_memories():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        memory_store_name = f"pytest-memory-store-{uuid4().hex[:8]}"
        client.beta.memory_stores.create(
            name=memory_store_name,
            definition=MemoryStoreDefaultDefinition(
                chat_model=os.environ["AZURE_DEPLOYMENT_NAME"],
                embedding_model=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"],
            ),
        )

        try:
            updated_memories = client.beta.memory_stores.begin_update_memories(
                name=memory_store_name,
                scope="pytest",
                items=[{"role": "user", "content": "I always travel by train."}],
            ).result()

            assert updated_memories is not None
        finally:
            client.beta.memory_stores.delete(name=memory_store_name)


@pytest.mark.integration
def test_create():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        memory_store_name = f"pytest-memory-store-{uuid4().hex[:8]}"

        try:
            created_memory_store = client.beta.memory_stores.create(
                name=memory_store_name,
                definition=MemoryStoreDefaultDefinition(
                    chat_model=os.environ["AZURE_DEPLOYMENT_NAME"],
                    embedding_model=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"],
                ),
                description="Temporary memory store created by pytest.",
            )

            assert created_memory_store is not None
        finally:
            client.beta.memory_stores.delete(name=memory_store_name)


@pytest.mark.integration
def test_create_memory():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        memory_store_name = f"pytest-memory-store-{uuid4().hex[:8]}"
        client.beta.memory_stores.create(
            name=memory_store_name,
            definition=MemoryStoreDefaultDefinition(
                chat_model=os.environ["AZURE_DEPLOYMENT_NAME"],
                embedding_model=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"],
            ),
        )

        try:
            created_memory = client.beta.memory_stores.create_memory(
                name=memory_store_name,
                scope="pytest",
                content="The user always travels by train.",
                kind=MemoryItemKind.USER_PROFILE,
            )

            assert created_memory is not None
        finally:
            client.beta.memory_stores.delete(name=memory_store_name)


@pytest.mark.integration
def test_delete():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        memory_store_name = f"pytest-memory-store-{uuid4().hex[:8]}"
        client.beta.memory_stores.create(
            name=memory_store_name,
            definition=MemoryStoreDefaultDefinition(
                chat_model=os.environ["AZURE_DEPLOYMENT_NAME"],
                embedding_model=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"],
            ),
        )

        deleted_memory_store = client.beta.memory_stores.delete(name=memory_store_name)

        assert deleted_memory_store is not None


@pytest.mark.integration
def test_delete_memory():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        memory_store_name = f"pytest-memory-store-{uuid4().hex[:8]}"
        client.beta.memory_stores.create(
            name=memory_store_name,
            definition=MemoryStoreDefaultDefinition(
                chat_model=os.environ["AZURE_DEPLOYMENT_NAME"],
                embedding_model=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"],
            ),
        )
        created_memory = client.beta.memory_stores.create_memory(
            name=memory_store_name,
            scope="pytest",
            content="The user always travels by train.",
            kind=MemoryItemKind.USER_PROFILE,
        )

        try:
            deleted_memory = client.beta.memory_stores.delete_memory(
                name=memory_store_name,
                memory_id=created_memory.memory_id,
            )

            assert deleted_memory is not None
        finally:
            client.beta.memory_stores.delete(name=memory_store_name)


@pytest.mark.integration
def test_delete_scope():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        memory_store_name = f"pytest-memory-store-{uuid4().hex[:8]}"
        client.beta.memory_stores.create(
            name=memory_store_name,
            definition=MemoryStoreDefaultDefinition(
                chat_model=os.environ["AZURE_DEPLOYMENT_NAME"],
                embedding_model=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"],
            ),
        )
        client.beta.memory_stores.create_memory(
            name=memory_store_name,
            scope="pytest",
            content="The user always travels by train.",
            kind=MemoryItemKind.USER_PROFILE,
        )

        try:
            deleted_scope = client.beta.memory_stores.delete_scope(
                name=memory_store_name,
                scope="pytest",
            )

            assert deleted_scope is not None
        finally:
            client.beta.memory_stores.delete(name=memory_store_name)


@pytest.mark.integration
def test_get():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        memory_store_name = f"pytest-memory-store-{uuid4().hex[:8]}"
        client.beta.memory_stores.create(
            name=memory_store_name,
            definition=MemoryStoreDefaultDefinition(
                chat_model=os.environ["AZURE_DEPLOYMENT_NAME"],
                embedding_model=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"],
            ),
        )

        try:
            retrieved_memory_store = client.beta.memory_stores.get(
                name=memory_store_name,
            )

            assert retrieved_memory_store is not None
        finally:
            client.beta.memory_stores.delete(name=memory_store_name)


@pytest.mark.integration
def test_get_memory():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        memory_store_name = f"pytest-memory-store-{uuid4().hex[:8]}"
        client.beta.memory_stores.create(
            name=memory_store_name,
            definition=MemoryStoreDefaultDefinition(
                chat_model=os.environ["AZURE_DEPLOYMENT_NAME"],
                embedding_model=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"],
            ),
        )
        created_memory = client.beta.memory_stores.create_memory(
            name=memory_store_name,
            scope="pytest",
            content="The user always travels by train.",
            kind=MemoryItemKind.USER_PROFILE,
        )

        try:
            retrieved_memory = client.beta.memory_stores.get_memory(
                name=memory_store_name,
                memory_id=created_memory.memory_id,
            )

            assert retrieved_memory is not None
        finally:
            client.beta.memory_stores.delete(name=memory_store_name)


@pytest.mark.integration
def test_list():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        listed_memory_stores = list(client.beta.memory_stores.list())

        assert isinstance(listed_memory_stores, list)


@pytest.mark.integration
def test_list_memories():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        memory_store_name = f"pytest-memory-store-{uuid4().hex[:8]}"
        client.beta.memory_stores.create(
            name=memory_store_name,
            definition=MemoryStoreDefaultDefinition(
                chat_model=os.environ["AZURE_DEPLOYMENT_NAME"],
                embedding_model=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"],
            ),
        )
        client.beta.memory_stores.create_memory(
            name=memory_store_name,
            scope="pytest",
            content="The user always travels by train.",
            kind=MemoryItemKind.USER_PROFILE,
        )

        try:
            listed_memories = list(
                client.beta.memory_stores.list_memories(
                    name=memory_store_name,
                    scope="pytest",
                )
            )

            assert isinstance(listed_memories, list)
        finally:
            client.beta.memory_stores.delete(name=memory_store_name)


@pytest.mark.integration
def test_search_memories():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        memory_store_name = f"pytest-memory-store-{uuid4().hex[:8]}"
        client.beta.memory_stores.create(
            name=memory_store_name,
            definition=MemoryStoreDefaultDefinition(
                chat_model=os.environ["AZURE_DEPLOYMENT_NAME"],
                embedding_model=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"],
            ),
        )
        client.beta.memory_stores.create_memory(
            name=memory_store_name,
            scope="pytest",
            content="The user always travels by train.",
            kind=MemoryItemKind.USER_PROFILE,
        )

        try:
            search_result = client.beta.memory_stores.search_memories(
                name=memory_store_name,
                scope="pytest",
                items="How does the user like to travel?",
            )

            assert search_result is not None
        finally:
            client.beta.memory_stores.delete(name=memory_store_name)


@pytest.mark.integration
def test_update():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        memory_store_name = f"pytest-memory-store-{uuid4().hex[:8]}"
        client.beta.memory_stores.create(
            name=memory_store_name,
            definition=MemoryStoreDefaultDefinition(
                chat_model=os.environ["AZURE_DEPLOYMENT_NAME"],
                embedding_model=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"],
            ),
        )

        try:
            updated_memory_store = client.beta.memory_stores.update(
                name=memory_store_name,
                description="Temporary memory store updated by pytest.",
            )

            assert updated_memory_store is not None
        finally:
            client.beta.memory_stores.delete(name=memory_store_name)


@pytest.mark.integration
def test_update_memory():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        memory_store_name = f"pytest-memory-store-{uuid4().hex[:8]}"
        client.beta.memory_stores.create(
            name=memory_store_name,
            definition=MemoryStoreDefaultDefinition(
                chat_model=os.environ["AZURE_DEPLOYMENT_NAME"],
                embedding_model=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"],
            ),
        )
        created_memory = client.beta.memory_stores.create_memory(
            name=memory_store_name,
            scope="pytest",
            content="The user always travels by train.",
            kind=MemoryItemKind.USER_PROFILE,
        )

        try:
            updated_memory = client.beta.memory_stores.update_memory(
                name=memory_store_name,
                memory_id=created_memory.memory_id,
                content="The user always travels by night train.",
            )

            assert updated_memory is not None
        finally:
            client.beta.memory_stores.delete(name=memory_store_name)
