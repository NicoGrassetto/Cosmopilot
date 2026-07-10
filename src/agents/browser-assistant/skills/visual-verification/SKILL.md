---
name: visual-verification
description: Verify on-screen state from screenshots before and after each action.
---

# Visual verification

Act on what the screen actually shows, not what you assume it shows.

## Instructions

- Before clicking or typing, confirm the target element is visible and correct in the
  latest screenshot. Re-check after the page changes.
- After each action, verify the expected result occurred (URL changed, element appeared)
  before proceeding to the next step.
- If the screen does not match your expectation, stop, re-observe, and re-plan.
- Describe what you see and what you intend to do next, so the user can follow along.
- Prefer stable selectors (labels, roles, text) over fragile pixel coordinates.
