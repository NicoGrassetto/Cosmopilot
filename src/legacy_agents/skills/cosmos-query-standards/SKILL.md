---
name: cosmos-query-standards
description: Safe, cost-aware conventions for generating and executing Azure Cosmos DB queries from Cosmopilot agents.
---

# Cosmos DB query standards

Follow these conventions whenever you generate or execute a Cosmos DB query — for
example through the `query_cosmos_db` tool. They keep queries safe, cheap, and
grounded, and they apply to any agent that touches operational data (the
data-insights hosted agent and the incident detector).

## Safety

- Generate **read-only** queries only. Never emit `INSERT`, `UPDATE`, `DELETE`,
  or container-management statements.
- Always scope by the partition key (`/tenantId`) when the tenant is in context.
  Do not run cross-partition queries when a partition key is known.
- Treat user-supplied values as data, not SQL. Do not interpolate raw input into
  query text without validation.

## Cost awareness (RU/s)

- Prefer point reads and partition-scoped queries over cross-partition scans.
- Filter on indexed properties; avoid `SELECT *` when only a few fields are
  needed.
- Cap exploratory result sets with `TOP` (or `OFFSET`/`LIMIT`); default to
  `TOP 100` unless the user explicitly asks for more.
- When a query is likely to be cross-partition or high-RU, call that out and
  suggest a cheaper alternative before running it.

## Grounding

- Always report the `database` and `container` you queried.
- Cite specific documents by their `id` and timestamp when summarizing results.
- If data is unavailable, state clearly what is missing rather than guessing.
