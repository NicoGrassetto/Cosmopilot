# # import os
# # import sys

# # from azure.ai.projects.models import TestingCriterionAzureAIEvaluator
# # from openai.types.eval_create_params import DataSourceConfigCustom

# # from src.evaluations.evals import register_eval


# # PREFIX = "eu-resilience-agent"

# # MODEL_DEPLOYMENT = os.environ["AZURE_DEPLOYMENT_NAME"]


# # custom_data_source_config: DataSourceConfigCustom = {
# #     "type": "custom",
# #     "item_schema": {
# #         "type": "object",
# #         "properties": {
# #             "question": {"type": "string"},
# #             "answer": {"type": "string"},
# #         },
# #         "required": ["question", "answer"],
# #     },
# #     "include_sample_schema": True,
# # }

# # criteria = [
# #     TestingCriterionAzureAIEvaluator(
# #         type="azure_ai_evaluator",
# #         name="coherence",
# #         evaluator_name="builtin.coherence",
# #         initialization_parameters={"model": MODEL_DEPLOYMENT},
# #         data_mapping={
# #             "query": "{{item.question}}",
# #             "response": "{{item.answer}}",
# #         },
# #     ),
# #     TestingCriterionAzureAIEvaluator(
# #         type="azure_ai_evaluator",
# #         name="relevance",
# #         evaluator_name="builtin.relevance",
# #         initialization_parameters={"model": MODEL_DEPLOYMENT},
# #         data_mapping={
# #             "query": "{{item.question}}",
# #             "response": "{{item.answer}}",
# #         },
# #     ),
# # ]

# # register_eval(
# #     name=f"{PREFIX}-turn-response-quality-v1",
# #     data_source_config=custom_data_source_config,
# #     testing_criteria=criteria,
# # )

# # def main() -> None:
# #     evaluation_type = sys.argv[1]

# #     if evaluation_type == "test":
# #         register_eval(
# #             name=f"{PREFIX}-test-quality",
# #             data_source_config=custom_data_source_config,
# #             testing_criteria=criteria,
# #         )
# #     else:
# #         raise SystemExit(f"Unknown type: {evaluation_type}")


# # if __name__ == "__main__":
# #     main()


# ### ONLINE EVALUATION ###
# from azure.ai.projects.models import (
#     ContinuousEvaluationRuleAction,
#     EvaluationRule,
#     EvaluationRuleEventType,
#     EvaluationRuleFilter,
# )
# from evaluations import rules

# evaluation_id = "<ID returned when the evaluation was registered>"

# created_rule = rules.create_or_update(
#     rule_id="eu-resilience-agent-continuous-quality",
#     evaluation_rule=EvaluationRule(
#         display_name="EU resilience agent continuous quality",
#         description="Samples completed EU resilience agent responses.",
#         action=ContinuousEvaluationRuleAction(
#             eval_id=evaluation_id,
#             sampling_rate=5,
#             max_hourly_runs=20,
#         ),
#         event_type=EvaluationRuleEventType.RESPONSE_COMPLETED,
#         filter=EvaluationRuleFilter(
#             agent_name="eu-resilience-agent",
#         ),
#         enabled=True,
#     ),
# )

# print(created_rule)

