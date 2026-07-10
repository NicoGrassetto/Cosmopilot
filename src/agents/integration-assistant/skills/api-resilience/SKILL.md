---
name: api-resilience
description: Call external APIs and connectors with retries, backoff, and idempotency.
---

# API resilience

Integrations fail transiently. Design every call to tolerate that.

## Instructions

- Retry transient failures (429, 502, 503, timeouts) with exponential backoff and jitter.
- Respect Retry-After headers and documented rate limits; do not hammer an endpoint.
- Make mutating operations idempotent (use idempotency keys or natural unique keys) so
  a retry never double-applies a change.
- Validate and echo the request payload before executing a write; confirm destructive calls.
- Surface the HTTP status, error body, and a plain-language explanation when a call fails.
- Never log or expose secrets, tokens, or connection strings in outputs.
