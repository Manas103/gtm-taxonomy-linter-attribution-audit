"""Lints one campaign-launch-sheet row (a planned link) against the
taxonomy (taxonomy.py) and the campaign registry (registry.py), returning
every violation it finds, each naming the exact rule broken. A row with
zero violations is clean; a row is never partially flagged without saying
which rule, because every rule function in taxonomy.py returns a tagged
RuleViolation or None, never a bare boolean.
"""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qsl, urlsplit

from tracking_audit import taxonomy
from tracking_audit.registry import RegisteredCampaign


@dataclass(frozen=True)
class LaunchLinkRow:
    row_id: int
    url: str


@dataclass(frozen=True)
class LintViolation:
    row_id: int
    rule_id: str
    message: str


def _query_pairs(url: str) -> list[tuple[str, str]]:
    query = urlsplit(url).query
    return parse_qsl(query, keep_blank_values=True)


def lint_row(row: LaunchLinkRow, registry: dict[str, RegisteredCampaign]) -> list[LintViolation]:
    violations: list[LintViolation] = []
    parts = urlsplit(row.url)
    pairs = _query_pairs(row.url)
    by_key = dict(pairs)  # last-wins for lookups; duplicate detection uses `pairs` itself

    def add(v) -> None:
        if v is not None:
            violations.append(LintViolation(row.row_id, v.rule_id, v.message))

    add(taxonomy.rule_https(row.url))
    add(taxonomy.rule_landing_domain(parts.netloc))
    add(taxonomy.rule_no_duplicate_params(pairs))
    add(taxonomy.rule_required_params_present(pairs))

    source = by_key.get("utm_source")
    medium = by_key.get("utm_medium")
    campaign = by_key.get("utm_campaign")

    add(taxonomy.rule_source_known(source))
    add(taxonomy.rule_medium_known_for_source(source, medium))
    add(taxonomy.rule_campaign_code_shape(campaign))
    add(taxonomy.rule_campaign_case(campaign))

    if campaign is not None and taxonomy.CAMPAIGN_CODE_RE.match(campaign) and campaign not in registry:
        violations.append(
            LintViolation(row.row_id, "campaign_not_registered", f"utm_campaign {campaign!r} is not in the campaign registry")
        )

    return violations


@dataclass
class LintReport:
    total_rows: int
    violations: list[LintViolation]

    @property
    def clean_rows(self) -> int:
        flagged = {v.row_id for v in self.violations}
        return self.total_rows - len(flagged)


def lint_sheet(rows: list[LaunchLinkRow], registry: dict[str, RegisteredCampaign]) -> LintReport:
    all_violations: list[LintViolation] = []
    for row in rows:
        all_violations.extend(lint_row(row, registry))
    return LintReport(total_rows=len(rows), violations=all_violations)
