# from openai.types.eval_create_params import DataSourceConfigCustom
# import os
# from azure.identity import DefaultAzureCredential
# from azure.ai.projects import AIProjectClient

# with (
#     DefaultAzureCredential() as credential,
#     AIProjectClient(
#         endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
#         credential=credential,
#     ) as project_client
# ):
#     dataset_id = project_client.datasets.upload_file(
#         name="adventure_works_evaluation",
#         file_path=""
#     )
# data_source_config = DataSourceConfigCustom(
#     type="custom",
#     item_schema={
#         "type": "object",
#         "properties": {
#             "query": {"type": "string"},
#             "response": {"type": "string"},
#             "context": {"type": "string"},
#             "ground_truth": {"type": "string"},
#         },
#         "required": ["query", "response", "ground_truth"],
#     },
# )

# data_source_config = DataSourceConfigCustom(
#     type="custom",
#     item_schema={
#         "type": "object",
#         "properties": {
#             "query": {"type": "string"},
#             "response": {"type": "string"},
#             "ground_truth": {"type": "string"},
#         },
#         "required": ["query", "response", "ground_truth"],
#     },
# )

# testing_criteria = [
#     {
#         "type": "azure_ai_evaluator",
#         "name": "intent_resolution",
#         "evaluator_name": "builtin.intent_resolution",
#         "initialization_parameters": {
#             "deployment_name": model_deployment_name,
#         },
#         "data_mapping": {
#             "query": "{{item.query}}",
#             "response": "{{item.response}}",
#         },
#     },
#     {
#         "type": "azure_ai_evaluator",
#         "name": "relevance",
#         "evaluator_name": "builtin.relevance",
#         "initialization_parameters": {
#             "deployment_name": model_deployment_name,
#         },
#         "data_mapping": {
#             "query": "{{item.query}}",
#             "response": "{{item.response}}",
#         },
#     },
#     {
#         "type": "azure_ai_evaluator",
#         "name": "groundedness",
#         "evaluator_name": "builtin.groundedness",
#         "initialization_parameters": {
#             "deployment_name": model_deployment_name,
#         },
#         "data_mapping": {
#             "query": "{{item.query}}",
#             "response": "{{item.response}}",
#             "context": "{{item.ground_truth}}",
#         },
#     },
# ]
