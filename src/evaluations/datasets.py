from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import DataGenerationJob, DataGenerationJobResult, PageOrder
from azure.core.polling import LROPoller
from azure.ai.projects.models import FileDatasetVersion
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)


def create_generation_job(
	job: DataGenerationJob,
	*,
	operation_id: str | None = None,
	**kwargs: Any,
) -> LROPoller[DataGenerationJobResult]:
	credential = DefaultAzureCredential()
	client = AIProjectClient(
		endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
		credential=credential,
		allow_preview=True,
	)
	return client.beta.datasets.begin_create_generation_job(
		job=job,
		operation_id=operation_id,
		**kwargs,
	)


def cancel_generation_job(
	job_id: str,
	**kwargs: Any,
) -> DataGenerationJob:
	with DefaultAzureCredential() as credential:
		with AIProjectClient(
			endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
			credential=credential,
			allow_preview=True,
		) as client:
			return client.beta.datasets.cancel_generation_job(job_id=job_id, **kwargs)


def delete_generation_job(
	job_id: str,
	**kwargs: Any,
) -> None:
	with DefaultAzureCredential() as credential:
		with AIProjectClient(
			endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
			credential=credential,
			allow_preview=True,
		) as client:
			client.beta.datasets.delete_generation_job(job_id=job_id, **kwargs)


def get_generation_job(
	job_id: str,
	**kwargs: Any,
) -> DataGenerationJob:
	with DefaultAzureCredential() as credential:
		with AIProjectClient(
			endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
			credential=credential,
			allow_preview=True,
		) as client:
			return client.beta.datasets.get_generation_job(job_id=job_id, **kwargs)


def list_generation_jobs(
	*,
	limit: int | None = None,
	order: str | PageOrder | None = None,
	before: str | None = None,
	**kwargs: Any,
) -> list[DataGenerationJob]:
	with DefaultAzureCredential() as credential:
		with AIProjectClient(
			endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
			credential=credential,
			allow_preview=True,
		) as client:
			return list(
				client.beta.datasets.list_generation_jobs(
					limit=limit,
					order=order,
					before=before,
					**kwargs,
				)
			)

def upload_dataset(name: str, version: str, path: str) -> FileDatasetVersion:
    client = AIProjectClient(endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=DefaultAzureCredential())
    return client.datasets.upload_file(name=name, version=version, file_path=path)

def list_datasets() -> list[FileDatasetVersion]:
    client = AIProjectClient(endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=DefaultAzureCredential())
    return list(client.datasets.list())

def delete_dataset(name: str, version: str) -> None:
    client = AIProjectClient(endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=DefaultAzureCredential())
    client.datasets.delete(name=name, version=version)

def get_dataset(name: str, version: str) -> FileDatasetVersion:
    client = AIProjectClient(endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=DefaultAzureCredential())
    return client.datasets.get(name=name, version=version)

def main() -> None:
	parser = argparse.ArgumentParser()
	commands = parser.add_subparsers(dest="command", required=True)

	create_command = commands.add_parser("create-generation-job")
	create_command.add_argument("-f", "--definition", type=Path, required=True)
	create_command.add_argument("--operation-id")

	get_command = commands.add_parser("get-generation-job")
	get_command.add_argument("-j", "--job-id", required=True)

	list_command = commands.add_parser("list-generation-jobs")
	list_command.add_argument("--limit", type=int)
	list_command.add_argument("--order", choices=("asc", "desc"))
	list_command.add_argument("--before")

	cancel_command = commands.add_parser("cancel-generation-job")
	cancel_command.add_argument("-j", "--job-id", required=True)

	delete_command = commands.add_parser("delete-generation-job")
	delete_command.add_argument("-j", "--job-id", required=True)

	upload_command = commands.add_parser("upload-dataset")
	upload_command.add_argument("-n", "--name", required=True)
	upload_command.add_argument("-v", "--version", required=True)
	upload_command.add_argument("-p", "--path", required=True)

	list_datasets_command = commands.add_parser("list-datasets")

	get_dataset_command = commands.add_parser("get-dataset")
	get_dataset_command.add_argument("-n", "--name", required=True)
	get_dataset_command.add_argument("-v", "--version", required=True)

	delete_dataset_command = commands.add_parser("delete-dataset")
	delete_dataset_command.add_argument("-n", "--name", required=True)
	delete_dataset_command.add_argument("-v", "--version", required=True)

	args = parser.parse_args()

	try:
		if args.command == "create-generation-job":
			definition = json.loads(
				args.definition.read_text(encoding="utf-8")
			)
			job = DataGenerationJob(definition)
			print(
				create_generation_job(
					job,
					operation_id=args.operation_id,
				).result()
			)

		elif args.command == "get-generation-job":
			print(get_generation_job(args.job_id))

		elif args.command == "list-generation-jobs":
			for job in list_generation_jobs(
				limit=args.limit,
				order=args.order,
				before=args.before,
			):
				print(job)

		elif args.command == "cancel-generation-job":
			print(cancel_generation_job(args.job_id))

		elif args.command == "delete-generation-job":
			delete_generation_job(args.job_id)
			print(f"Deleted generation job {args.job_id}")

		elif args.command == "upload-dataset":
			dataset_version = upload_dataset(args.name, args.version, args.path)
			print(f"Uploaded dataset {dataset_version.name} version {dataset_version.version}")

		elif args.command == "list-datasets":
			for dataset in list_datasets():
				print(dataset)

		elif args.command == "get-dataset":
			dataset_version = get_dataset(args.name, args.version)
			print(f"Dataset {dataset_version.name} version {dataset_version.version}")

		elif args.command == "delete-dataset":
			delete_dataset(args.name, args.version)
			print(f"Deleted dataset {args.name} version {args.version}")
		else:
			raise ValueError(
				f"Unsupported dataset command: {args.command}"
			)
	except Exception:
		logger.exception(
			"Dataset command failed command=%s",
			args.command,
		)
		raise SystemExit(1)


if __name__ == "__main__":
	main()