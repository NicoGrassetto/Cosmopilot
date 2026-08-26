import inspect
import logging
from pathlib import Path
from unittest.mock import MagicMock, call

from azure.ai.projects.operations import BetaModelsOperations

import models


def test_model_wrapper_parameters_match_sdk():
    pairs = (
        (models.upload_weights, BetaModelsOperations.create),
        (models.delete_weights, BetaModelsOperations.delete),
        (models.get_model_credentials, BetaModelsOperations.get_credentials),
        (models.update_weights, BetaModelsOperations.update),
        (models.list_models, BetaModelsOperations.list),
        (models.list_model_versions, BetaModelsOperations.list_versions),
        (models.get_model_version, BetaModelsOperations.get),
    )

    for wrapper, sdk_method in pairs:
        wrapper_parameters = tuple(inspect.signature(wrapper).parameters.values())
        sdk_parameters = tuple(
            parameter
            for parameter in list(inspect.signature(sdk_method).parameters.values())[1:]
            if parameter.kind is not inspect.Parameter.VAR_KEYWORD
        )

        assert all(
            parameter.kind is not inspect.Parameter.VAR_KEYWORD
            for parameter in wrapper_parameters
        )
        assert tuple(
            (parameter.name, parameter.kind, parameter.default)
            for parameter in wrapper_parameters
        ) == tuple(
            (parameter.name, parameter.kind, parameter.default)
            for parameter in sdk_parameters
        )


def test_model_wrappers_delegate_to_beta_models(monkeypatch, caplog):
    endpoint = "https://example.services.ai.azure.com/api/projects/test"
    monkeypatch.setenv("AZURE_AI_PROJECT_ENDPOINT", endpoint)
    caplog.set_level(logging.INFO, logger=models.__name__)

    credential_context = MagicMock()
    credential = object()
    credential_context.__enter__.return_value = credential
    credential_factory = MagicMock(return_value=credential_context)

    client = MagicMock()
    client.__enter__.return_value = client
    client_factory = MagicMock(return_value=client)
    sdk_models = client.beta.models

    monkeypatch.setattr(models, "DefaultAzureCredential", credential_factory)
    monkeypatch.setattr(models, "AIProjectClient", client_factory)

    created = object()
    sdk_models.create.return_value = created
    source = Path("weights")
    assert models.upload_weights(
        name="custom-model",
        version="1",
        source=source,
        weight_type="LoRA",
        base_model="base-model",
        description="description",
        tags={"stage": "test"},
        azcopy_path="/usr/local/bin/azcopy",
        wait_for_commit=False,
        polling_timeout=10.0,
        polling_interval=0.5,
    ) is created
    sdk_models.create.assert_called_once_with(
        name="custom-model",
        version="1",
        source=source,
        weight_type="LoRA",
        base_model="base-model",
        description="description",
        tags={"stage": "test"},
        azcopy_path="/usr/local/bin/azcopy",
        wait_for_commit=False,
        polling_timeout=10.0,
        polling_interval=0.5,
    )

    models.delete_weights("custom-model", "1")
    sdk_models.delete.assert_called_once_with(
        name="custom-model",
        version="1",
    )

    credentials = object()
    sdk_models.get_credentials.return_value = credentials
    credential_request = {"kind": "SAS"}
    assert models.get_model_credentials(
        "custom-model",
        "1",
        credential_request,
    ) is credentials
    sdk_models.get_credentials.assert_called_once_with(
        name="custom-model",
        version="1",
        credential_request=credential_request,
    )

    updated = object()
    sdk_models.update.return_value = updated
    model_version_update = {"description": "updated"}
    assert models.update_weights(
        "custom-model",
        "1",
        model_version_update,
    ) is updated
    sdk_models.update.assert_called_once_with(
        name="custom-model",
        version="1",
        model_version_update=model_version_update,
    )

    latest = [object(), object()]
    sdk_models.list.return_value = iter(latest)
    assert models.list_models() == latest
    sdk_models.list.assert_called_once_with()

    versions = [object()]
    sdk_models.list_versions.return_value = iter(versions)
    assert models.list_model_versions("custom-model") == versions
    sdk_models.list_versions.assert_called_once_with(name="custom-model")

    retrieved = object()
    sdk_models.get.return_value = retrieved
    assert models.get_model_version("custom-model", "1") is retrieved
    sdk_models.get.assert_called_once_with(
        name="custom-model",
        version="1",
    )

    assert credential_factory.call_count == 7
    assert client_factory.call_args_list == [
        call(endpoint=endpoint, credential=credential)
    ] * 7

    messages = [record.getMessage() for record in caplog.records]
    expected_prefixes = (
        "Uploading model weights name=custom-model version=1 source=weights",
        "Uploaded model weights name=custom-model version=1 committed=True duration_ms=",
        "Deleting model weights name=custom-model version=1",
        "Deleted model weights name=custom-model version=1 duration_ms=",
        "Getting model credentials name=custom-model version=1",
        "Retrieved model credentials name=custom-model version=1 duration_ms=",
        "Updating model weights name=custom-model version=1",
        "Updated model weights name=custom-model version=1 duration_ms=",
        "Listing models",
        "Listed models count=2 duration_ms=",
        "Listing model versions name=custom-model",
        "Listed model versions name=custom-model count=1 duration_ms=",
        "Getting model version name=custom-model version=1",
        "Retrieved model version name=custom-model version=1 duration_ms=",
    )

    assert len(messages) == len(expected_prefixes)
    assert all(
        message.startswith(expected_prefix)
        for message, expected_prefix in zip(messages, expected_prefixes)
    )
    assert all("SAS" not in message for message in messages)