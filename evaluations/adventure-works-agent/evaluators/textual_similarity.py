"""
Textual Similarity Evaluators

Measures overlap and similarity between generated responses and ground truth.
- Similarity: AI-assisted textual similarity
- F1 Score: Harmonic mean of precision and recall in token overlaps
- BLEU: Bilingual Evaluation Understudy for n-gram overlap
- GLEU: Google-BLEU variant for sentence-level assessment
- ROUGE: Recall-Oriented Understudy for Gisting Evaluation
- METEOR: Metric for Evaluation of Translation with Explicit Ordering
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
        "name": "similarity",
        "evaluator_name": "builtin.similarity",
        "initialization_parameters": {"deployment_name": model_deployment},
        "data_mapping": {"response": "{{item.response}}", "ground_truth": "{{item.ground_truth}}"},
    },
    {
        "type": "azure_ai_evaluator",
        "name": "f1_score",
        "evaluator_name": "builtin.f1_score",
        "initialization_parameters": {},
        "data_mapping": {"response": "{{item.response}}", "ground_truth": "{{item.ground_truth}}"},
    },
    {
        "type": "azure_ai_evaluator",
        "name": "bleu",
        "evaluator_name": "builtin.bleu",
        "initialization_parameters": {},
        "data_mapping": {"response": "{{item.response}}", "ground_truth": "{{item.ground_truth}}"},
    },
    {
        "type": "azure_ai_evaluator",
        "name": "gleu",
        "evaluator_name": "builtin.gleu",
        "initialization_parameters": {},
        "data_mapping": {"response": "{{item.response}}", "ground_truth": "{{item.ground_truth}}"},
    },
    {
        "type": "azure_ai_evaluator",
        "name": "rouge",
        "evaluator_name": "builtin.rouge",
        "initialization_parameters": {},
        "data_mapping": {"response": "{{item.response}}", "ground_truth": "{{item.ground_truth}}"},
    },
    {
        "type": "azure_ai_evaluator",
        "name": "meteor",
        "evaluator_name": "builtin.meteor",
        "initialization_parameters": {},
        "data_mapping": {"response": "{{item.response}}", "ground_truth": "{{item.ground_truth}}"},
    },
]

# Sample test data with ground truth
test_data = [
    {
        "response": "For a March hike in the Scottish Highlands, bring waterproof layers, sturdy boots, and a map.",
        "ground_truth": "Essential gear for March hiking in Scotland includes waterproof jacket and trousers, hiking boots with ankle support, an OS map, and warm layers.",
    },
]

if __name__ == "__main__":
    print("Textual Similarity Evaluators configured:")
    for criteria in testing_criteria:
        print(f"  - {criteria['name']} ({criteria['evaluator_name']})")
    print("\nRun these evaluators via the SDK or Foundry portal with your agent responses.")
