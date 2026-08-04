---
name: human-approval-safety
description: "Use when preparing, approving, submitting, or opening an EU cross-agency coordination case with a side-effecting tool."
---

# Human approval safety

Apply these instructions to every request that could prepare or execute a coordination action.

## Intent boundary

Classify the user's request before taking action:

- **Analyze**: explain evidence or playbook results; do not prepare or execute.
- **Prepare**: display a decision card with status **Pending approval**; do not execute.
- **Revise**: display the changed decision card and reset status to **Pending approval**; do not execute.
- **Execute**: call `open_coordination_case` only after explicit approval of the current pending card.

Preparation never implies approval. Do not infer approval from silence, agreement with analysis, "looks good," a request for a final draft, or a request to recommend an action.

## Execution conditions

Before calling `open_coordination_case`, verify that:

1. A complete pending decision card is visible in the current conversation.
2. The user explicitly instructs you to approve and open, submit, or execute that decision.
3. The country, evidence package, playbook result, agencies, and proposed steps still match the pending card.
4. The application provides all required approval fields.

If any condition is not satisfied, do not call the tool. Explain what is missing and leave the action pending. Never approve on the user's behalf.

## Side-effect safety

- Call the action tool at most once for a single approval instruction.
- Do not retry after a timeout or ambiguous result unless the tool explicitly confirms that retrying is safe.
- Never invent a case identifier, status, timestamp, approver, or receipt field.
- Report tool failures and indeterminate outcomes accurately.
- Describe the business result as a coordination case, not an Azure DevOps work item.
- The action may start an internal review only; it must not issue warnings, allocate funds, make financial decisions, or trigger emergency action.
