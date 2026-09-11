# Cosmopilot clean-code assessment

Assessment date: 2026-09-11

## Scope and method

This baseline samples hand-authored Python in `src/`, `backend/`, and `frontend/server.py`, together with the corresponding tests. Documentation, datasets, generated infrastructure output, and third-party code are excluded. Legacy files are reported separately so they do not distort the active-code assessment.

Evidence was gathered with exact symbol and text searches plus targeted source reads. The intended fast test command was:

```shell
PYTHONPATH=src .venv/bin/python -m pytest -m 'not integration'
```

The command did not reach test collection because the active virtual environment does not contain `pytest`, although `pytest==9.1.1` is pinned in `requirements.txt`. Installing the full requirements and then installing only the pinned pytest version were both attempted; each failed on a read timeout from `files.pythonhosted.org`. Test passage and coverage are therefore not verified in this snapshot.

## Scores

| Criterion | Score | Evidence |
| --- | ---: | --- |
| Obvious to other programmers | 3/5 | Types and names are generally explicit, but one request handler contains roughly 385 lines of mixed workflow logic. |
| No harmful duplication | 2/5 | Project-client setup is repeated broadly, and old/current agent implementations coexist. |
| Minimal moving parts | 3/5 | The code avoids deep class hierarchies, but broad modules and legacy paths increase the reasoning surface. |
| Passes all tests | Not verified | The fast suite was blocked by a missing test dependency; coverage was not measured. |
| Overall | 2.7/5 provisional | Mean of the three scored criteria; do not treat this as a complete score until tests run. |

## Findings

### High: request handling has too many responsibilities

[`FrontendRequestHandler.do_POST`](../../../../frontend/server.py#L204-L588) handles request validation, session creation and lookup, document state, agent streaming, tool execution, approval state, response shaping, and exception translation in one method. Its named request limits and typed `SessionState` are useful, but following or changing one branch requires understanding the full workflow.

Recommended direction: extract cohesive functions for parsing/validation, session acquisition, and agent-turn execution. Keep the HTTP handler and shared state model; introducing a class per responsibility would increase moving parts without clear benefit.

### High: Azure project-client lifecycle is duplicated

The exact context-manager expression `DefaultAzureCredential() as credential` appears 115 times across 18 files, including 30 occurrences in [`src/agents/agents.py`](../../../../src/agents/agents.py#L39). Most occurrences repeat endpoint lookup, preview configuration, and `AIProjectClient` lifecycle management around a small SDK call.

Recommended direction: first prove a small context-manager function can preserve credential and client cleanup, endpoint selection, and preview behavior. Apply it to one cohesive module and compare tests before expanding it. Do not hide materially different client construction behind one abstraction.

### Medium: legacy and current agent paths coexist

Two explicit legacy files remain: [`src/agents/agents_old.py`](../../../../src/agents/agents_old.py) and [`create_eu_resilience_agent_old.py`](../../../../src/agents/eu-resilience-agent/create_eu_resilience_agent_old.py). The [`weather creation script`](../../../../src/agents/weather-agent/create_weather_agent.py#L1) imports the old agent module, so these files cannot safely be labeled dead code or deleted without first resolving that dependency.

Recommended direction: document why the weather path still needs the old API or migrate it to the current API under a focused test. Remove a legacy file only after searches and tests prove it has no callers.

### Medium: the main agent wrapper module is broad

[`src/agents/agents.py`](../../../../src/agents/agents.py) contains many related SDK wrappers and their CLI surface in one module. The functions are individually typed and mostly direct, but repeated setup and the number of operations make navigation and coordinated lifecycle changes expensive.

Recommended direction: remove setup duplication before splitting the module. Split only along an existing stable boundary, such as API operations versus CLI parsing, and preserve imports used by tests and scripts.

### Medium: fast feedback covers a minority of declared tests

Static search found 86 pytest-style test functions and 52 `integration` markers across nine files. The repository intentionally excludes those live Azure tests from routine local validation because they can incur cost. This leaves a meaningful mocked unit-test layer for agents, frontend behavior, reports, memory storage, insights, models, and deployments, but several SDK wrapper modules are protected only by live tests.

Recommended direction: add mocked contract tests to integration-only modules when they are refactored. Keep live tests for service compatibility; unit tests should complement rather than replace them.

## Strengths to preserve

- Core wrappers use type annotations and descriptive public operation names.
- Resource cleanup commonly uses credential and client context managers.
- Limits in the frontend are named constants rather than unexplained inline literals.
- The design is predominantly functional and does not rely on deep inheritance or speculative class hierarchies.
- Existing mocked tests verify parameter forwarding and CLI behavior without Azure access.

## Prioritized plan

| Priority | Change | Expected benefit | Primary risk | Validation |
| --- | --- | --- | --- | --- |
| 1 | Restore dependencies and run the non-integration suite | Establishes a trustworthy baseline | Environment resolution may differ from CI | Exact fast-suite command above |
| 2 | Extract functions from `do_POST` one responsibility at a time | Improves readability and error-path testing | Streaming or session-state regression | Narrow frontend tests, then fast suite |
| 3 | Add one project-client context manager in a single module | Removes repeated lifecycle code | Cleanup or preview-mode behavior changes | Existing wrapper mocks plus new lifecycle tests |
| 4 | Resolve the weather agent's dependency on `agents_old` | Establishes one canonical implementation | Preview API incompatibility | Focused creation-script test or dry-run mocks |
| 5 | Add mocked tests when touching integration-only wrappers | Faster feedback without Azure cost | Mocks may drift from SDK contracts | Unit tests plus retained live integration coverage |

## Limitations

- No test pass rate is available because `pytest` was missing from the active environment and dependency downloads timed out.
- `pytest-cov` is neither pinned nor installed, and no coverage report is available, so no coverage percentage is claimed.
- Similarity was measured through targeted textual patterns, not a clone-detection tool.
- Live Azure behavior, performance, security, and dataset quality were outside this assessment.