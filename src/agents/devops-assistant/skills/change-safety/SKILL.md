---
name: change-safety
description: Apply infrastructure and shell changes safely with dry-runs and confirmation.
---

# Change safety protocol

This agent can run shells, patch files, and invoke functions. Guard every change.

## Instructions

- Dry-run first where possible (--what-if, --dry-run, plan) and show the diff before applying.
- Explicitly confirm before destructive or irreversible operations: deletes, drops,
  force pushes, scaling to zero, or production changes.
- Prefer the smallest, most targeted change that accomplishes the goal.
- Never run commands that exfiltrate secrets or disable security controls.
- After a change, verify success (status, health check, tests) and report the outcome.
- If a command fails, stop and diagnose; do not blindly retry destructive operations.
