from tracking_audit.linter import LaunchLinkRow, lint_row, lint_sheet


def _first_campaign(registry):
    return next(iter(registry.values()))


def test_a_well_formed_registered_link_is_clean(registry):
    c = _first_campaign(registry)
    url = f"https://www.example-saas.com/lp?utm_source={c.source}&utm_medium={c.medium}&utm_campaign={c.code}"
    row = LaunchLinkRow(0, url)
    assert lint_row(row, registry) == []


def test_missing_utm_medium_is_flagged_by_name(registry):
    c = _first_campaign(registry)
    url = f"https://www.example-saas.com/lp?utm_source={c.source}&utm_campaign={c.code}"
    row = LaunchLinkRow(0, url)
    violations = lint_row(row, registry)
    assert any(v.rule_id == "missing_required_param" for v in violations)


def test_unregistered_but_shape_valid_campaign_is_flagged(registry):
    c = _first_campaign(registry)
    url = (
        f"https://www.example-saas.com/lp?utm_source={c.source}&utm_medium={c.medium}"
        f"&utm_campaign=totallymadeup-theme-2099q1"
    )
    row = LaunchLinkRow(0, url)
    violations = lint_row(row, registry)
    assert any(v.rule_id == "campaign_not_registered" for v in violations)


def test_duplicate_param_is_flagged():
    row = LaunchLinkRow(
        0,
        "https://www.example-saas.com/lp?utm_source=google&utm_source=google&utm_medium=cpc&utm_campaign=x-y-2026q1",
    )
    violations = lint_row(row, {})
    assert any(v.rule_id == "duplicate_query_param" for v in violations)


def test_lint_sheet_reports_clean_row_count(registry):
    c = _first_campaign(registry)
    clean = LaunchLinkRow(0, f"https://www.example-saas.com/lp?utm_source={c.source}&utm_medium={c.medium}&utm_campaign={c.code}")
    broken = LaunchLinkRow(1, "http://www.example-saas.com/lp?utm_source=google&utm_medium=cpc&utm_campaign=x-y-2026q1")
    report = lint_sheet([clean, broken], registry)
    assert report.total_rows == 2
    assert report.clean_rows == 1
    assert len(report.violations) >= 1
