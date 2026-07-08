"""
Custom code-based evaluator: Domain Accuracy.

Validates that agent responses contain expected domain-specific
facts or keywords. Configurable per agent via a facts dictionary.
"""

from typing import Optional


class DomainAccuracyEvaluator:
    """Code-based evaluator that checks factual accuracy against known domain facts.

    Args:
        required_facts: Dict mapping query patterns to expected facts/keywords.
            Example: {"capital of France": ["Paris"], "water composition": ["H2O", "hydrogen", "oxygen"]}
        case_sensitive: Whether fact matching is case-sensitive.
    """

    def __init__(self, required_facts: dict[str, list[str]], case_sensitive: bool = False):
        self._facts = required_facts
        self._case_sensitive = case_sensitive

    def __call__(
        self,
        *,
        query: str,
        response: str,
        ground_truth: Optional[str] = None,
        **kwargs,
    ) -> dict:
        matched_facts = []
        missing_facts = []
        applicable_facts = []

        # Find which fact sets apply to this query
        for pattern, expected_keywords in self._facts.items():
            check_query = query if self._case_sensitive else query.lower()
            check_pattern = pattern if self._case_sensitive else pattern.lower()

            if check_pattern in check_query:
                applicable_facts.extend(expected_keywords)

        if not applicable_facts:
            return {
                "domain_accuracy_score": 1.0,
                "domain_accuracy_reason": "No domain facts configured for this query.",
                "matched_facts": [],
                "missing_facts": [],
            }

        # Check which facts appear in the response
        check_response = response if self._case_sensitive else response.lower()
        for fact in applicable_facts:
            check_fact = fact if self._case_sensitive else fact.lower()
            if check_fact in check_response:
                matched_facts.append(fact)
            else:
                missing_facts.append(fact)

        score = len(matched_facts) / len(applicable_facts) if applicable_facts else 1.0

        return {
            "domain_accuracy_score": round(score, 2),
            "domain_accuracy_reason": (
                f"Matched {len(matched_facts)}/{len(applicable_facts)} expected facts."
            ),
            "matched_facts": matched_facts,
            "missing_facts": missing_facts,
        }
