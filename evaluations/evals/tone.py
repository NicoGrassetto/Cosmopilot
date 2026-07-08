"""
Custom prompt-based evaluator: Tone & Style.

Evaluates whether the agent response matches an expected tone
(e.g., professional, friendly, concise).
"""

import os
from typing import Optional

import prompty
from prompty.core import Prompty


TONE_PROMPT = """system:
You are an expert evaluator of conversational AI tone and style.

Given a response from an AI assistant, evaluate whether the tone matches
the expected style described below.

Expected tone: {{expected_tone}}

Score from 1 to 5:
- 1: Completely mismatched tone
- 2: Mostly mismatched with occasional alignment
- 3: Mixed — partially matches expected tone
- 4: Mostly matches with minor deviations
- 5: Perfectly aligned with expected tone

user:
Response to evaluate:
{{response}}

Provide your assessment as JSON: {"score": <int>, "reason": "<brief explanation>"}
"""


class ToneEvaluator:
    """Prompt-based evaluator that scores tone alignment on a 1-5 scale.

    Args:
        model_config: Azure OpenAI model configuration dict.
        expected_tone: Description of the desired tone (e.g., "professional and concise").
    """

    def __init__(self, model_config: dict, expected_tone: str = "professional and helpful"):
        self._model_config = model_config
        self._expected_tone = expected_tone

    def __call__(self, *, response: str, expected_tone: Optional[str] = None, **kwargs) -> dict:
        import json
        from openai import AzureOpenAI

        tone = expected_tone or self._expected_tone

        client = AzureOpenAI(
            azure_endpoint=self._model_config["azure_endpoint"],
            api_key=self._model_config.get("api_key", os.environ.get("AZURE_OPENAI_API_KEY")),
            api_version=self._model_config.get("api_version", "2024-12-01-preview"),
        )

        prompt = TONE_PROMPT.replace("{{expected_tone}}", tone).replace("{{response}}", response)
        messages = [
            {"role": "system", "content": prompt.split("user:")[0].replace("system:", "").strip()},
            {"role": "user", "content": prompt.split("user:")[1].strip()},
        ]

        completion = client.chat.completions.create(
            model=self._model_config.get("azure_deployment", "gpt-4o"),
            messages=messages,
            temperature=0,
            response_format={"type": "json_object"},
        )

        result = json.loads(completion.choices[0].message.content)
        return {
            "tone_score": result.get("score", 0),
            "tone_reason": result.get("reason", ""),
        }
