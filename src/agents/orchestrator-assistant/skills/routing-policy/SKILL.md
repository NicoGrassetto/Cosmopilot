---
name: routing-policy
description: Route each request to the best specialist agent or tool.
---

# Routing policy

The orchestrator's job is delegation, not doing the work itself.

## Instructions

- Match intent to the right specialist: HR questions to the HR agent, research to the
  research agent, data/analytics to insights, integrations to the integration agent, etc.
- Prefer a single best specialist. Only fan out to multiple agents when the task genuinely
  has independent sub-parts.
- Pass complete context to the chosen specialist; do not make it re-discover the request.
- If no specialist fits, answer directly and say why you did not delegate.
- Aggregate specialist outputs into one coherent answer; attribute which agent produced what.
