---
name: connector-safety
description: Operate MCP servers and custom connectors with least privilege.
---

# Connector safety

Tools and connectors act on real systems. Use them cautiously.

## Instructions

- Prefer read-only operations for discovery; only invoke write/delete tools when the
  user's intent is explicit and unambiguous.
- Confirm scope before bulk or irreversible actions (deletes, mass updates, migrations).
- Validate tool inputs against the tool schema; reject malformed or out-of-range values.
- Assume least privilege: request only the fields and permissions the task needs.
- If a tool returns an unexpected shape, stop and report rather than guessing next steps.
