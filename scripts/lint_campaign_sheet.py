"""The CI entry point: lints a real campaign launch sheet (a CSV of
row_id,url pairs) against the taxonomy and the registry, prints every
violation by exact rule, and exits 1 if there is even one, so a malformed
link cannot merge.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from tracking_audit.linter import LaunchLinkRow, lint_sheet
from tracking_audit.registry import build_registry

DEFAULT_SHEET = Path(__file__).resolve().parent.parent / "data" / "launch_sheet.csv"


def load_rows(path: Path) -> list[LaunchLinkRow]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [LaunchLinkRow(row_id=int(r["row_id"]), url=r["url"]) for r in reader]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sheet", default=str(DEFAULT_SHEET))
    args = parser.parse_args()

    registry = build_registry()
    rows = load_rows(Path(args.sheet))
    report = lint_sheet(rows, registry)

    print(f"sheet: {args.sheet}")
    print(f"rows checked: {report.total_rows}")
    print(f"clean rows: {report.clean_rows} / {report.total_rows}")
    print(f"violations: {len(report.violations)}")
    for v in report.violations:
        print(f"  - row {v.row_id} [{v.rule_id}]: {v.message}")

    return 1 if report.violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
