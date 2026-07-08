"""
Report generator — aggregates evaluation results into a readable summary.

Usage:
    python report.py results/adventure-works_20250701_120000.json
    python report.py results/  # Process all results in directory
"""

import argparse
import json
import sys
from pathlib import Path

import yaml


def load_thresholds() -> dict:
    """Load pass/fail thresholds from config."""
    config_path = Path(__file__).parent / "config" / "thresholds.yaml"
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f)
    return {}


def flatten_thresholds(thresholds: dict) -> dict:
    """Flatten nested threshold config into {metric: value}."""
    flat = {}
    for category, metrics in thresholds.items():
        if isinstance(metrics, dict):
            flat.update(metrics)
    return flat


def generate_report(results_path: Path) -> str:
    """Generate a markdown report from evaluation results."""
    with open(results_path) as f:
        data = json.load(f)

    thresholds = flatten_thresholds(load_thresholds())
    metrics = data.get("metrics", data)

    lines = []
    lines.append(f"# Evaluation Report")
    lines.append(f"**Source:** `{results_path.name}`\n")

    # Summary table
    lines.append("| Metric | Score | Threshold | Status |")
    lines.append("|--------|-------|-----------|--------|")

    passed = 0
    failed = 0
    for metric, value in sorted(metrics.items()):
        if not isinstance(value, (int, float)):
            continue
        threshold = thresholds.get(metric)
        if threshold is not None:
            status = "✅ PASS" if value >= threshold else "❌ FAIL"
            if value >= threshold:
                passed += 1
            else:
                failed += 1
        else:
            status = "—"
        lines.append(f"| {metric} | {value:.2f} | {threshold or '—'} | {status} |")

    lines.append(f"\n**Summary:** {passed} passed, {failed} failed, {len(metrics)} total metrics")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate evaluation report.")
    parser.add_argument("path", help="Path to results JSON file or results directory")
    parser.add_argument("--output", "-o", help="Output markdown file path")
    args = parser.parse_args()

    path = Path(args.path)

    if path.is_dir():
        files = sorted(path.glob("*.json"))
    elif path.is_file():
        files = [path]
    else:
        print(f"Error: {path} not found.")
        sys.exit(1)

    reports = []
    for f in files:
        print(f"Processing: {f.name}")
        report = generate_report(f)
        reports.append(report)

    full_report = "\n\n---\n\n".join(reports)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(full_report)
        print(f"Report written to: {output_path}")
    else:
        print(full_report)


if __name__ == "__main__":
    main()
