import os
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    DataGenerationJob,
    DataGenerationJobInputs,
    DataGenerationJobOutputOptions,
    DataGenerationJobScenario,
    FileDatasetVersion,
    PendingUploadRequest,
    PendingUploadType,
    PromptDataGenerationJobSource,
    SimpleQnADataGenerationJobOptions,
)
from azure.identity import DefaultAzureCredential


@pytest.mark.integration
def test_begin_create_generation_job():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        dataset_name = f"pytest-dataset-{uuid4().hex[:8]}"
        generation_job = client.beta.datasets.begin_create_generation_job(
            job=DataGenerationJob(
                inputs=DataGenerationJobInputs(
                    name=f"pytest-generation-{uuid4().hex[:8]}",
                    scenario=DataGenerationJobScenario.EVALUATION,
                    sources=[
                        PromptDataGenerationJobSource(
                            prompt="Questions and answers about the weather in Paris.",
                        )
                    ],
                    options=SimpleQnADataGenerationJobOptions(max_samples=1),
                    output_options=DataGenerationJobOutputOptions(name=dataset_name),
                ),
            ),
        )

        try:
            generation_result = generation_job.result()

            assert generation_result is not None
        finally:
            client.beta.datasets.delete_generation_job(
                job_id=generation_job.details["job_id"],
            )


@pytest.mark.integration
def test_cancel_generation_job():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        dataset_name = f"pytest-dataset-{uuid4().hex[:8]}"
        generation_job = client.beta.datasets.begin_create_generation_job(
            job=DataGenerationJob(
                inputs=DataGenerationJobInputs(
                    name=f"pytest-generation-{uuid4().hex[:8]}",
                    scenario=DataGenerationJobScenario.EVALUATION,
                    sources=[
                        PromptDataGenerationJobSource(
                            prompt="Questions and answers about the weather in Paris.",
                        )
                    ],
                    options=SimpleQnADataGenerationJobOptions(max_samples=1),
                    output_options=DataGenerationJobOutputOptions(name=dataset_name),
                ),
            ),
        )

        try:
            cancelled_generation_job = client.beta.datasets.cancel_generation_job(
                job_id=generation_job.details["job_id"],
            )

            assert cancelled_generation_job is not None
        finally:
            client.beta.datasets.delete_generation_job(
                job_id=generation_job.details["job_id"],
            )


@pytest.mark.integration
def test_create_or_update():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
        tempfile.TemporaryDirectory() as directory,
    ):
        dataset_name = f"pytest-dataset-{uuid4().hex[:8]}"
        dataset_file = Path(directory) / "dataset.jsonl"
        dataset_file.write_text('{"query": "test"}\n', encoding="utf-8")
        uploaded_dataset = client.datasets.upload_file(
            name=dataset_name,
            version="1",
            file_path=str(dataset_file),
        )

        try:
            created_dataset = client.datasets.create_or_update(
                name=dataset_name,
                version="2",
                dataset_version=FileDatasetVersion(
                    name=dataset_name,
                    version="2",
                    data_uri=uploaded_dataset.data_uri,
                    description="Temporary dataset created by pytest.",
                ),
            )

            assert created_dataset is not None
        finally:
            client.datasets.delete(name=dataset_name, version="2")
            client.datasets.delete(name=dataset_name, version="1")


@pytest.mark.integration
def test_delete():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
        tempfile.TemporaryDirectory() as directory,
    ):
        dataset_name = f"pytest-dataset-{uuid4().hex[:8]}"
        dataset_file = Path(directory) / "dataset.jsonl"
        dataset_file.write_text('{"query": "test"}\n', encoding="utf-8")
        client.datasets.upload_file(
            name=dataset_name,
            version="1",
            file_path=str(dataset_file),
        )

        deleted_dataset = client.datasets.delete(name=dataset_name, version="1")

        assert deleted_dataset is None


@pytest.mark.integration
def test_delete_generation_job():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        dataset_name = f"pytest-dataset-{uuid4().hex[:8]}"
        generation_job = client.beta.datasets.begin_create_generation_job(
            job=DataGenerationJob(
                inputs=DataGenerationJobInputs(
                    name=f"pytest-generation-{uuid4().hex[:8]}",
                    scenario=DataGenerationJobScenario.EVALUATION,
                    sources=[
                        PromptDataGenerationJobSource(
                            prompt="Questions and answers about the weather in Paris.",
                        )
                    ],
                    options=SimpleQnADataGenerationJobOptions(max_samples=1),
                    output_options=DataGenerationJobOutputOptions(name=dataset_name),
                ),
            ),
        )
        client.beta.datasets.cancel_generation_job(
            job_id=generation_job.details["job_id"],
        )

        deleted_generation_job = client.beta.datasets.delete_generation_job(
            job_id=generation_job.details["job_id"],
        )

        assert deleted_generation_job is None


