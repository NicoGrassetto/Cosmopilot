"""
Agent Evaluators

Measures agent task execution quality, tool usage, and overall performance.

System evaluation (end-to-end outcomes):
- Task Adherence: Agent follows system instructions and constraints
- Task Completion: Agent successfully completed the requested task
- Customer Satisfaction: Holistic user satisfaction (1-5 scale, 6 dimensions)
- Intent Resolution: Agent correctly identifies and addresses user intentions
- Task Navigation Efficiency: Agent's steps match optimal/expected path

Process evaluation (step-by-step execution):
- Tool Call Accuracy: Overall quality of tool calls
- Tool Selection: Agent selected the most appropriate tools
- Tool Input Accuracy: All tool call parameters are correct
- Tool Output Utilization: Agent correctly uses tool outputs in responses
- Tool Call Success: All tool calls executed without technical failures

Quality evaluation:
- Quality Grader: Multi-dimensional quality scoring in a single evaluator
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

# Tool definitions for the Adventure Works trail guide agent
tool_definitions = [
    {
        "type": "function",
        "function": {
            "name": "search_trails",
            "description": "Search for hiking trails by location, difficulty, and distance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "Geographic area to search."},
                    "difficulty": {"type": "string", "enum": ["easy", "moderate", "hard"], "description": "Trail difficulty level."},
                    "max_distance_km": {"type": "number", "description": "Maximum trail distance in kilometers."},
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current and forecast weather for a location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "Location to get weather for."},
                    "days": {"type": "integer", "description": "Number of forecast days (1-7)."},
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recommend_gear",
            "description": "Recommend gear from Adventure Works catalog based on activity and conditions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "activity": {"type": "string", "description": "Type of outdoor activity."},
                    "conditions": {"type": "string", "description": "Expected weather/terrain conditions."},
                    "experience_level": {"type": "string", "enum": ["beginner", "intermediate", "advanced"], "description": "User experience level."},
                },
                "required": ["activity", "conditions"],
            },
        },
    },
]

# --- System Evaluators ---
system_evaluators = [
    {
        "type": "azure_ai_evaluator",
        "name": "task_adherence",
        "evaluator_name": "builtin.task_adherence",
        "initialization_parameters": {"deployment_name": model_deployment},
        "data_mapping": {
            "query": "{{item.query}}",
            "response": "{{item.response}}",
        },
    },
    {
        "type": "azure_ai_evaluator",
        "name": "task_completion",
        "evaluator_name": "builtin.task_completion",
        "initialization_parameters": {"deployment_name": model_deployment},
        "data_mapping": {
            "query": "{{item.query}}",
            "response": "{{item.response}}",
            "tool_definitions": "{{item.tool_definitions}}",
        },
    },
    {
        "type": "azure_ai_evaluator",
        "name": "customer_satisfaction",
        "evaluator_name": "builtin.customer_satisfaction",
        "initialization_parameters": {"model": model_deployment},
        "data_mapping": {
            "messages": "{{item.messages}}",
        },
    },
    {
        "type": "azure_ai_evaluator",
        "name": "intent_resolution",
        "evaluator_name": "builtin.intent_resolution",
        "initialization_parameters": {"deployment_name": model_deployment},
        "data_mapping": {
            "query": "{{item.query}}",
            "response": "{{item.response}}",
        },
    },
    {
        "type": "azure_ai_evaluator",
        "name": "task_navigation_efficiency",
        "evaluator_name": "builtin.task_navigation_efficiency",
        "initialization_parameters": {"matching_mode": "in_order_match"},
        "data_mapping": {
            "actions": "{{item.actions}}",
            "expected_actions": "{{item.expected_actions}}",
        },
    },
]

# --- Process Evaluators ---
process_evaluators = [
    {
        "type": "azure_ai_evaluator",
        "name": "tool_call_accuracy",
        "evaluator_name": "builtin.tool_call_accuracy",
        "initialization_parameters": {"deployment_name": model_deployment},
        "data_mapping": {
            "query": "{{item.query}}",
            "response": "{{item.response}}",
            "tool_definitions": "{{item.tool_definitions}}",
        },
    },
    {
        "type": "azure_ai_evaluator",
        "name": "tool_selection",
        "evaluator_name": "builtin.tool_selection",
        "initialization_parameters": {"deployment_name": model_deployment},
        "data_mapping": {
            "query": "{{item.query}}",
            "response": "{{item.response}}",
            "tool_definitions": "{{item.tool_definitions}}",
        },
    },
    {
        "type": "azure_ai_evaluator",
        "name": "tool_input_accuracy",
        "evaluator_name": "builtin.tool_input_accuracy",
        "initialization_parameters": {"deployment_name": model_deployment},
        "data_mapping": {
            "query": "{{item.query}}",
            "response": "{{item.response}}",
            "tool_definitions": "{{item.tool_definitions}}",
        },
    },
    {
        "type": "azure_ai_evaluator",
        "name": "tool_output_utilization",
        "evaluator_name": "builtin.tool_output_utilization",
        "initialization_parameters": {"deployment_name": model_deployment},
        "data_mapping": {
            "query": "{{item.query}}",
            "response": "{{item.response}}",
            "tool_definitions": "{{item.tool_definitions}}",
        },
    },
    {
        "type": "azure_ai_evaluator",
        "name": "tool_call_success",
        "evaluator_name": "builtin.tool_call_success",
        "initialization_parameters": {"deployment_name": model_deployment},
        "data_mapping": {
            "response": "{{item.response}}",
        },
    },
]

# --- Quality Evaluator ---
quality_evaluators = [
    {
        "type": "azure_ai_evaluator",
        "name": "quality_grader",
        "evaluator_name": "builtin.quality_grader",
        "initialization_parameters": {"deployment_name": model_deployment},
        "data_mapping": {
            "query": "{{item.query}}",
            "response": "{{item.response}}",
        },
    },
]

testing_criteria = system_evaluators + process_evaluators + quality_evaluators

# Sample test data
test_data = [
    {
        "query": [
            {"role": "system", "content": "You are a helpful trail guide assistant for Adventure Works."},
            {"role": "user", "content": "I want to hike in the Scottish Highlands this weekend. What's the weather like and what trails do you recommend?"},
        ],
        "response": [
            {"role": "assistant", "content": [{"type": "tool_call", "name": "get_weather", "arguments": "{\"location\": \"Scottish Highlands\", \"days\": 3}"}]},
            {"role": "tool", "content": [{"type": "tool_result", "tool_result": {"temp": "8C", "conditions": "rain likely", "wind": "moderate"}}]},
            {"role": "assistant", "content": [{"type": "tool_call", "name": "search_trails", "arguments": "{\"location\": \"Scottish Highlands\", \"difficulty\": \"moderate\"}"}]},
            {"role": "tool", "content": [{"type": "tool_result", "tool_result": {"trails": [{"name": "Ben A'an", "distance_km": 5}]}}]},
            {"role": "assistant", "content": "Based on the forecast (8C, rain likely), I'd recommend Ben A'an -- a moderate 5km trail with great views. Bring waterproofs and layers."},
        ],
        "tool_definitions": tool_definitions,
    },
]

if __name__ == "__main__":
    print("Agent Evaluators configured:")
    print("\n  System Evaluators:")
    for e in system_evaluators:
        print(f"    - {e['name']} ({e['evaluator_name']})")
    print("\n  Process Evaluators:")
    for e in process_evaluators:
        print(f"    - {e['name']} ({e['evaluator_name']})")
    print("\n  Quality Evaluators:")
    for e in quality_evaluators:
        print(f"    - {e['name']} ({e['evaluator_name']})")
    print("\nRun these evaluators via the SDK or Foundry portal with your agent responses.")
