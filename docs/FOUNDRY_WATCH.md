# Microsoft Foundry SDK and Documentation Watcher

This document defines a proposed automated watcher for Microsoft Foundry SDK
features that may affect Cosmopilot. The watcher uses the exact SDK versions in
[`requirements.txt`](../requirements.txt) as its baseline and monitors the
public source repository behind Microsoft Learn for supporting documentation
changes.

The watcher produces evidence-backed GitHub issues for review. It does not edit
dependencies, modify source code, invoke a coding agent, open pull requests, or
run live Azure tests.

## Scope

The watcher monitors only supported Microsoft Foundry SDK packages that are
present with an exact `==` pin in `requirements.txt`. The current packages are:

- `azure-ai-projects`
- `azure-ai-evaluation`

Packages such as `azure-core`, `azure-identity`, and `openai` are not monitored
independently. They can still appear in a proposal when a newer Foundry SDK
requires a dependency migration.

The following sources are deliberately outside the trigger path:

- Unreleased SDK changes on the default branch.
- Azure REST API and TypeSpec changes.
- Preview or release-candidate packages not selected by the repository pin.
- Bug fixes, sample changes, CI changes, and prose-only SDK changes.

## Authoritative sources

### Published SDK releases

PyPI is the authority for whether a package version has been published:

- `https://pypi.org/pypi/azure-ai-projects/json`
- `https://pypi.org/pypi/azure-ai-evaluation/json`

For each newer stable, non-yanked release, the watcher reads the immutable
version-tagged changelog in
[`Azure/azure-sdk-for-python`](https://github.com/Azure/azure-sdk-for-python):

- `sdk/ai/azure-ai-projects/CHANGELOG.md`
- `sdk/evaluation/azure-ai-evaluation/CHANGELOG.md`

The matching tagged `api.md` file is used, when available, to corroborate new
public classes, operations, parameters, and return types. The release-specific
PyPI description is a fallback when the tagged changelog cannot be retrieved.

### Microsoft Learn documentation

Microsoft Learn exposes its public Foundry documentation source in
[`MicrosoftDocs/azure-ai-docs`](https://github.com/MicrosoftDocs/azure-ai-docs).
The watcher tracks:

- `articles/foundry/**`
- `articles/foundry/whats-new-foundry.md`

Documentation activity is supporting context. A documentation-only change
never creates a code proposal.

## Detection rules

The watcher performs these steps for every supported exact pin:

1. Parse the pinned version from `requirements.txt`.
2. Query PyPI for newer stable versions with published, non-yanked files.
3. Fetch the changelog from the matching immutable SDK tag.
4. Parse only the block for that published version.
5. Determine whether the release contains at least one entry under
   `Features Added` or `Features added`.
6. Map each feature to local imports, client operations, tests, and docs.
7. Create a GitHub issue only when the feature has a credible local ownership
   match.

A published release is actionable only when its release block has a non-empty
feature section. Breaking changes, deprecations, and dependency updates are
included as adoption requirements only when that same release contains a new
feature.

The watcher does not create an issue for a release containing only:

- `Bugs Fixed`
- `Other Changes`
- Dependency updates
- Sample or example updates
- Documentation updates
- Test or CI changes

## Repository impact analysis

The watcher uses Python's `ast` module to build a local usage inventory under
`src/` and `tests/`. It records:

- Imports from monitored packages.
- Aliases such as `import azure.ai.projects.models as models`.
- Imported model and enum names.
- Client chains such as `client.beta.routines.list`.
- File paths and source line numbers.

It also searches `docs/` and `README.md` for exact SDK symbols and operations.
Matches are ranked as follows:

- **High confidence:** exact model, enum, method, or operation-chain match.
- **Medium confidence:** a new capability matches an existing owning area such
  as agents, evaluations, toolboxes, indexes, memory, or red teaming.
- **Low confidence:** no direct symbol or credible ownership match.

Only high- and medium-confidence features create issues. Low-confidence results
remain in the generated report for manual inspection.

## GitHub issue contract

The watcher creates one issue per package and feature-bearing release. The
title follows this format:

```text
[Foundry SDK feature] <package> <version>
```

Each issue contains:

- The version currently pinned by Cosmopilot.
- The published version and publication date.
- Immutable PyPI and tagged-changelog links.
- The detected feature entries.
- Matching local files and line numbers.
- Breaking changes and dependency requirements needed for adoption.
- A proposed source, test, dependency, and documentation checklist.
- Focused unit-test and full non-integration test commands.

The body includes a stable marker for deduplication:

```html
<!-- foundry-watch:<package>:<version> -->
```

Before creating an issue, the workflow searches both open and closed issues for
the marker. Closing or rejecting a proposal therefore does not cause it to be
recreated.

## Documentation digest

The documentation collector queries recent commits affecting
`articles/foundry`. It records added, modified, and removed Markdown or YAML
files, while excluding media files and generated redirection noise.

The resulting digest:

- Groups changes by Foundry documentation area.
- Highlights changes to `whats-new-foundry.md`.
- Links to source commits and changed files.
- Adds overlapping documentation links to relevant SDK issues.
- Appears in the GitHub Actions job summary and uploaded artifacts.

Documentation-only activity never opens a GitHub issue.

## Proposed implementation

The implementation consists of these files:

- `scripts/foundry_watch.py`: dependency parsing, upstream collection, release
  classification, impact mapping, report formatting, and issue publishing.
- `tests/test_foundry_watch.py`: deterministic tests using local fixtures and
  fake HTTP responses.
- `.github/workflows/foundry-watch.yml`: weekly and manually dispatched runs.

The script should use the Python standard library, including `urllib.request`,
`json`, `ast`, and `argparse`. Network requests must use an identifying user
agent, bounded timeouts, and limited retries for rate limits and transient
server errors.

The workflow should:

- Run each Monday at 09:00 UTC.
- Support manual `dry_run` and `docs_lookback_days` inputs.
- Use Python 3.11.
- Grant only `contents: read` and `issues: write` permissions.
- Use the repository-provided `GITHUB_TOKEN`.
- Write a Markdown digest and JSON report under the runner temporary directory.
- Append the digest to `GITHUB_STEP_SUMMARY`.
- Upload both reports with `actions/upload-artifact`.

No committed checkpoint is required. Existing issue markers provide SDK issue
state, and the bounded documentation lookback window provides the docs digest.

## Failure behavior

SDK detection must fail the workflow when PyPI or both changelog sources cannot
be read for a candidate release. The watcher must not silently treat an
unclassified release as checked.

Documentation collection is non-blocking. If the Microsoft Learn source cannot
be queried, the SDK check continues and the digest contains a prominent
warning.

Upstream changelog and documentation text must be treated as untrusted input.
The issue formatter must preserve text as quoted evidence, avoid executable
content, and never log credentials or authorization headers.

## Validation

The implementation should be validated with:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_foundry_watch.py -v
PYTHONPATH=src .venv/bin/python -m pytest -m 'not integration' --tb=short
```

A networked dry run should then confirm that the watcher:

- Reads the current exact pins from `requirements.txt`.
- Detects only newer versions already published on PyPI.
- Excludes fixes-only and unreleased versions.
- Produces a Microsoft Foundry documentation digest.
- Does not create an issue in dry-run mode.
- Produces the same issue marker on repeated runs.

For the current `azure-ai-projects==2.4.0` baseline, the `2.5.0` regression
fixture should demonstrate that the report can identify relevant feature and
adoption evidence, including routines pagination changes, optimization model
renames, and the `openai>=3.0.0` dependency requirement.