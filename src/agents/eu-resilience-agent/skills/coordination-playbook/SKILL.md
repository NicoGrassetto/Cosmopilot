---
name: coordination-playbook
description: "Use when deciding whether EU cross-agency coordination criteria are met or when assigning lead and participating agencies."
---

# Coordination playbook

Apply these instructions whenever the user asks whether coordination is justified, who should participate, or what internal response should follow.

## Instructions

1. Establish a current country evidence package before evaluating coordination.
2. Call `evaluate_coordination_playbook`; do not reproduce its thresholds or agency-selection logic in model reasoning.
3. Use the returned result for:
   - Eligibility status
   - Criteria met, not met, or indeterminate
   - Playbook name and version
   - Lead agency
   - Participating agencies
   - Recommended internal review steps
   - Limitations
4. Explain the evidence supporting each met criterion.
5. Do not override, broaden, or narrow the returned result using model judgment.
6. If required evidence is missing or the result is indeterminate, recommend evidence review rather than claiming eligibility.
7. Always describe the playbook as illustrative demo logic, not formal EU policy, legal advice, or an emergency-response mandate.
8. Agency assignments initiate an internal coordination review only. They do not authorize public warnings, funding decisions, financial interventions, or emergency action.

## Decision-card consistency

When preparing a decision card, copy the playbook version, criteria, agency assignments, and limitations from the matching evaluation result. If the country evidence or proposed action changes, evaluate the playbook again before presenting a revised card.
