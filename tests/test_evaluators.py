import os
from uuid import uuid4

import pytest
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    EvaluatorCategory,
    EvaluatorCredentialRequest,
    EvaluatorGenerationInputs,
    EvaluatorGenerationJob,
    EvaluatorType,
    EvaluatorVersion,
    PendingUploadRequest,
    PendingUploadType,
    PromptBasedEvaluatorDefinition,
    PromptEvaluatorGenerationJobSource,
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
        evaluator_name = f"pytest-evaluator-{uuid4().hex[:8]}"
        generation_job = client.beta.evaluators.begin_create_generation_job(
            job=EvaluatorGenerationJob(
                inputs=EvaluatorGenerationInputs(
                    sources=[
                        PromptEvaluatorGenerationJobSource(
                            prompt="Judge whether the answer is polite.",
                        )
                    ],
                    model=os.environ["AZURE_DEPLOYMENT_NAME"],
                    evaluator_name=evaluator_name,
                ),
            ),
        )

        try:
            generated_evaluator_version = generation_job.result()

            assert generated_evaluator_version is not None
        finally:
            client.beta.evaluators.delete_version(name=evaluator_name, version="1")
            client.beta.evaluators.delete_generation_job(
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
        generation_job = client.beta.evaluators.begin_create_generation_job(
            job=EvaluatorGenerationJob(
                inputs=EvaluatorGenerationInputs(
                    sources=[
                        PromptEvaluatorGenerationJobSource(
                            prompt="Judge whether the answer is polite.",
                        )
                    ],
                    model=os.environ["AZURE_DEPLOYMENT_NAME"],
                    evaluator_name=f"pytest-evaluator-{uuid4().hex[:8]}",
                ),
            ),
        )

        try:
            cancelled_generation_job = client.beta.evaluators.cancel_generation_job(
                job_id=generation_job.details["job_id"],
            )

            assert cancelled_generation_job is not None
        finally:
            client.beta.evaluators.delete_generation_job(
                job_id=generation_job.details["job_id"],
            )


@pytest.mark.integration
def test_create_version():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        evaluator_name = f"pytest-evaluator-{uuid4().hex[:8]}"

        try:
            created_evaluator_version = client.beta.evaluators.create_version(
                name=evaluator_name,
                evaluator_version=EvaluatorVersion(
                    display_name="Temporary evaluator created by pytest.",
                    evaluator_type=EvaluatorType.CUSTOM,
                    categories=[EvaluatorCategory.QUALITY],
                    definition=PromptBasedEvaluatorDefinition(
                        prompt_text="Answer 1 if the response is polite, 0 otherwise.",
                    ),
                ),
            )

            assert created_evaluator_version is not None
        finally:
            client.beta.evaluators.delete_version(name=evaluator_name, version="1")


@pytest.mark.integration
def test_delete_generation_job():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        generation_job = client.beta.evaluators.begin_create_generation_job(
            job=EvaluatorGenerationJob(
                inputs=EvaluatorGenerationInputs(
                    sources=[
                        PromptEvaluatorGenerationJobSource(
                            prompt="Judge whether the answer is polite.",
                        )
                    ],
                    model=os.environ["AZURE_DEPLOYMENT_NAME"],
                    evaluator_name=f"pytest-evaluator-{uuid4().hex[:8]}",
                ),
            ),
        )
        client.beta.evaluators.cancel_generation_job(
            job_id=generation_job.details["job_id"],
        )

        deleted_generation_job = client.beta.evaluators.delete_generation_job(
            job_id=generation_job.details["job_id"],
        )

        assert deleted_generation_job is None


@pytest.mark.integration
def test_delete_version():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        evaluator_name = f"pytest-evaluator-{uuid4().hex[:8]}"
        client.beta.evaluators.create_version(
            name=evaluator_name,
            evaluator_version=EvaluatorVersion(
                display_name="Temporary evaluator created by pytest.",
                evaluator_type=EvaluatorType.CUSTOM,
                categories=[EvaluatorCategory.QUALITY],
                definition=PromptBasedEvaluatorDefinition(
                    prompt_text="Answer 1 if the response is polite, 0 otherwise.",
                ),
            ),
        )

        deleted_evaluator_version = client.beta.evaluators.delete_version(
            name=evaluator_name,
            version="1",
        )

        assert deleted_evaluator_version is None


@pytest.mark.integration
def test_get_credentials():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        evaluator_name = f"pytest-evaluator-{uuid4().hex[:8]}"
        pending_upload = client.beta.evaluators.pending_upload(
            name=evaluator_name,
            version="1",
            pending_upload_request=PendingUploadRequest(
                pending_upload_type=PendingUploadType.BLOB_REFERENCE,
            ),
        )

        try:
            evaluator_credential = client.beta.evaluators.get_credentials(
                name=evaluator_name,
                version="1",
                credential_request=EvaluatorCredentialRequest(
                    blob_uri=pending_upload.blob_reference.blob_uri,
                ),
            )

            assert evaluator_credential is not None
        finally:
            client.beta.evaluators.delete_version(name=evaluator_name, version="1")


@pytest.mark.integration
def test_get_generation_job():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        generation_job = client.beta.evaluators.begin_create_generation_job(
            job=EvaluatorGenerationJob(
                inputs=EvaluatorGenerationInputs(
                    sources=[
                        PromptEvaluatorGenerationJobSource(
                            prompt="Judge whether the answer is polite.",
                        )
                    ],
                    model=os.environ["AZURE_DEPLOYMENT_NAME"],
                    evaluator_name=f"pytest-evaluator-{uuid4().hex[:8]}",
                ),
            ),
        )

        try:
            retrieved_generation_job = client.beta.evaluators.get_generation_job(
                job_id=generation_job.details["job_id"],
            )

            assert retrieved_generation_job is not None
        finally:
            client.beta.evaluators.cancel_generation_job(
                job_id=generation_job.details["job_id"],
            )
            client.beta.evaluators.delete_generation_job(
                job_id=generation_job.details["job_id"],
            )


@pytest.mark.integration
def test_get_version():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        evaluator_name = f"pytest-evaluator-{uuid4().hex[:8]}"
        client.beta.evaluators.create_version(
            name=evaluator_name,
            evaluator_version=EvaluatorVersion(
                display_name="Temporary evaluator created by pytest.",
                evaluator_type=EvaluatorType.CUSTOM,
                categories=[EvaluatorCategory.QUALITY],
                definition=PromptBasedEvaluatorDefinition(
                    prompt_text="Answer 1 if the response is polite, 0 otherwise.",
                ),
            ),
        )

        try:
            retrieved_evaluator_version = client.beta.evaluators.get_version(
                name=evaluator_name,
                version="1",
            )

            assert retrieved_evaluator_version is not None
        finally:
            client.beta.evaluators.delete_version(name=evaluator_name, version="1")


@pytest.mark.integration
def test_list():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        listed_evaluators = list(client.beta.evaluators.list())

        assert isinstance(listed_evaluators, list)


@pytest.mark.integration
def test_list_generation_jobs():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        listed_generation_jobs = list(client.beta.evaluators.list_generation_jobs())

        assert isinstance(listed_generation_jobs, list)


@pytest.mark.integration
def test_list_versions():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        evaluator_name = f"pytest-evaluator-{uuid4().hex[:8]}"
        client.beta.evaluators.create_version(
            name=evaluator_name,
            evaluator_version=EvaluatorVersion(
                display_name="Temporary evaluator created by pytest.",
                evaluator_type=EvaluatorType.CUSTOM,
                categories=[EvaluatorCategory.QUALITY],
                definition=PromptBasedEvaluatorDefinition(
                    prompt_text="Answer 1 if the response is polite, 0 otherwise.",
                ),
            ),
        )

        try:
            evaluator_versions = list(
                client.beta.evaluators.list_versions(name=evaluator_name)
            )

            assert isinstance(evaluator_versions, list)
        finally:
            client.beta.evaluators.delete_version(name=evaluator_name, version="1")


@pytest.mark.integration
def test_pending_upload():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        evaluator_name = f"pytest-evaluator-{uuid4().hex[:8]}"

        try:
            pending_upload = client.beta.evaluators.pending_upload(
                name=evaluator_name,
                version="1",
                pending_upload_request=PendingUploadRequest(
                    pending_upload_type=PendingUploadType.BLOB_REFERENCE,
                ),
            )

            assert pending_upload is not None
        finally:
            client.beta.evaluators.delete_version(name=evaluator_name, version="1")


@pytest.mark.integration
def test_update_version():
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        evaluator_name = f"pytest-evaluator-{uuid4().hex[:8]}"
        client.beta.evaluators.create_version(
            name=evaluator_name,
            evaluator_version=EvaluatorVersion(
                display_name="Temporary evaluator created by pytest.",
                evaluator_type=EvaluatorType.CUSTOM,
                categories=[EvaluatorCategory.QUALITY],
                definition=PromptBasedEvaluatorDefinition(
                    prompt_text="Answer 1 if the response is polite, 0 otherwise.",
                ),
            ),
        )

        try:
            updated_evaluator_version = client.beta.evaluators.update_version(
                name=evaluator_name,
                version="1",
                evaluator_version=EvaluatorVersion(
                    display_name="Temporary evaluator updated by pytest.",
                    evaluator_type=EvaluatorType.CUSTOM,
                    categories=[EvaluatorCategory.QUALITY],
                    definition=PromptBasedEvaluatorDefinition(
                        prompt_text="Answer 1 if the response is concise, 0 otherwise.",
                    ),
                ),
            )

            assert updated_evaluator_version is not None
        finally:
            client.beta.evaluators.delete_version(name=evaluator_name, version="1")
