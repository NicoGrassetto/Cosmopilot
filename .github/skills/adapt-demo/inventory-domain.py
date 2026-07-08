#!/usr/bin/env python3
"""Inventory domain-specific content in the demo repository.

Part of the `adapt-demo` skill. Scans the repo for tokens that encode the
*current* demo domain (brand name, personas, entities, sample scenarios) so you
can re-theme every location for a new target audience — and re-run afterwards to
confirm no stale references remain.

Usage:
    python .github/skills/adapt-demo/inventory-domain.py
    python .github/skills/adapt-demo/inventory-domain.py --root /path/to/repo
    python .github/skills/adapt-demo/inventory-domain.py --extra myoldbrand term2
    python .github/skills/adapt-demo/inventory-domain.py --json

Exit code is 0 always; the report is informational. A summary count is printed
at the end so you can tell at a glance whether the repo is clean.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# The repo contains non-cp1252 characters (e.g. box-drawing in diagrams). Force
# UTF-8 output so the report never crashes on a Windows console.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass

# Tokens that encode the current ("Cosmopilot" ops + "Adventure Works") domain.
# Matched case-insensitively as whole-ish words. Extend with --extra.
DEFAULT_TOKENS = [
    "cosmopilot",
    "cosmos db",
    "cosmosdb",
    "telemetry",
    "operational",
    "incident",
    "anomaly",
    "anomalies",
    "change feed",
    "change-feed",
    "changefeed",
    "adventure works",
    "adventure-works",
    "trail guide",
    "detector",
    "diagnostician",
    "remediator",
]

# Directories to skip entirely.
SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    ".svelte-kit",
    "results",
    ".pytest_cache",
    ".mypy_cache",
}

# File names / suffixes to skip (lockfiles, binaries, assets).
SKIP_FILES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml"}
SKIP_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg",
    ".pdf", ".zip", ".gz", ".tar", ".woff", ".woff2", ".ttf", ".eot",
    ".mp3", ".mp4", ".mov", ".lock",
}

# This skill's own directory is skipped so the skill docs don't self-report.
SKILL_DIR_NAME = "adapt-demo"


def find_repo_root(explicit: str | None) -> Path:
    """Resolve the repo root: explicit arg, else infer from this script's path."""
    if explicit:
        return Path(explicit).resolve()
    # Script lives at <repo>/.github/skills/adapt-demo/inventory-domain.py
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / ".git").exists() or (parent / ".github").is_dir():
            # Prefer the directory that *contains* .github (the repo root).
            if (parent / ".github").is_dir() and parent.name != ".github":
                return parent
    # Fallback: four levels up (…/adapt-demo -> …/skills -> …/.github -> repo).
    return here.parents[3] if len(here.parents) >= 4 else Path.cwd()


def build_pattern(tokens: list[str]) -> re.Pattern[str]:
    escaped = sorted({re.escape(t.strip()) for t in tokens if t.strip()}, key=len, reverse=True)
    return re.compile("|".join(escaped), re.IGNORECASE)


def should_skip(path: Path, skill_dir: Path) -> bool:
    if skill_dir in path.parents:
        return True
    if path.name in SKIP_FILES:
        return True
    if path.suffix.lower() in SKIP_SUFFIXES:
        return True
    return False


def scan(root: Path, pattern: re.Pattern[str], skill_dir: Path) -> dict[str, list[tuple[int, str]]]:
    findings: dict[str, list[tuple[int, str]]] = {}
    for path in sorted(root.rglob("*")):
        if path.is_dir():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if should_skip(path, skill_dir):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue  # binary or unreadable
        hits: list[tuple[int, str]] = []
        for lineno, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                hits.append((lineno, line.strip()[:160]))
        if hits:
            rel = path.relative_to(root).as_posix()
            findings[rel] = hits
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", help="Repo root to scan (default: auto-detect).")
    parser.add_argument("--extra", nargs="*", default=[], help="Additional tokens to search for.")
    parser.add_argument("--only", nargs="*", help="Search ONLY these tokens (ignore defaults).")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text report.")
    args = parser.parse_args()

    root = find_repo_root(args.root)
    skill_dir = Path(__file__).resolve().parent
    tokens = list(args.only) if args.only else DEFAULT_TOKENS + list(args.extra)
    pattern = build_pattern(tokens)

    findings = scan(root, pattern, skill_dir)
    total_files = len(findings)
    total_hits = sum(len(v) for v in findings.values())

    if args.json:
        print(json.dumps({
            "root": str(root),
            "tokens": tokens,
            "files": total_files,
            "matches": total_hits,
            "findings": findings,
        }, indent=2))
        return 0

    print(f"Domain inventory for: {root}")
    print(f"Tokens: {', '.join(tokens)}")
    print("=" * 72)
    if not findings:
        print("No domain tokens found — repo looks clean for these tokens.")
    for rel, hits in findings.items():
        print(f"\n{rel}  ({len(hits)} match{'es' if len(hits) != 1 else ''})")
        for lineno, line in hits:
            print(f"  {lineno:>5}: {line}")
    print("\n" + "=" * 72)
    print(f"Summary: {total_hits} match(es) across {total_files} file(s).")
    if findings:
        print("Re-theme each location above, then re-run to confirm it is clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
