import inspect
import logging
from unittest.mock import MagicMock, call

from azure.ai.projects.operations import DeploymentsOperations

import deployments


def test_deployment_wrapper_parameters_match_sdk():
    pairs = (
        (deployments.get_deployment, DeploymentsOperations.get),
        (deployments.list_deployments, DeploymentsOperations.list),
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


def test_deployment_wrappers_delegate_to_deployments(monkeypatch, caplog):
    endpoint = "https://example.services.ai.azure.com/api/projects/test"
    monkeypatch.setenv("AZURE_AI_PROJECT_ENDPOINT", endpoint)
    caplog.set_level(logging.INFO, logger=deployments.__name__)

    credential_context = MagicMock()
    credential = object()
    credential_context.__enter__.return_value = credential
    credential_factory = MagicMock(return_value=credential_context)

    client = MagicMock()
    client.__enter__.return_value = client
    client_factory = MagicMock(return_value=client)
    sdk_deployments = client.deployments

    monkeypatch.setattr(
        deployments,
        "DefaultAzureCredential",
        credential_factory,
    )
    monkeypatch.setattr(deployments, "AIProjectClient", client_factory)

    retrieved = object()
    sdk_deployments.get.return_value = retrieved
    assert deployments.get_deployment("chat-model") is retrieved
    sdk_deployments.get.assert_called_once_with(name="chat-model")

    listed = [object(), object()]
    sdk_deployments.list.return_value = iter(listed)
    assert deployments.list_deployments(
        model_publisher="OpenAI",
        model_name="gpt-4.1-nano",
        deployment_type="ModelDeployment",
    ) == listed
    sdk_deployments.list.assert_called_once_with(
        model_publisher="OpenAI",
        model_name="gpt-4.1-nano",
        deployment_type="ModelDeployment",
    )

    assert credential_factory.call_count == 2
    assert client_factory.call_args_list == [
        call(endpoint=endpoint, credential=credential),
        call(endpoint=endpoint, credential=credential),
    ]

    messages = [record.getMessage() for record in caplog.records]
    expected_prefixes = (
        "Getting deployment name=chat-model",
        "Retrieved deployment name=chat-model duration_ms=",
        "Listing deployments model_publisher=OpenAI "
        "model_name=gpt-4.1-nano deployment_type=ModelDeployment",
        "Listed deployments count=2 duration_ms=",
    )

    assert len(messages) == len(expected_prefixes)
    assert all(
        message.startswith(expected_prefix)
        for message, expected_prefix in zip(messages, expected_prefixes)
    )