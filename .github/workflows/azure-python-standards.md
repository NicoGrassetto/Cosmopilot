---
description: Remediate Python standards violations after changes reach main.
on:
  push:
    branches: [main]
    paths: ["**/*.py"]
permissions:
  contents: read
  copilot-requests: write
engine: copilot
checkout:
  fetch-depth: 0
network:
  allowed: [defaults, python]
tools:
  edit:
  bash:
    - "git log"
    - "git show"
    - "git diff"
    - "git status"
    - "git rev-parse"
    - "python -m compileall"
    - "python -m pip install"
    - "env PYTHONPATH=src python -m pytest"
safe-outputs:
  create-pull-request:
    title-prefix: "[python-standards] "
    base-branch: main
    draft: true
    allowed-files: ["**/*.py"]
    protected-files: allowed
    fallback-as-issue: false
    if-no-changes: ignore
  report-failure-as-issue: false
---

# Enforce Python standards

Review Python changes in `${{ github.event.before }}..${{ github.event.after }}`
and only their directly affected context. Apply, in order:

1. Repository instructions.
2. [Azure SDK guidance](https://azure.github.io/azure-sdk/),
   [Python design](https://azure.github.io/azure-sdk/python_design.html),
   [documentation](https://azure.github.io/azure-sdk/python_documentation.html),
   and [Microsoft Python guidance](https://learn.microsoft.com/azure/developer/python/sdk/fundamentals/language-design-guidelines).
3. Official Python [style](https://peps.python.org/pep-0008/),
   [docstrings](https://peps.python.org/pep-0257/),
   [typing](https://typing.python.org/en/latest/spec/), and
   [packaging](https://packaging.python.org/) standards for uncovered topics.

Enforce `MUST`, `DO`, and `DO NOT`; apply `SHOULD` only when unambiguous. This
repository consumes Azure SDKs, so do not impose SDK distribution requirements
on application code. Fix only objective violations without redesigning behavior
or breaking public APIs. Preserve local formatting and ignore unrelated legacy
code. Check Python 3.10 compatibility, API naming and typing, docstrings,
authentication and cleanup, exceptions, logging, tests, and secret handling.

If no correction is needed, call `noop`. Otherwise compile changed files, run
focused non-integration tests, run `git diff --check`, and call
`create_pull_request` with cited violations and validation results.
