import os
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    ModelCredentialRequest,
    ModelPendingUploadRequest,
    ModelVersion,
    PendingUploadType,
    UpdateModelVersionRequest,
)
from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential


@pytest.mark.integration
def test_create():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
        tempfile.TemporaryDirectory() as directory,
    ):
        model_name = f"pytest-model-{uuid4().hex[:8]}"
        weights_file = Path(directory) / "weights.safetensors"
        weights_file.write_bytes(b"pytest")

        try:
            created_model = client.beta.models.create(
                name=model_name,
                version="1",
                source=str(weights_file),
                description="Temporary model registered by pytest.",
                wait_for_commit=False,
            )

            assert created_model is None
        finally:
            client.beta.models.delete(name=model_name, version="1")


@pytest.mark.integration
def test_delete():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        model_name = f"pytest-model-{uuid4().hex[:8]}"
        client.beta.models.pending_upload(
            name=model_name,
            version="1",
            pending_upload_request=ModelPendingUploadRequest(
                pending_upload_type=PendingUploadType.TEMPORARY_BLOB_REFERENCE,
            ),
        )

        deleted_model = client.beta.models.delete(name=model_name, version="1")

        assert deleted_model is None


@pytest.mark.integration
def test_get():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            client.beta.models.get(
                name=f"pytest-model-{uuid4().hex[:8]}",
                version="1",
            )


@pytest.mark.integration
def test_get_credentials():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        model_name = f"pytest-model-{uuid4().hex[:8]}"
        pending_upload = client.beta.models.pending_upload(
            name=model_name,
            version="1",
            pending_upload_request=ModelPendingUploadRequest(
                pending_upload_type=PendingUploadType.TEMPORARY_BLOB_REFERENCE,
            ),
        )

        try:
            model_credential = client.beta.models.get_credentials(
                name=model_name,
                version="1",
                credential_request=ModelCredentialRequest(
                    blob_uri=pending_upload.blob_reference.blob_uri,
                ),
            )

            assert model_credential is not None
        finally:
            client.beta.models.delete(name=model_name, version="1")


@pytest.mark.integration
def test_list():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        listed_models = list(client.beta.models.list())

        assert isinstance(listed_models, list)


@pytest.mark.integration
def test_list_versions():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        model_name = f"pytest-model-{uuid4().hex[:8]}"
        client.beta.models.pending_upload(
            name=model_name,
            version="1",
            pending_upload_request=ModelPendingUploadRequest(
                pending_upload_type=PendingUploadType.TEMPORARY_BLOB_REFERENCE,
            ),
        )

        try:
            model_versions = list(client.beta.models.list_versions(name=model_name))

            assert isinstance(model_versions, list)
        finally:
            client.beta.models.delete(name=model_name, version="1")


@pytest.mark.integration
def test_pending_create_version():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        model_name = f"pytest-model-{uuid4().hex[:8]}"
        pending_upload = client.beta.models.pending_upload(
            name=model_name,
            version="1",
            pending_upload_request=ModelPendingUploadRequest(
                pending_upload_type=PendingUploadType.TEMPORARY_BLOB_REFERENCE,
            ),
        )

        try:
            create_response = client.beta.models.pending_create_version(
                name=model_name,
                version="1",
                model_version=ModelVersion(
                    blob_uri=pending_upload.blob_reference.blob_uri,
                    description="Temporary model registered by pytest.",
                ),
            )

            assert create_response is not None
        finally:
            client.beta.models.delete(name=model_name, version="1")


@pytest.mark.integration
def test_pending_upload():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        model_name = f"pytest-model-{uuid4().hex[:8]}"

        try:
            pending_upload = client.beta.models.pending_upload(
                name=model_name,
                version="1",
                pending_upload_request=ModelPendingUploadRequest(
                    pending_upload_type=PendingUploadType.TEMPORARY_BLOB_REFERENCE,
                ),
            )

            assert pending_upload is not None
        finally:
            client.beta.models.delete(name=model_name, version="1")


@pytest.mark.integration
def test_update():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        with pytest.raises(ResourceNotFoundError):
            client.beta.models.update(
                name=f"pytest-model-{uuid4().hex[:8]}",
                version="1",
                model_version_update=UpdateModelVersionRequest(
                    description="Temporary model updated by pytest.",
                ),
            )
