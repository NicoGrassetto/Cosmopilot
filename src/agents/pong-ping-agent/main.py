import os

from azure.identity import DefaultAzureCredential
from langchain.agents import create_agent
from langchain_azure_ai.agents.hosting import ResponsesHostServer
from langchain_azure_ai.chat_models import AzureAIOpenAIApiChatModel

model = AzureAIOpenAIApiChatModel(
    project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
    model=os.environ["AZURE_DEPLOYMENT_NAME"],
    credential=DefaultAzureCredential(),
)

agent = create_agent(
    name="ping-pong-agent",
    model=model,
    tools=[],
    system_prompt=(
        "If the user's entire message is 'ping', reply with exactly 'pong', "
        "without punctuation or formatting. "
        "For any other message, reply with exactly 'Please say ping'."
    ),
)

if __name__ == "__main__":
    ResponsesHostServer(agent).run()