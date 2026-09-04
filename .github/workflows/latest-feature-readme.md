---
description: Keep the README latest-feature callout current.
on:
  push:
    branches: [main]
    paths-ignore: [README.md]
permissions:
  contents: read
  copilot-requests: write
engine: copilot
checkout:
  fetch-depth: 0
tools:
  edit:
  bash: ["git log", "git show", "git diff", "git status", "git rev-parse"]
safe-outputs:
  create-pull-request:
    title-prefix: "[docs] "
    base-branch: main
    draft: true
    allowed-files: [README.md]
    protected-files: allowed
    fallback-as-issue: false
    if-no-changes: ignore
  report-failure-as-issue: false
---

# Update the latest feature

Inspect `${{ github.event.before }}..${{ github.event.after }}`. Judge implementation,
not commit messages. A feature adds a user- or developer-operable capability;
bug fixes, refactors, tests, docs, dependencies, formatting, renames, assets,
decks, and maintenance do not. A candidate must still exist at `HEAD`.

If there is no genuine feature, call `noop`. Otherwise replace only the content
between `latest-feature:start` and `latest-feature:end` in `README.md` with its
newest surviving feature, preserving the `TIP` callout and factual relative
links. Do not classify maintenance workflows, generated files, or README
updates as features.

Run `git diff --check -- README.md`, then call `create_pull_request` with the
selected commit and evidence in the body.
