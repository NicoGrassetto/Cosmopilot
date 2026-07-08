"""
Run all test prompts against the deployed agent and store responses.

This script:
1. Loads test prompts from test-prompts/ directory
2. Retrieves the most recent agent version by name
3. Calls the agent for each prompt
4. Captures responses with metadata
5. Saves results to experiments/{experiment-name}/agent-responses.json
"""
import os
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

# Load environment variables from .env file
load_dotenv()


def load_test_prompts(test_prompts_dir):
    """Load all test prompt files from the test-prompts directory."""
    prompts = {}
    for prompt_file in Path(test_prompts_dir).glob("*.txt"):
        test_name = prompt_file.stem
        with open(prompt_file, 'r') as f:
            prompts[test_name] = f.read().strip()
    return prompts


def run_batch_tests(experiment_name):
    """
    Run all test prompts against the deployed agent and capture responses.

    Args:
        experiment_name: Name of the experiment (e.g., 'prompt-v2-concise')
    """
    # Load test prompts
    test_prompts_dir = Path(__file__).parent / 'test-prompts'
    test_prompts = load_test_prompts(test_prompts_dir)

    if not test_prompts:
        print(f"No test prompts found in {test_prompts_dir}")
        return

    print(f"Running {len(test_prompts)} test prompts for experiment: {experiment_name}")
    print("=" * 80)

    # Create project client
    client = AIProjectClient(
        endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
        credential=DefaultAzureCredential(),
    )

    openai_client = client.get_openai_client()

    # Get the agent by name
    agent_name = os.environ.get("AGENT_NAME", "trail-guide")

    agents = client.agents.list()
    agent = None
    for a in agents:
        if a.name == agent_name:
            agent = a
            break

    if not agent:
        print(f"Error: No agent found with name '{agent_name}'")
        print("Please run 'python agent.py' first to create the agent.")
        return

    print(f"Using agent: {agent.name} (id: {agent.id})")

    # Capture all results
    results = {
        "experiment": experiment_name,
        "timestamp": datetime.now().isoformat(),
        "agent_id": agent.id,
        "agent_name": agent.name,
        "test_results": []
    }

    # Run each test prompt
    for test_name, prompt_text in sorted(test_prompts.items()):
        print(f"\nTesting: {test_name}")
        print(f"   Prompt: {prompt_text[:60]}...")

        conversation = openai_client.conversations.create()

        openai_client.conversations.items.create(
            conversation_id=conversation.id,
            items=[{
                "type": "message",
                "role": "user",
                "content": prompt_text,
            }],
        )

        response = openai_client.responses.create(
            conversation=conversation.id,
            extra_body={"agent_reference": {"name": agent_name, "type": "agent_reference"}},
            input="",
        )

        try:
            response_text = response.output[0].content[0].text
        except Exception:
            response_text = str(response)

        usage = getattr(response, "usage", None)
        token_usage = {
            "prompt_tokens": getattr(usage, "input_tokens", None) if usage else None,
            "completion_tokens": getattr(usage, "output_tokens", None) if usage else None,
            "total_tokens": getattr(usage, "total_tokens", None) if usage else None,
        }

        results["test_results"].append({
            "test_name": test_name,
            "prompt": prompt_text,
            "response": response_text,
            "token_usage": token_usage,
        })

        print(f"   Response captured ({token_usage['total_tokens']} tokens)")

    # Save results to experiment folder
    experiment_dir = Path(__file__).parent / 'experiments' / experiment_name
    experiment_dir.mkdir(parents=True, exist_ok=True)

    results_file = experiment_dir / 'agent-responses.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to {results_file}")


if __name__ == "__main__":
    import sys
    experiment = sys.argv[1] if len(sys.argv) > 1 else "default"
    run_batch_tests(experiment)
