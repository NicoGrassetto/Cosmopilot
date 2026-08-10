# import os
# from typing import Any, Awaitable, Callable

# from azure.ai.projects import AIProjectClient
# from azure.ai.projects.models import FileDatasetVersion
# from azure.identity import DefaultAzureCredential

# from azure.ai.evaluation.simulator import (
#     AdversarialScenario,
#     DirectAttackSimulator,
#     IndirectAttackSimulator,
#     Simulator,
# )

# SimulationTarget = Callable[..., Awaitable[dict[str, Any]]]



# def register_eval(name: str, data_source_config: dict, testing_criteria: list):
#     client = AIProjectClient(endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=DefaultAzureCredential())
#     return client.get_openai_client().evals.create(name=name, data_source_config=data_source_config, testing_criteria=testing_criteria)

# def list_evals():
#     client = AIProjectClient(endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=DefaultAzureCredential())
#     return list(client.get_openai_client().evals.list())

# def delete_eval(eval_id: str):
#     client = AIProjectClient(endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=DefaultAzureCredential())
#     return client.get_openai_client().evals.delete(eval_id=eval_id)

# def get_eval(eval_id: str):
#     client = AIProjectClient(endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=DefaultAzureCredential())
#     return client.get_openai_client().evals.retrieve(eval_id=eval_id)

# async def simulate_direct_attack_dataset(
#     target: SimulationTarget,
#     max_simulation_results: int = 10,
#     max_conversation_turns: int = 3,
# ):
#     simulator = DirectAttackSimulator(
#         azure_ai_project=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
#         credential=DefaultAzureCredential(),
#     )

#     return await simulator(
#         target=target,
#         scenario=AdversarialScenario.ADVERSARIAL_CONVERSATION,
#         max_simulation_results=max_simulation_results,
#         max_conversation_turns=max_conversation_turns,
#     )

# async def simulate_indirect_attack_dataset(
#     target: SimulationTarget,
#     max_simulation_results: int = 10,
#     max_conversation_turns: int = 3,
# ):
#     simulator = IndirectAttackSimulator(
#         azure_ai_project=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
#         credential=DefaultAzureCredential(),
#     )

#     return await simulator(
#         target=target,
#         max_simulation_results=max_simulation_results,
#         max_conversation_turns=max_conversation_turns,
#     )

# async def generate_synthetic_dataset(
#     target: SimulationTarget,
#     text: str,
#     tasks: list[str],
#     num_queries: int = 10,
#     max_conversation_turns: int = 3,
# ):
#     model_config = {
#         "azure_endpoint": os.environ["AZURE_OPENAI_ENDPOINT"],
#         "azure_deployment": os.environ["AZURE_DEPLOYMENT_NAME"],
#         "api_version": os.environ.get(
#             "AZURE_OPENAI_API_VERSION",
#             "2024-12-01-preview",
#         ),
#     }

#     simulator = Simulator(model_config=model_config)
#     return await simulator(
#         target=target,
#         text=text,
#         tasks=tasks,
#         num_queries=num_queries,
#         max_conversation_turns=max_conversation_turns,
#     )


from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any

import azure.ai.projects.models as models
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)

def create_evaluator_version(
    name: str,
    evaluator_version: models.EvaluatorVersion,
    *,
    content_type: str = "application/json",
    **kwargs: Any,
) -> models.EvaluatorVersion:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return client.beta.evaluators.create_version(
            name=name,
            evaluator_version=evaluator_version,
            content_type=content_type,
            **kwargs,
        )

def get_evaluator_version(
    name: str,
    version: str,
    **kwargs: Any,
) -> models.EvaluatorVersion:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return client.beta.evaluators.get_version(
            name=name,
            version=version,
            **kwargs,
        )

def list_evaluators(
    *,
    evaluator_type: str | None = None,
    limit: int | None = None,
    **kwargs: Any,
) -> list[models.EvaluatorVersion]:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return list(
            client.beta.evaluators.list(
                type=evaluator_type,
                limit=limit,
                **kwargs,
            )
        )