@pytest.mark.integration
def test_get():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
        tempfile.TemporaryDirectory() as directory,
    ):
        dataset_name = f"pytest-dataset-{uuid4().hex[:8]}"
        dataset_file = Path(directory) / "dataset.jsonl"
        dataset_file.write_text('{"query": "test"}\n', encoding="utf-8")
        client.datasets.upload_file(
            name=dataset_name,
            version="1",
            file_path=str(dataset_file),
        )

        try:
            retrieved_dataset = client.datasets.get(name=dataset_name, version="1")

            assert retrieved_dataset is not None
        finally:
            client.datasets.delete(name=dataset_name, version="1")


@pytest.mark.integration
def test_get_credentials():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
        tempfile.TemporaryDirectory() as directory,
    ):
        dataset_name = f"pytest-dataset-{uuid4().hex[:8]}"
        dataset_file = Path(directory) / "dataset.jsonl"
        dataset_file.write_text('{"query": "test"}\n', encoding="utf-8")
        client.datasets.upload_file(
            name=dataset_name,
            version="1",
            file_path=str(dataset_file),
        )

        try:
            dataset_credential = client.datasets.get_credentials(
                name=dataset_name,
                version="1",
            )

            assert dataset_credential is not None
        finally:
            client.datasets.delete(name=dataset_name, version="1")


@pytest.mark.integration
def test_get_generation_job():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        dataset_name = f"pytest-dataset-{uuid4().hex[:8]}"
        generation_job = client.beta.datasets.begin_create_generation_job(
            job=DataGenerationJob(
                inputs=DataGenerationJobInputs(
                    name=f"pytest-generation-{uuid4().hex[:8]}",
                    scenario=DataGenerationJobScenario.EVALUATION,
                    sources=[
                        PromptDataGenerationJobSource(
                            prompt="Questions and answers about the weather in Paris.",
                        )
                    ],
                    options=SimpleQnADataGenerationJobOptions(max_samples=1),
                    output_options=DataGenerationJobOutputOptions(name=dataset_name),
                ),
            ),
        )

        try:
            retrieved_generation_job = client.beta.datasets.get_generation_job(
                job_id=generation_job.details["job_id"],
            )

            assert retrieved_generation_job is not None
        finally:
            client.beta.datasets.cancel_generation_job(
                job_id=generation_job.details["job_id"],
            )
            client.beta.datasets.delete_generation_job(
                job_id=generation_job.details["job_id"],
            )


@pytest.mark.integration
def test_list():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        listed_datasets = list(client.datasets.list())

        assert isinstance(listed_datasets, list)


@pytest.mark.integration
def test_list_generation_jobs():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        listed_generation_jobs = list(client.beta.datasets.list_generation_jobs())

        assert isinstance(listed_generation_jobs, list)


@pytest.mark.integration
def test_list_versions():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
        tempfile.TemporaryDirectory() as directory,
    ):
        dataset_name = f"pytest-dataset-{uuid4().hex[:8]}"
        dataset_file = Path(directory) / "dataset.jsonl"
        dataset_file.write_text('{"query": "test"}\n', encoding="utf-8")
        client.datasets.upload_file(
            name=dataset_name,
            version="1",
            file_path=str(dataset_file),
        )

        try:
            versions = list(client.datasets.list_versions(name=dataset_name))

            assert isinstance(versions, list)
        finally:
            client.datasets.delete(name=dataset_name, version="1")


@pytest.mark.integration
def test_pending_upload():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        dataset_name = f"pytest-dataset-{uuid4().hex[:8]}"

        try:
            pending_upload = client.datasets.pending_upload(
                name=dataset_name,
                version="1",
                pending_upload_request=PendingUploadRequest(
                    pending_upload_type=PendingUploadType.BLOB_REFERENCE,
                ),
            )

            assert pending_upload is not None
        finally:
            client.datasets.delete(name=dataset_name, version="1")


@pytest.mark.integration
def test_upload_file():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
        tempfile.TemporaryDirectory() as directory,
    ):
        dataset_name = f"pytest-dataset-{uuid4().hex[:8]}"
        dataset_file = Path(directory) / "dataset.jsonl"
        dataset_file.write_text('{"query": "test"}\n', encoding="utf-8")

        try:
            uploaded_dataset = client.datasets.upload_file(
                name=dataset_name,
                version="1",
                file_path=str(dataset_file),
            )

            assert uploaded_dataset is not None
        finally:
            client.datasets.delete(name=dataset_name, version="1")


@pytest.mark.integration
def test_upload_folder():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
        tempfile.TemporaryDirectory() as directory,
    ):
        dataset_name = f"pytest-dataset-{uuid4().hex[:8]}"
        (Path(directory) / "dataset.jsonl").write_text(
            '{"query": "test"}\n',
            encoding="utf-8",
        )

        try:
            uploaded_dataset = client.datasets.upload_folder(
                name=dataset_name,
                version="1",
                folder=directory,
            )

            assert uploaded_dataset is not None
        finally:
            client.datasets.delete(name=dataset_name, version="1")
