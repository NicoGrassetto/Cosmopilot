---
name: incident-triage-policy
description: Shared severity thresholds, escalation gates, and human-approval rules applied consistently across every Cosmopilot incident-triage agent.
---

# Incident triage policy

Apply this policy consistently across every incident-triage agent — detector,
diagnostician, remediator, and reporter. It defines how severity is assigned,
when to escalate to a human, and which actions require approval. Keeping this in
one skill means all four agents share one source of truth instead of duplicating
the rules in each agent's instructions.

## Severity levels

Classify every incident into exactly one severity:

- **critical** — customer-facing outage, data-loss risk, or sustained
  throttling: Cosmos DB `429 (TooManyRequests)` > 100/min, RU/s consumption
  > 5× provisioned, or p99 latency > 5s.
- **high** — degraded performance with user impact: p99 latency 2–5s, or error
  rate 1–5%.
- **medium** — anomalies without direct user impact: transient spikes, or a
  single hot partition key.
- **low** — informational deviations that stay within expected ranges.

## Escalation

- Escalate to a human when the diagnostic `confidence_score < 0.6`.
- Escalate immediately for any `critical` severity, regardless of confidence.
- When escalating, include: severity, a one-line summary, affected components,
  and the specific evidence (metric + timestamp) that triggered the escalation.

## Human-in-the-loop approval

- Any remediation action with `risk_level == "high"` requires explicit human
  approval before execution.
- Never auto-execute actions that delete data, change a partition key, or reduce
  provisioned throughput.
- For every approval-gated action, present a rollback plan and the estimated
  blast radius.

## Consistency

- Use these exact severity labels everywhere: `critical`, `high`, `medium`,
  `low`.
- Ground every severity call in a concrete metric and timestamp — never assign
  severity from narrative alone.
