"""
General Purpose Evaluators: Coherence and Fluency

Measures writing quality of AI-generated text independent of factual correctness.
- Coherence: Logical flow and organization of ideas (1-5 scale)
- Fluency: Grammatical accuracy and readability (1-5 scale)
"""
import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

load_dotenv()

project_client = AIProjectClient(
    endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential(),
)

model_deployment = os.getenv("MODEL_NAME", "gpt-5.1")

testing_criteria = [
    {
        "type": "azure_ai_evaluator",
        "name": "coherence",
        "evaluator_name": "builtin.coherence",
        "initialization_parameters": {"deployment_name": model_deployment},
        "data_mapping": {"query": "{{item.query}}", "response": "{{item.response}}"},
    },
    {
        "type": "azure_ai_evaluator",
        "name": "fluency",
        "evaluator_name": "builtin.fluency",
        "initialization_parameters": {"deployment_name": model_deployment},
        "data_mapping": {"response": "{{item.response}}"},
    },
]

# Sample test data
test_data = [
    {"query": "What gear do I need for a day hike in the Scottish Highlands in March?", "response": ""},
    {"query": "Recommend family-friendly trails near London for teenagers.", "response": ""},
]

if __name__ == "__main__":
    print("General Purpose Evaluators configured:")
    for criteria in testing_criteria:
        print(f"  - {criteria['name']} ({criteria['evaluator_name']})")
    print("\nRun these evaluators via the SDK or Foundry portal with your agent responses.")
