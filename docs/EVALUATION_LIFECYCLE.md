# Evaluation Lifecycle

Use progressively broader evaluations as a change gets closer to production. Local deterministic checks provide fast PR feedback; cloud evaluation adds managed quality, safety, agent, and reporting capabilities where their cost and latency are justified.

## Evaluation levels

| Trigger | Level | Checks | Blocking |
| --- | --- | --- | --- |
| Commit or draft PR | L0 | Lint, types, unit tests, and evaluator configuration validation | Yes |
| PR to `develop` | L1 | Small curated local dataset with deterministic and custom evaluators | Yes |
| PR to `main` | L2 | Cloud quality, safety, groundedness, rubric, and applicable agent evaluators | Yes |
| Merge to `main` | L3 | Cloud smoke evaluation against the deployed model or agent target | Yes for promotion |
| Nightly schedule | L4 | Larger datasets, conversation tests, model comparisons, and sampled traces | Alert or open an issue |
| Weekly or pre-release | L5 | Full safety suite, adversarial simulation, red teaming, and compliance checks | Required for release |
| Production continuously | L6 | Sample real traces for quality, safety, tool success, latency, and drift | Alerting; not normally deployment-blocking |

For repositories without a `develop` branch, run L0 and L1 on every PR and L2 on PRs targeting `main`.

## Evaluation definitions and runs

Register stable evaluation definitions once and reuse them across runs:

- `cosmopilot-pr-quality`
- `cosmopilot-pr-safety`
- `cosmopilot-agent-regression`
- `cosmopilot-nightly-quality`
- `cosmopilot-release-assurance`

Create a distinct run for every PR, commit, schedule, or release:

- `pr-142-a1b2c3d`
- `main-a1b2c3d`
- `nightly-2026-08-01`
- `release-v1.4.0`

Do not register a new evaluation definition for every PR. A stable definition keeps criteria comparable while uniquely named runs preserve the commit, dataset version, and execution history.

## Suggested gates

- Deterministic checks: 100% passing.
- Safety checks: 100% passing.
- Groundedness: at least 95% passing.
- Relevance: at least 90% passing.
- Rubric quality: at least 85% passing.
- No meaningful regression from the latest successful `main` baseline.

Treat these percentages as starting points and calibrate them against reviewed examples. Gate on aggregate dataset results rather than a single LLM judgment. Retry infrastructure failures, but do not retry a genuine failed score into passing.

## Related references

- [Evaluator catalog](evaluations.md)
- [Evaluator API reference](EVALUATORS.md)
- [Data-source configuration reference](DATA_SOURCE_CONFIGS.md)
