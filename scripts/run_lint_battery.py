"""The lint battery: 400 genuinely valid launch-sheet links must produce
zero violations, and 180 deliberately broken links (20 for each of 9 named
violation kinds) must each be caught by the exact rule they were built to
break.
"""
from __future__ import annotations

from collections import Counter

from tracking_audit.launch_sheet import VIOLATION_KINDS, build_broken_rows, build_valid_rows
from tracking_audit.linter import lint_row, lint_sheet
from tracking_audit.registry import build_registry

VALID_SEED = 20260702
BROKEN_SEED = 20260703


def main() -> int:
    registry = build_registry()
    valid_rows = build_valid_rows(VALID_SEED, registry, n=400)
    broken_pairs = build_broken_rows(BROKEN_SEED, registry, per_kind=20)

    valid_report = lint_sheet(valid_rows, registry)
    false_flags = valid_report.violations

    caught_by_kind: Counter[str] = Counter()
    misses = []
    for row, expected_kind in broken_pairs:
        violations = lint_row(row, registry)
        rule_ids = {v.rule_id for v in violations}
        if expected_kind in rule_ids:
            caught_by_kind[expected_kind] += 1
        else:
            misses.append((row.row_id, expected_kind, rule_ids))

    total_caught = sum(caught_by_kind.values())
    total_broken = len(broken_pairs)

    print(f"valid links checked: {len(valid_rows)}")
    print(f"false flags on valid links: {len(false_flags)} / {len(valid_rows)}")
    for v in false_flags[:10]:
        print(f"  - row {v.row_id}: {v.rule_id}: {v.message}")
    print()
    print(f"seeded violations caught by exact rule: {total_caught} / {total_broken}")
    for kind in VIOLATION_KINDS:
        print(f"  {kind}: {caught_by_kind[kind]} / 20")
    for row_id, expected, got in misses:
        print(f"  - MISS row {row_id}: expected {expected}, got {got}")

    ok = len(false_flags) == 0 and total_caught == total_broken
    print()
    print(f"LINT BATTERY: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