def list_evaluator_versions(
    name: str,
    *,
    evaluator_type: str | None = None,
    limit: int | None = None,
    **kwargs: Any,
) -> list[models.EvaluatorVersion]:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return list(
            client.beta.evaluators.list_versions(
                name=name,
                type=evaluator_type,
                limit=limit,
                **kwargs,
            )
        )

def update_evaluator_version(
    name: str,
    version: str,
    evaluator_version: models.EvaluatorVersion,
    *,
    content_type: str = "application/json",
    **kwargs: Any,
) -> models.EvaluatorVersion:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        return client.beta.evaluators.update_version(
            name=name,
            version=version,
            evaluator_version=evaluator_version,
            content_type=content_type,
            **kwargs,
        )

def delete_evaluator_version(
    name: str,
    version: str,
    **kwargs: Any,
) -> None:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as client,
    ):
        client.beta.evaluators.delete_version(
            name=name,
            version=version,
            **kwargs,
        )

def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)

    create_command = commands.add_parser("create")
    create_command.add_argument("-n", "--name", required=True)
    create_command.add_argument(
        "-f", "--definition", type=Path, required=True
    )

    get_command = commands.add_parser("get")
    get_command.add_argument("-n", "--name", required=True)
    get_command.add_argument("-v", "--version", required=True)

    list_evaluators_command = commands.add_parser("list-evaluators")
    list_evaluators_command.add_argument(
        "--type",
        dest="evaluator_type",
        choices=("all", "builtin", "custom"),
    )
    list_evaluators_command.add_argument("--limit", type=int)

    list_versions_command = commands.add_parser("list-versions")
    list_versions_command.add_argument("-n", "--name", required=True)
    list_versions_command.add_argument(
        "--type",
        dest="evaluator_type",
        choices=("all", "builtin", "custom"),
    )
    list_versions_command.add_argument("--limit", type=int)

    update_command = commands.add_parser("update")
    update_command.add_argument("-n", "--name", required=True)
    update_command.add_argument("-v", "--version", required=True)
    update_command.add_argument(
        "-f", "--definition", type=Path, required=True
    )

    delete_command = commands.add_parser("delete")
    delete_command.add_argument("-n", "--name", required=True)
    delete_command.add_argument("-v", "--version", required=True)

    args = parser.parse_args()

    try:
        if args.command == "create":
            definition = json.loads(
                args.definition.read_text(encoding="utf-8")
            )
            print(
                create_evaluator_version(
                    name=args.name,
                    evaluator_version=models.EvaluatorVersion(definition),
                )
            )

        elif args.command == "get":
            print(
                get_evaluator_version(
                    name=args.name,
                    version=args.version,
                )
            )

        elif args.command == "list-evaluators":
            for evaluator in list_evaluators(
                evaluator_type=args.evaluator_type,
                limit=args.limit,
            ):
                print(evaluator)

        elif args.command == "list-versions":
            for evaluator in list_evaluator_versions(
                name=args.name,
                evaluator_type=args.evaluator_type,
                limit=args.limit,
            ):
                print(evaluator)

        elif args.command == "update":
            definition = json.loads(
                args.definition.read_text(encoding="utf-8")
            )
            print(
                update_evaluator_version(
                    name=args.name,
                    version=args.version,
                    evaluator_version=models.EvaluatorVersion(definition),
                )
            )

        elif args.command == "delete":
            delete_evaluator_version(
                name=args.name,
                version=args.version,
            )
            print(
                f"Deleted evaluator {args.name} version {args.version}"
            )
        else:
            raise ValueError(
                f"Unsupported evaluator command: {args.command}"
            )
    except Exception:
        logger.exception(
            "Evaluator command failed command=%s",
            args.command,
        )
        raise SystemExit(1)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    )
    main()

# def pending_upload():
#     pass

# def get_credentials():
#     pass