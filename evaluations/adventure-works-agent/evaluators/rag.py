"""
RAG (Retrieval-Augmented Generation) Evaluators

Measures retrieval quality and groundedness of responses.
- Retrieval: Effectiveness of information retrieval
- Document Retrieval: Accuracy of retrieval results given ground truth
- Groundedness: How grounded the response is in retrieved context (1-5 scale)
- Groundedness Pro: Binary pass/fail grounding check via Azure AI Content Safety
- Relevance: How relevant the response is to the query (1-5 scale)
- Response Completeness: Whether the response covers all critical information
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
        "name": "retrieval",
        "evaluator_name": "builtin.retrieval",
        "initialization_parameters": {"deployment_name": model_deployment},
        "data_mapping": {
            "query": "{{item.query}}",
            "context": "{{item.context}}",
            "response": "{{item.response}}",
        },
    },
    {
        "type": "azure_ai_evaluator",
        "name": "document_retrieval",
        "evaluator_name": "builtin.document_retrieval",
        "initialization_parameters": {},
        "data_mapping": {
            "query": "{{item.query}}",
            "context": "{{item.context}}",
            "ground_truth": "{{item.ground_truth}}",
        },
    },
    {
        "type": "azure_ai_evaluator",
        "name": "groundedness",
        "evaluator_name": "builtin.groundedness",
        "initialization_parameters": {"deployment_name": model_deployment},
        "data_mapping": {
            "query": "{{item.query}}",
            "context": "{{item.context}}",
            "response": "{{item.response}}",
        },
    },
    {
        "type": "azure_ai_evaluator",
        "name": "groundedness_pro",
        "evaluator_name": "builtin.groundedness_pro",
        "initialization_parameters": {},
        "data_mapping": {
            "query": "{{item.query}}",
            "context": "{{item.context}}",
            "response": "{{item.response}}",
        },
    },
    {
        "type": "azure_ai_evaluator",
        "name": "relevance",
        "evaluator_name": "builtin.relevance",
        "initialization_parameters": {"deployment_name": model_deployment},
        "data_mapping": {
            "query": "{{item.query}}",
            "response": "{{item.response}}",
        },
    },
    {
        "type": "azure_ai_evaluator",
        "name": "response_completeness",
        "evaluator_name": "builtin.response_completeness",
        "initialization_parameters": {"deployment_name": model_deployment},
        "data_mapping": {
            "query": "{{item.query}}",
            "response": "{{item.response}}",
            "ground_truth": "{{item.ground_truth}}",
        },
    },
]

# Sample test data
test_data = [
    {
        "query": "What gear do I need for a day hike in the Scottish Highlands in March?",
        "context": "Adventure Works recommends waterproof jackets, hiking boots, layered clothing, OS maps, and emergency whistle for Scottish Highland hikes in spring.",
        "response": "For a March day hike in the Highlands, you'll need a waterproof jacket, sturdy hiking boots, layered clothing, and navigation tools.",
        "ground_truth": "Essential gear includes waterproof jacket and trousers, hiking boots, warm layers, OS map, compass, whistle, headtorch, and first aid kit.",
    },
]

if __name__ == "__main__":
    print("RAG Evaluators configured:")
    for criteria in testing_criteria:
        print(f"  - {criteria['name']} ({criteria['evaluator_name']})")
    print("\nRun these evaluators via the SDK or Foundry portal with your agent responses.")
