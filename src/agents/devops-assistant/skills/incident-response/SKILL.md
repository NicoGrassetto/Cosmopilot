---
name: incident-response
description: Triage production incidents methodically before making changes.
---

# Incident response runbook

During an incident, structure beats speed. Follow the loop.

## Instructions

- Establish impact first: what is broken, since when, and who/what is affected.
- Gather evidence (logs, metrics, recent deploys) before hypothesizing a cause.
- Prefer mitigations that restore service (rollback, scale out, failover) over risky fixes.
- Change one thing at a time and observe its effect before the next action.
- Keep a running timeline of actions taken and their results for the postmortem.
- Escalate to a human on-call for data loss, security breaches, or customer-facing outages.
