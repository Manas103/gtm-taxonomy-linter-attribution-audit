from tracking_audit.launch_sheet import VIOLATION_KINDS, build_broken_rows, build_valid_rows
from tracking_audit.linter import lint_row, lint_sheet


def test_build_valid_rows_are_genuinely_clean(registry):
    rows = build_valid_rows(1, registry, n=400)
    report = lint_sheet(rows, registry)
    assert report.violations == []
    assert report.clean_rows == 400


def test_every_broken_row_genuinely_fails_with_its_expected_rule(registry):
    """'180/180 caught by name' is only meaningful if the 180 are genuinely
    broken in exactly the way they claim to be; this is the dedicated check
    for that, the same discipline natural-language-segment-builder's
    test_invalid_dataset.py applies to its own mutation generator."""
    pairs = build_broken_rows(2, registry, per_kind=20)
    assert len(pairs) == 180
    for row, expected_kind in pairs:
        violations = lint_row(row, registry)
        assert violations, f"row {row.row_id} (kind {expected_kind}) produced no violations at all"
        assert any(v.rule_id == expected_kind for v in violations), (
            f"row {row.row_id}: expected {expected_kind}, got {[v.rule_id for v in violations]}"
        )


def test_every_violation_kind_is_represented_exactly_per_kind_count(registry):
    pairs = build_broken_rows(3, registry, per_kind=20)
    counts = {}
    for _, kind in pairs:
        counts[kind] = counts.get(kind, 0) + 1
    assert counts == {k: 20 for k in VIOLATION_KINDS}
