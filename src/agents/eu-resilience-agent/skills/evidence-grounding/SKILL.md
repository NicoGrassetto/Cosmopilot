---
name: evidence-grounding
description: "Use when ranking countries or explaining environmental, health, food, economic, population, wildfire, or banking evidence."
---

# Evidence grounding

Apply these instructions whenever a response contains factual claims about EU resilience priorities, countries, indicators, agencies, or observation dates.

## Instructions

1. Call the relevant evidence tool before making factual claims:
   - Use `get_resilience_priorities` for rankings and comparisons.
   - Use `get_country_resilience_evidence` for country-specific explanations.
2. Treat the latest successful tool result for the requested scope as authoritative.
3. Include the observation date and describe the source as a curated snapshot.
4. Preserve returned values, units, source labels, classifications, and geographic grain.
5. Never present country-level evidence as regional, city-level, or local evidence.
6. Separate the response into:
   - Observed or source-derived evidence
   - Derived interpretation
   - Plausible scenario
7. Report missing, stale, conflicting, or indeterminate evidence explicitly.
8. Do not calculate missing indicators, infer unsupported relationships, or fill gaps from model memory.
9. Do not imply causation from correlation.
10. Keep function names, file paths, ZIP archives, and local implementation details out of business-facing answers unless explicitly requested.

## Minimum disclosure

For substantive evidence answers, include:

- Snapshot date
- Geographic grain
- Strongest supporting indicators
- Material synthetic-data usage
- Material evidence limitations
