from uuid import uuid4

import pytest

from evaluations import datasets

@pytest.mark.integration
def test_upload_dataset(request, tmp_path):
    dataset_name = f"pytest-dataset-{uuid4().hex[:8]}"
    dataset_version = "1"
    dataset_path = tmp_path / "dataset.jsonl"
    dataset_path.write_text('{"query":"test"}\n', encoding="utf-8")

    uploaded_dataset = datasets.upload_dataset(
        name=dataset_name,
        version=dataset_version,
        path=str(dataset_path),
    )
    request.addfinalizer(
        lambda: datasets.delete_dataset(dataset_name, dataset_version)
    )

    assert uploaded_dataset is not None

@pytest.mark.integration
def test_get_dataset(request, tmp_path):
    dataset_name = f"pytest-dataset-{uuid4().hex[:8]}"
    dataset_version = "1"
    dataset_path = tmp_path / "dataset.jsonl"
    dataset_path.write_text('{"query":"test"}\n', encoding="utf-8")

    datasets.upload_dataset(
        name=dataset_name,
        version=dataset_version,
        path=str(dataset_path),
    )
    request.addfinalizer(
        lambda: datasets.delete_dataset(dataset_name, dataset_version)
    )

    retrieved_dataset = datasets.get_dataset(
        name=dataset_name,
        version=dataset_version,
    )

    assert retrieved_dataset is not None

@pytest.mark.integration
def test_list_datasets():
    listed_datasets = datasets.list_datasets()

    assert isinstance(listed_datasets, list)

@pytest.mark.integration
def test_delete_dataset(tmp_path):
    dataset_name = f"pytest-dataset-{uuid4().hex[:8]}"
    dataset_version = "1"
    dataset_path = tmp_path / "dataset.jsonl"
    dataset_path.write_text('{"query":"test"}\n', encoding="utf-8")

    datasets.upload_dataset(
        name=dataset_name,
        version=dataset_version,
        path=str(dataset_path),
    )

    deleted_dataset = datasets.delete_dataset(
        name=dataset_name,
        version=dataset_version,
    )

    assert deleted_dataset is None