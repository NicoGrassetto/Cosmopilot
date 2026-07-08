"""
Pre-composed evaluator suites grouping all 28 built-in evaluators.

Usage:
    from evals.suites import quality_suite, safety_suite

    evaluators = quality_suite(model_config)
    evaluators.update(safety_suite(azure_ai_project))
"""

from azure.ai.evaluation import (
    # General purpose (AI-assisted)
    CoherenceEvaluator,
    FluencyEvaluator,
    QAEvaluator,
    # Textual similarity / NLP
    SimilarityEvaluator,
    F1ScoreEvaluator,
    BleuScoreEvaluator,
    GleuScoreEvaluator,
    RougeScoreEvaluator,
    MeteorScoreEvaluator,
    # RAG
    RetrievalEvaluator,
    DocumentRetrievalEvaluator,
    GroundednessEvaluator,
    GroundednessProEvaluator,
    RelevanceEvaluator,
    ResponseCompletenessEvaluator,
    # Risk and safety
    ViolenceEvaluator,
    SexualEvaluator,
    SelfHarmEvaluator,
    HateUnfairnessEvaluator,
    IndirectAttackEvaluator,
    ProtectedMaterialEvaluator,
    UngroundedAttributesEvaluator,
    CodeVulnerabilityEvaluator,
    ContentSafetyEvaluator,
    # Agentic
    IntentResolutionEvaluator,
    ToolCallAccuracyEvaluator,
    TaskAdherenceEvaluator,
    # Azure OpenAI Graders
    AzureOpenAILabelGrader,
    AzureOpenAIStringCheckGrader,
    AzureOpenAITextSimilarityGrader,
    AzureOpenAIGrader,
)


def quality_suite(model_config: dict) -> dict:
    """General quality + RAG evaluators. Requires a judge model."""
    return {
        "coherence": CoherenceEvaluator(model_config),
        "fluency": FluencyEvaluator(model_config),
        "relevance": RelevanceEvaluator(model_config),
        "groundedness": GroundednessEvaluator(model_config),
        "retrieval": RetrievalEvaluator(model_config),
        "similarity": SimilarityEvaluator(model_config),
        "response_completeness": ResponseCompletenessEvaluator(model_config),
        "qa": QAEvaluator(model_config),
    }


def rag_pro_suite(azure_ai_project) -> dict:
    """RAG evaluators that use the Azure AI Content Safety backend."""
    return {
        "groundedness_pro": GroundednessProEvaluator(azure_ai_project),
        "document_retrieval": DocumentRetrievalEvaluator(azure_ai_project),
    }


def safety_suite(azure_ai_project) -> dict:
    """All risk & safety evaluators. Requires Foundry project connection."""
    return {
        "violence": ViolenceEvaluator(azure_ai_project),
        "sexual": SexualEvaluator(azure_ai_project),
        "self_harm": SelfHarmEvaluator(azure_ai_project),
        "hate_unfairness": HateUnfairnessEvaluator(azure_ai_project),
        "indirect_attack": IndirectAttackEvaluator(azure_ai_project),
        "protected_material": ProtectedMaterialEvaluator(azure_ai_project),
        "ungrounded_attributes": UngroundedAttributesEvaluator(azure_ai_project),
        "code_vulnerability": CodeVulnerabilityEvaluator(azure_ai_project),
        "content_safety": ContentSafetyEvaluator(azure_ai_project),
    }


def agentic_suite(model_config: dict) -> dict:
    """Evaluators for tool-calling agents. Requires a judge model."""
    return {
        "intent_resolution": IntentResolutionEvaluator(model_config),
        "tool_call_accuracy": ToolCallAccuracyEvaluator(model_config),
        "task_adherence": TaskAdherenceEvaluator(model_config),
    }


def nlp_suite() -> dict:
    """NLP / textual similarity metrics. No model needed."""
    return {
        "f1": F1ScoreEvaluator(),
        "bleu": BleuScoreEvaluator(),
        "gleu": GleuScoreEvaluator(),
        "rouge": RougeScoreEvaluator(),
        "meteor": MeteorScoreEvaluator(),
    }


def grader_suite(model_config: dict, labels: list[str] | None = None) -> dict:
    """Azure OpenAI Graders. Requires a judge model.

    Args:
        model_config: Azure OpenAI model configuration.
        labels: Classification labels for the label grader.
    """
    graders = {
        "string_check": AzureOpenAIStringCheckGrader(
            model_config=model_config,
            input="{{item.response}}",
            name="string_check",
            reference="{{item.ground_truth}}",
            operation="eq",
        ),
        "text_similarity": AzureOpenAITextSimilarityGrader(
            model_config=model_config,
            input="{{item.response}}",
            name="text_similarity",
            reference="{{item.ground_truth}}",
            evaluation_metric="fuzzy_match",
        ),
    }
    if labels:
        graders["label"] = AzureOpenAILabelGrader(
            model_config=model_config,
            input=[{"role": "user", "content": "{{item.response}}"}],
            labels=labels,
            model=model_config.get("azure_deployment", "gpt-4o"),
            name="label_grader",
            passing_labels=labels[:1],
        )
    return graders


def all_suites(model_config: dict, azure_ai_project) -> dict:
    """Combine all suites into one evaluator dict (excluding graders)."""
    combined = {}
    combined.update(quality_suite(model_config))
    combined.update(rag_pro_suite(azure_ai_project))
    combined.update(safety_suite(azure_ai_project))
    combined.update(agentic_suite(model_config))
    combined.update(nlp_suite())
    return combined
