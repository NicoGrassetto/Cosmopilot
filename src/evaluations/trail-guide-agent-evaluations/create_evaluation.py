
import os

from evaluations.datasets import upload_dataset
from evaluations import rules

from azure.identity import DefaultAzureCredential

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    ContinuousEvaluationRuleAction,
    EvaluationRule,
    EvaluationRuleEventType,
    EvaluationRuleFilter,
)
from azure.ai.projects.models import (
        AzureAIDataSourceConfig,
        TestingCriterionAzureAIEvaluator,
)

def main() -> None:
    ###############################
    ######## DATASET STUFF ########
    ###############################
    dataset = upload_dataset(
        name="trail-guide-evaluation",
        version="1",
        path="data/trail_guide/datasets/evaluation_dataset.jsonl",
    )

    print(dataset)

    ############################
    ##### EVALUATION STUFF #####
    ############################
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=credential,
        ) as project_client,
        project_client.get_openai_client() as openai_client,
    ):
        evaluation = openai_client.evals.create(
            name="Trail Guide Continuous Quality",
            data_source_config=AzureAIDataSourceConfig(
                type="azure_ai_source",
                scenario="responses",
            ),
            testing_criteria=[
                TestingCriterionAzureAIEvaluator(
                    type="azure_ai_evaluator",
                    name="intent_resolution",
                    evaluator_name="builtin.intent_resolution",
                    initialization_parameters={
                        "deployment_name": os.environ["AZURE_DEPLOYMENT_NAME"],
                    },
                    data_mapping={
                        "query": "{{item.query}}",
                        "response": "{{sample.output_items}}",
                    },
                ),
                TestingCriterionAzureAIEvaluator(
                    type="azure_ai_evaluator",
                    name="relevance",
                    evaluator_name="builtin.relevance",
                    initialization_parameters={
                        "deployment_name": os.environ["AZURE_DEPLOYMENT_NAME"],
                    },
                    data_mapping={
                        "query": "{{item.query}}",
                        "response": "{{sample.output_text}}",
                    },
                ),
                TestingCriterionAzureAIEvaluator(
                    type="azure_ai_evaluator",
                    name="groundedness",
                    evaluator_name="builtin.groundedness",
                    initialization_parameters={
                        "deployment_name": os.environ["AZURE_DEPLOYMENT_NAME"],
                    },
                    data_mapping={
                        "query": "{{item.query}}",
                        "response": "{{sample.output_items}}",
                    },
                ),
            ],
        )

    print(f"Created evaluation {evaluation.id}")

    ################################
    ########## RULE STUFF ##########
    ################################
    SAMPLING_RATE = 100  # each matching response has a n% chance of being evaluated
    MAX_HOURLY_RUNS = 20  # no more than 20 evaluation runs can start per hour, even when sampling selects more.
    
    created_rule = rules.create_or_update(
        rule_id="trail-guide-agent-continuous-quality",
        evaluation_rule=EvaluationRule(
            display_name="Trail guide continuous quality",
            description="Samples completed trail-guide responses.",
            action=ContinuousEvaluationRuleAction(
                eval_id=evaluation.id,
                sampling_rate=SAMPLING_RATE,
                max_hourly_runs=MAX_HOURLY_RUNS,
            ),
            event_type=EvaluationRuleEventType.RESPONSE_COMPLETED, # or EvaluationRuleEventType.MANUAL
            filter=EvaluationRuleFilter(
                agent_name="trail-guide-agent",
            ),
            enabled=True,
        ),
    )

    print(created_rule)
    
    ##############################################
    ########## SCHEDULE STUFF (offline) ##########
    ##############################################

    #######################################
    ########## RED TEAMING STUFF ##########
    #######################################

if __name__ == "__main__":
    main()