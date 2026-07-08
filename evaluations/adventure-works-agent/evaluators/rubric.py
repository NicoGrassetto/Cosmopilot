"""
Rubric Evaluator

Scores a response or multi-turn conversation against custom, weighted criteria
using an LLM as the judge. Returns a weighted average score normalized to 0-1
with per-dimension reasoning.

Define your own dimensions, weights, and scoring criteria tailored to the
Adventure Works trail guide use case.
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

# Custom rubric for the Adventure Works trail guide agent
rubric_criteria = {
    "safety_emphasis": {
        "weight": 0.3,
        "description": "Does the response prioritize hiker safety with appropriate warnings and precautions?",
        "scoring": {
            "5": "Proactively identifies all relevant safety concerns with specific, actionable precautions.",
            "4": "Addresses major safety concerns with reasonable precautions.",
            "3": "Mentions safety but lacks specificity or misses important concerns.",
            "2": "Minimal safety awareness, missing critical safety information.",
            "1": "No safety considerations mentioned despite obvious risks.",
        },
    },
    "actionability": {
        "weight": 0.25,
        "description": "Are the recommendations specific and actionable enough to follow?",
        "scoring": {
            "5": "Provides precise, step-by-step guidance that can be immediately acted upon.",
            "4": "Mostly specific and actionable with minor gaps.",
            "3": "Mix of specific and vague advice.",
            "2": "Mostly generic advice that requires significant further research.",
            "1": "Completely generic, no actionable information.",
        },
    },
    "personalization": {
        "weight": 0.2,
        "description": "Does the response tailor advice to the user's stated experience, constraints, and preferences?",
        "scoring": {
            "5": "Fully customized to user's experience level, time constraints, group composition, and stated preferences.",
            "4": "Good personalization with minor oversights.",
            "3": "Some personalization but also includes generic advice.",
            "2": "Minimal personalization, mostly one-size-fits-all.",
            "1": "No personalization at all despite user providing relevant details.",
        },
    },
    "gear_relevance": {
        "weight": 0.15,
        "description": "Are gear recommendations appropriate for the conditions and activity described?",
        "scoring": {
            "5": "All gear suggestions are perfectly suited to conditions, season, and activity level.",
            "4": "Gear recommendations are appropriate with minor omissions.",
            "3": "Some gear is relevant, but important items are missing or unnecessary items included.",
            "2": "Gear recommendations are mostly inappropriate for the described scenario.",
            "1": "No gear recommendations or completely wrong suggestions.",
        },
    },
    "completeness": {
        "weight": 0.1,
        "description": "Does the response address all aspects of the user's question?",
        "scoring": {
            "5": "Addresses every aspect of the query comprehensively.",
            "4": "Addresses most aspects with minor omissions.",
            "3": "Addresses the main question but misses secondary aspects.",
            "2": "Only partially addresses the query.",
            "1": "Fails to address the core question.",
        },
    },
}

testing_criteria = [
    {
        "type": "azure_ai_evaluator",
        "name": "rubric",
        "evaluator_name": "builtin.rubric",
        "initialization_parameters": {
            "deployment_name": model_deployment,
            "rubric": rubric_criteria,
        },
        "data_mapping": {
            "query": "{{item.query}}",
            "response": "{{item.response}}",
        },
    },
]

# Sample test data
test_data = [
    {
        "query": "I'm a digital nomad looking to do a weekend hike in the Scottish Highlands in March. I have moderate fitness and some hiking experience.",
        "response": "For a March weekend in the Highlands, I'd recommend Ben A'an (moderate, 5km round trip) for stunning views with manageable difficulty. Pack waterproof jacket and trousers, warm layers, sturdy boots, and a headtorch. March weather is unpredictable -- expect rain and wind. Check the Mountain Weather Information Service before heading out and let someone know your route.",
    },
]

if __name__ == "__main__":
    print("Rubric Evaluator configured with custom dimensions:")
    for dim, config in rubric_criteria.items():
        print(f"  - {dim} (weight: {config['weight']}): {config['description']}")
    print("\nRun via the SDK or Foundry portal with your agent responses.")
