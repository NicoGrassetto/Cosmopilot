---
name: change-feed-summary-format
description: Canonical structured output format for classifying and summarizing Cosmos DB change-feed events across Cosmopilot agents.
---

# Change-feed summary format

Use this format whenever you classify or summarize an operational event from the
Cosmos DB change feed. It applies to the data-enrichment workflow classifier, the
incident reporter, and any agent that emits an event summary — so downstream
consumers can parse results deterministically.

## Classification object

Return a JSON object with exactly these fields, in this order:

- `category` — one of: `performance`, `error`, `security`, `configuration`,
  `scaling`, `deployment`.
- `severity` — one of: `low`, `medium`, `high`, `critical`. Use the thresholds
  defined in the `incident-triage-policy` skill.
- `summary` — a single present-tense sentence, at most 160 characters.

## Rules

- Choose exactly one `category` and one `severity`; never return multiple values
  for either.
- The `summary` must name the affected resource (container, account, or
  partition) and the observed signal.
- Do not embed the raw event body in the summary; reference it by `id` instead.
- Keep the field order stable so downstream parsers stay deterministic.

## Example

```json
{
  "category": "performance",
  "severity": "critical",
  "summary": "Container conversations is throttling with sustained 429s on tenant acme."
}
```
