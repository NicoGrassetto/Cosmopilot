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

import os
from typing import Any, Callable, Literal, TypeVar

import azure.ai.projects.models as models
from azure.ai.projects import AIProjectClient
from azure.ai.projects.operations import BetaEvaluatorsOperations
from azure.identity import DefaultAzureCredential

def create_evaluator_version(
    name: str,
    value: models.EvaluatorVersion,
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
            evaluator_version=value,
            **kwargs,
        )

def get_evaluator_version():
    pass

def list_evaluators():
    pass

def list_evaluator_versions():
    pass

def update_evaluator_version():
    pass

def delete_evaluator_version():
    pass