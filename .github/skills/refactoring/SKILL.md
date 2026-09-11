---
name: refactoring
description: 'Assess and improve clean-code quality. Use when reviewing readability, naming, large methods or classes, magic values, duplication, unnecessary moving parts, test health, or when planning behavior-preserving refactors.'
argument-hint: '[scope, file, or refactoring goal]'
---

# Refactoring

Assess the requested scope before changing it, then make the smallest behavior-preserving improvement that addresses verified evidence.

## Assessment workflow

1. Read the repository instructions and identify the production code, tests, generated files, vendored code, examples, and explicitly retained legacy implementations in scope.
2. Establish a baseline with the narrowest applicable test command. Do not run live, destructive, costly, or integration tests unless the user explicitly requests them.
3. Inspect owning implementations and representative call sites or tests. Prefer exact searches and executable measurements over impressions.
4. Assess each clean-code criterion in the rubric below. Cite file paths, symbols, and line numbers for every finding.
5. Separate measured facts, reasoned judgments, and unknowns. Never infer coverage percentages from test counts, test markers, or passing tests.
6. Rank findings by maintenance risk and recommend the smallest changes with the highest benefit. Do not recommend abstractions merely to shorten files.
7. When asked to refactor, preserve public APIs unless a change is required, edit one coherent slice at a time, and rerun the focused baseline after each slice.
8. Finish with the exact validation commands and outcomes, including failures, deselections, skipped tests, and unmeasured coverage.

## Clean-code rubric

Score each criterion from 0 to 5. Use half-points only when the evidence genuinely falls between two levels.

### Obvious to other programmers

Evaluate names, function and class size, responsibility boundaries, control flow, comments, types, error handling, and unexplained literal values.

- `5`: Intent and control flow are immediately clear; responsibilities are narrow.
- `3`: Generally understandable, with a few large or ambiguous areas.
- `1`: Frequent unclear names, hidden assumptions, or oversized mixed-responsibility code.
- `0`: The behavior cannot be followed reliably from the source.

### No harmful duplication

Look for copied business rules, repeated lifecycle or error-handling blocks, parallel old/current implementations, and changes that must be synchronized. Similar-looking code is not automatically duplication when it represents intentionally independent behavior.

- `5`: No material knowledge duplication in the assessed scope.
- `3`: Local repetition exists but changes usually have one authoritative location.
- `1`: Important behavior is copied across several locations.
- `0`: Duplication makes safe change impractical.

### Minimal moving parts

Evaluate whether every module, class, helper, layer, configuration object, and dependency earns its cost. Reward direct code and cohesive modules; do not reward either giant modules or speculative abstractions.

- `5`: The design is direct, cohesive, and no more complex than the problem requires.
- `3`: Mostly proportionate, with a few oversized or redundant parts.
- `1`: Excess layers, broad modules, or obsolete paths impose substantial overhead.
- `0`: The structure prevents reliable reasoning or change.

### Passes all tests

Report pass rate only from an actual test run. Report coverage only from a coverage tool. A blocked or partial run is `not verified`, not a pass.

- `5`: All applicable tests pass and measured coverage strongly exercises important behavior and error paths.
- `3`: All runnable tests pass, but coverage is unmeasured or material gaps remain.
- `1`: Tests fail, are mostly blocked, or provide little meaningful protection.
- `0`: No useful tests exist, measured coverage is effectively zero, or failures make the baseline unusable.

## Required output

Provide:

1. Scope, exclusions, date, and commands used.
2. A score table with concise evidence and `not verified` where appropriate.
3. Findings first, ordered by severity, with concrete code references.
4. Existing strengths that should be preserved.
5. A prioritized refactoring plan that names expected benefit, risk, and validation.
6. Test and coverage results without extrapolation.

The repository baseline at the time this skill was created is recorded in [the codebase assessment](./references/codebase-assessment.md). Treat it as dated evidence and refresh it before relying on its scores.