"""
Cosmopilot Hosted Agent — Data Insights Agent

A hosted agent deployed on Azure AI Foundry that provides real-time
operational insights from Cosmos DB. It uses code interpreter for
data analysis and Cosmos DB tools for live queries.
"""

import os

from azure.ai.projects import FoundryClient
from azure.identity import DefaultAzureCredential

from skills import build_skill_instructions


def create_agent(client: FoundryClient) -> str:
    """Create the data-insights hosted agent in Foundry."""
    base_instructions = """You are Cosmopilot Data Insights, a specialized agent that
analyzes operational data from Azure Cosmos DB. You can:

1. Query Cosmos DB containers for operational metrics
2. Analyze time-series data for trends and anomalies
3. Generate visualizations of system health
4. Summarize change feed events

When analyzing data:
- Always show your reasoning step by step
- Use code interpreter for calculations and charts
- Cite specific data points with timestamps
- Flag any anomalies or threshold breaches"""

    # Append organization skills (Cosmos query standards + event-summary format)
    # as extra instructions. Skills are versioned in Foundry and shared across
    # agents, so updating a skill needs no change here. See ../skills/README.md.
    instructions = base_instructions + build_skill_instructions()

    agent = client.agents.create(
        name="cosmopilot-data-insights",
        model=os.environ.get("AZURE_DEPLOYMENT_NAME", "gpt-4o-mini"),
        instructions=instructions,
        tools=[
            {"type": "code_interpreter"},
            {
                "type": "function",
                "function": {
                    "name": "query_cosmos_db",
                    "description": "Execute a SQL query against Cosmos DB and return results",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "SQL query to execute against Cosmos DB",
                            },
                            "container": {
                                "type": "string",
                                "description": "Target container name",
                                "default": "conversations",
                            },
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_change_feed_events",
                    "description": "Retrieve recent change feed events from Cosmos DB",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "since_minutes": {
                                "type": "integer",
                                "description": "Number of minutes to look back",
                                "default": 60,
                            },
                            "container": {
                                "type": "string",
                                "description": "Target container name",
                                "default": "conversations",
                            },
                        },
                    },
                },
            },
        ],
    )
    return agent.id


def run_agent(client: FoundryClient, agent_id: str, user_message: str) -> str:
    """Run the hosted agent with a user message and return the response."""
    thread = client.agents.threads.create()

    client.agents.messages.create(
        thread_id=thread.id, role="user", content=user_message
    )

    run = client.agents.runs.create_and_wait(
        thread_id=thread.id, agent_id=agent_id
    )

    if run.status == "failed":
        raise RuntimeError(f"Agent run failed: {run.last_error}")

    messages = client.agents.messages.list(thread_id=thread.id)
    return messages.data[0].content[0].text.value


def main():
    """Entry point for local testing."""
    credential = DefaultAzureCredential()
    client = FoundryClient(
        endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
        credential=credential,
    )

    agent_id = create_agent(client)
    print(f"Created agent: {agent_id}")

    response = run_agent(
        client, agent_id, "Show me the system health for the last hour."
    )
    print(f"Response:\n{response}")

    # Cleanup
    client.agents.delete(agent_id)
    print("Agent deleted.")


if __name__ == "__main__":
    main()
