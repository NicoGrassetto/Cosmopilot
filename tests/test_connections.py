import inspect
import logging
from unittest.mock import MagicMock, call

from azure.ai.projects.operations import ConnectionsOperations

import connections


def test_connection_wrapper_parameters_match_sdk():
    pairs = (
        (connections.get_connection, ConnectionsOperations.get),
        (connections.get_default_connection, ConnectionsOperations.get_default),
        (connections.list_connections, ConnectionsOperations.list),
    )

    for wrapper, sdk_method in pairs:
        wrapper_parameters = tuple(inspect.signature(wrapper).parameters.values())
        sdk_parameters = tuple(
            parameter
            for parameter in list(inspect.signature(sdk_method).parameters.values())[1:]
            if parameter.kind is not inspect.Parameter.VAR_KEYWORD
        )

        assert tuple(
            (parameter.name, parameter.kind, parameter.default)
            for parameter in wrapper_parameters
        ) == tuple(
            (parameter.name, parameter.kind, parameter.default)
            for parameter in sdk_parameters
        )


def test_connection_wrappers_delegate_to_connections(monkeypatch, caplog):
    endpoint = "https://example.services.ai.azure.com/api/projects/test"
    monkeypatch.setenv("AZURE_AI_PROJECT_ENDPOINT", endpoint)
    caplog.set_level(logging.INFO, logger=connections.__name__)

    credential_context = MagicMock()
    credential = object()
    credential_context.__enter__.return_value = credential
    credential_factory = MagicMock(return_value=credential_context)

    client = MagicMock()
    client.__enter__.return_value = client
    client_factory = MagicMock(return_value=client)
    sdk_connections = client.connections

    monkeypatch.setattr(
        connections,
        "DefaultAzureCredential",
        credential_factory,
    )
    monkeypatch.setattr(connections, "AIProjectClient", client_factory)

    retrieved = object()
    sdk_connections.get.return_value = retrieved
    assert connections.get_connection(
        "search-connection",
        include_credentials=True,
    ) is retrieved
    sdk_connections.get.assert_called_once_with(
        name="search-connection",
        include_credentials=True,
    )

    default = MagicMock(name="default_connection")
    default.name = "default-search"
    sdk_connections.get_default.return_value = default
    assert connections.get_default_connection(
        "CognitiveSearch",
        include_credentials=False,
    ) is default
    sdk_connections.get_default.assert_called_once_with(
        connection_type="CognitiveSearch",
        include_credentials=False,
    )

    listed = [object(), object()]
    sdk_connections.list.return_value = iter(listed)
    assert connections.list_connections(
        connection_type="CognitiveSearch",
        default_connection=True,
    ) == listed
    sdk_connections.list.assert_called_once_with(
        connection_type="CognitiveSearch",
        default_connection=True,
    )

    assert credential_factory.call_count == 3
    assert client_factory.call_args_list == [
        call(endpoint=endpoint, credential=credential),
        call(endpoint=endpoint, credential=credential),
        call(endpoint=endpoint, credential=credential),
    ]

    messages = [record.getMessage() for record in caplog.records]
    expected_prefixes = (
        "Getting connection name=search-connection",
        "Retrieved connection name=search-connection duration_ms=",
        "Getting default connection type=CognitiveSearch",
        "Retrieved default connection type=CognitiveSearch "
        "name=default-search duration_ms=",
        "Listing connections type=CognitiveSearch default_connection=True",
        "Listed connections count=2 duration_ms=",
    )

    assert len(messages) == len(expected_prefixes)
    assert all(
        message.startswith(expected_prefix)
        for message, expected_prefix in zip(messages, expected_prefixes)
    )