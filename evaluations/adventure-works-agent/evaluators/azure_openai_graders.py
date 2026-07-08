"""
Azure OpenAI Graders

Custom evaluation using Azure OpenAI models as judges.
- Model Labeler: Classifies content using custom guidelines and labels
- String Checker: Performs flexible text validations and pattern matching
- Text Similarity: Evaluates semantic closeness of text
- Model Scorer: Generates numerical scores for content based on custom guidelines
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
        "type": "azure_openai_grader",
        "name": "response_tone_labeler",
        "grader_type": "model_labeler",
        "initialization_parameters": {"deployment_name": model_deployment},
        "guidelines": "Classify the tone of the trail guide's response.",
        "labels": ["professional", "friendly", "overly_casual", "too_formal"],
        "data_mapping": {"response": "{{item.response}}"},
    },
    {
        "type": "azure_openai_grader",
        "name": "safety_mention_check",
        "grader_type": "string_checker",
        "check_type": "contains_any",
        "values": ["safety", "caution", "warning", "careful", "risk", "emergency", "first aid"],
        "data_mapping": {"response": "{{item.response}}"},
    },
    {
        "type": "azure_openai_grader",
        "name": "response_similarity",
        "grader_type": "text_similarity",
        "initialization_parameters": {"deployment_name": model_deployment},
        "data_mapping": {
            "response": "{{item.response}}",
            "reference": "{{item.ground_truth}}",
        },
    },
    {
        "type": "azure_openai_grader",
        "name": "trail_guide_quality_scorer",
        "grader_type": "model_scorer",
        "initialization_parameters": {"deployment_name": model_deployment},
        "guidelines": "Score the trail guide response on a scale of 1-10 based on: (1) safety awareness, (2) specificity of trail/gear recommendations, (3) personalization to the user's stated needs, (4) appropriate level of detail.",
        "score_range": {"min": 1, "max": 10},
        "data_mapping": {"query": "{{item.query}}", "response": "{{item.response}}"},
    },
]

# Sample test data
test_data = [
    {
        "query": "What gear do I need for a day hike?",
        "response": "For a day hike, bring water (at least 2L), snacks, a waterproof jacket, sturdy boots, sunscreen, a map, and a basic first aid kit. Always tell someone your planned route for safety.",
        "ground_truth": "Essential day hike gear: water, food, navigation tools, sun protection, first aid, rain gear, proper footwear, and a backpack to carry it all.",
    },
]

if __name__ == "__main__":
    print("Azure OpenAI Graders configured:")
    for criteria in testing_criteria:
        print(f"  - {criteria['name']} ({criteria['grader_type']})")
    print("\nRun these graders via the SDK or Foundry portal with your agent responses.")
