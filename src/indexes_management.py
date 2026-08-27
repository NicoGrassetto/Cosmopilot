from __future__ import annotations

import argparse
import json
import logging
import os
from collections.abc import MutableMapping
from pathlib import Path
from typing import IO, Any

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import Index
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)


def create_or_update_index(
	name: str,
	version: str,
	index: Index,
) -> Index:
	with (
		DefaultAzureCredential() as credential,
		AIProjectClient(
			endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
			credential=credential,
		) as client,
	):
		return client.indexes.create_or_update(
			name=name,
			version=version,
			index=index,
		)


def get_index(name: str, version: str) -> Index:
	with (
		DefaultAzureCredential() as credential,
		AIProjectClient(
			endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
			credential=credential,
		) as client,
	):
		return client.indexes.get(name=name, version=version)


def list_indexes() -> list[Index]:
	with (
		DefaultAzureCredential() as credential,
		AIProjectClient(
			endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
			credential=credential,
		) as client,
	):
		return list(client.indexes.list())


def list_index_versions(name: str) -> list[Index]:
	with (
		DefaultAzureCredential() as credential,
		AIProjectClient(
			endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
			credential=credential,
		) as client,
	):
		return list(client.indexes.list_versions(name=name))


def delete_index(name: str, version: str) -> None:
	with (
		DefaultAzureCredential() as credential,
		AIProjectClient(
			endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
			credential=credential,
		) as client,
	):
		client.indexes.delete(name=name, version=version)


def main() -> None:
	parser = argparse.ArgumentParser(
		description="Manage versioned Microsoft Foundry index assets.",
	)
	commands = parser.add_subparsers(dest="command", required=True)

	create_command = commands.add_parser("create-or-update")
	create_command.add_argument("-n", "--name", required=True)
	create_command.add_argument("-v", "--version", required=True)
	create_command.add_argument(
		"-i",
		"--index",
		type=Path,
		required=True,
		help="Path to a serialized Index JSON object.",
	)

	get_command = commands.add_parser("get")
	get_command.add_argument("-n", "--name", required=True)
	get_command.add_argument("-v", "--version", required=True)

	commands.add_parser("list")

	list_versions_command = commands.add_parser("list-versions")
	list_versions_command.add_argument("-n", "--name", required=True)

	delete_command = commands.add_parser("delete")
	delete_command.add_argument("-n", "--name", required=True)
	delete_command.add_argument("-v", "--version", required=True)

	args = parser.parse_args()

	try:
		if args.command == "create-or-update":
			index = json.loads(args.index.read_text(encoding="utf-8"))
			output = create_or_update_index(
				args.name,
				args.version,
				index,
			).as_dict()

		elif args.command == "get":
			output = get_index(args.name, args.version).as_dict()

		elif args.command == "list":
			output = [index.as_dict() for index in list_indexes()]

		elif args.command == "list-versions":
			output = [
				index.as_dict()
				for index in list_index_versions(args.name)
			]

		elif args.command == "delete":
			delete_index(args.name, args.version)
			output = {
				"name": args.name,
				"version": args.version,
				"deleted": True,
			}

		else:
			raise AssertionError(f"Unhandled command: {args.command}")

		print(json.dumps(output, indent=2, default=str))
	except Exception:
		logger.exception("Index command failed command=%s", args.command)
		raise SystemExit(1)


if __name__ == "__main__":
	logging.basicConfig(
		level=logging.INFO,
		format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
	)
	main()
