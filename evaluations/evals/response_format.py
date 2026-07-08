"""
Custom code-based evaluator: Response Format Validation.

Checks that agent responses conform to expected structural requirements
(e.g., JSON output, markdown formatting, max length, required sections).
"""

import json
import re
from typing import Optional


class ResponseFormatEvaluator:
    """Code-based evaluator for structural/format requirements.

    Args:
        max_length: Maximum allowed character count (None = no limit).
        min_length: Minimum required character count.
        expected_format: One of "json", "markdown", "plain", or None.
        required_sections: List of heading/section titles that must appear.
        forbidden_patterns: Regex patterns that must NOT appear in the response.
    """

    def __init__(
        self,
        max_length: Optional[int] = None,
        min_length: int = 0,
        expected_format: Optional[str] = None,
        required_sections: Optional[list[str]] = None,
        forbidden_patterns: Optional[list[str]] = None,
    ):
        self._max_length = max_length
        self._min_length = min_length
        self._expected_format = expected_format
        self._required_sections = required_sections or []
        self._forbidden_patterns = forbidden_patterns or []

    def __call__(self, *, response: str, **kwargs) -> dict:
        issues = []
        checks_passed = 0
        total_checks = 0

        # Length checks
        total_checks += 1
        if self._min_length and len(response) < self._min_length:
            issues.append(f"Response too short: {len(response)} < {self._min_length} chars")
        else:
            checks_passed += 1

        if self._max_length:
            total_checks += 1
            if len(response) > self._max_length:
                issues.append(f"Response too long: {len(response)} > {self._max_length} chars")
            else:
                checks_passed += 1

        # Format validation
        if self._expected_format:
            total_checks += 1
            if self._expected_format == "json":
                try:
                    json.loads(response)
                    checks_passed += 1
                except json.JSONDecodeError:
                    issues.append("Expected JSON format but response is not valid JSON")
            elif self._expected_format == "markdown":
                if re.search(r"(^#|\*\*|```|\- )", response, re.MULTILINE):
                    checks_passed += 1
                else:
                    issues.append("Expected markdown formatting but none detected")
            else:
                checks_passed += 1

        # Required sections
        for section in self._required_sections:
            total_checks += 1
            if section.lower() in response.lower():
                checks_passed += 1
            else:
                issues.append(f"Missing required section: '{section}'")

        # Forbidden patterns
        for pattern in self._forbidden_patterns:
            total_checks += 1
            if re.search(pattern, response, re.IGNORECASE):
                issues.append(f"Forbidden pattern found: '{pattern}'")
            else:
                checks_passed += 1

        score = checks_passed / total_checks if total_checks > 0 else 1.0

        return {
            "format_score": round(score, 2),
            "format_pass": len(issues) == 0,
            "format_issues": issues,
            "format_checks_passed": checks_passed,
            "format_checks_total": total_checks,
        }
