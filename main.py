import os

from azure.ai.projects import FoundryClient
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
client = FoundryClient(
    endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
    credential=credential,
)

openai_client = client.get_openai_client()

model = os.environ.get("AZURE_DEPLOYMENT_NAME", "gpt-4o-mini")

data_source_config = {
    "type": "custom",
    "item_schema": {
        "type": "object",
        "properties": {
            "question": {"type": "string"},
            "reference_answer": {"type": "string"},
        },
        "required": ["question", "reference_answer"],
    },
    "include_sample_schema": True,
}

openai_client.evals.create(
    name="cosmos-answer-relevance",
    data_source_config=data_source_config,
    testing_criteria=[
        {
            "type": "label_model",
            "name": "relevance-grader",
            "model": model,
            "input": [
                {
                    "role": "developer",
                    "content": (
                        "Label whether the answer is relevant to the user's "
                        "question about Azure Cosmos DB operations. "
                        "Respond with 'relevant' or 'irrelevant'."
                    ),
                },
                {
                    "role": "user",
                    "content": "Question: {{item.question}}\nAnswer: {{sample.output_text}}",
                },
            ],
            "labels": ["relevant", "irrelevant"],
            "passing_labels": ["relevant"],
        }
    ],
)

openai_client.evals.create(
    name="cosmos-answer-similarity",
    data_source_config=data_source_config,
    testing_criteria=[
        {
            "type": "text_similarity",
            "name": "answer-similarity",
            "input": "{{sample.output_text}}",
            "reference": "{{item.reference_answer}}",
            "evaluation_metric": "cosine",
            "pass_threshold": 0.8,
        }
    ],
)
