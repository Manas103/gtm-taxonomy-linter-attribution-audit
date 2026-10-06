"""The tracking taxonomy a campaign launch sheet is linted against: the
fixed vocabulary and naming rules every planned link's UTM parameters must
follow before it ships. No row is linted against anything not written down
here; a rule the linter enforces that is not in this file would be a rule
nobody could audit.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

ALLOWED_SOURCES: tuple[str, ...] = ("google", "facebook", "linkedin", "newsletter", "partner-affiliate")

# Which utm_medium values are legal for a given utm_source. A source/medium
# pair not in this map is a taxonomy violation even if both values are
# individually valid for some other source.
ALLOWED_MEDIUM_BY_SOURCE: dict[str, tuple[str, ...]] = {
    "google": ("cpc", "organic"),
    "facebook": ("paid-social", "organic-social"),
    "linkedin": ("paid-social", "organic-social"),
    "newsletter": ("email",),
    "partner-affiliate": ("affiliate",),
}

ALLOWED_LANDING_DOMAINS: tuple[str, ...] = ("www.example-saas.com", "app.example-saas.com")

# campaign code shape: <product>-<theme>-<yyyy>q<1-4>, all lowercase, hyphen
# separated, e.g. "coresuite-springsale-2026q3"
CAMPAIGN_CODE_RE = re.compile(r"^[a-z0-9]+-[a-z0-9]+-20\d{2}q[1-4]$")

REQUIRED_PARAMS: tuple[str, ...] = ("utm_source", "utm_medium", "utm_campaign")


@dataclass(frozen=True)
class RuleViolation:
    rule_id: str
    message: str


def rule_source_known(source: str | None) -> RuleViolation | None:
    if source is None:
        return None  # handled by missing_required_param
    if source not in ALLOWED_SOURCES:
        return RuleViolation("unknown_utm_source", f"utm_source {source!r} is not in the allowed vocabulary")
    return None


def rule_medium_known_for_source(source: str | None, medium: str | None) -> RuleViolation | None:
    if source is None or medium is None:
        return None
    allowed = ALLOWED_MEDIUM_BY_SOURCE.get(source)
    if allowed is None:
        return None  # unknown_utm_source already covers an unrecognized source
    if medium not in allowed:
        return RuleViolation(
            "medium_not_valid_for_source",
            f"utm_medium {medium!r} is not valid for utm_source {source!r} (allowed: {allowed})",
        )
    return None


def rule_campaign_code_shape(campaign: str | None) -> RuleViolation | None:
    if campaign is None:
        return None
    if not CAMPAIGN_CODE_RE.match(campaign):
        return RuleViolation(
            "campaign_code_wrong_shape",
            f"utm_campaign {campaign!r} does not match <product>-<theme>-<yyyy>q<1-4>",
        )
    return None


def rule_campaign_case(campaign: str | None) -> RuleViolation | None:
    if campaign is None:
        return None
    if campaign != campaign.lower():
        return RuleViolation("campaign_code_not_lowercase", f"utm_campaign {campaign!r} must be all lowercase")
    return None


def rule_https(url: str) -> RuleViolation | None:
    if not url.startswith("https://"):
        return RuleViolation("not_https", f"landing URL {url!r} must use https")
    return None


def rule_landing_domain(domain: str) -> RuleViolation | None:
    if domain not in ALLOWED_LANDING_DOMAINS:
        return RuleViolation("landing_domain_not_allowed", f"landing domain {domain!r} is not in the allowed list")
    return None


def rule_no_duplicate_params(query_pairs: list[tuple[str, str]]) -> RuleViolation | None:
    keys = [k for k, _ in query_pairs]
    seen = set()
    for k in keys:
        if k in seen:
            return RuleViolation("duplicate_query_param", f"query parameter {k!r} appears more than once")
        seen.add(k)
    return None


def rule_required_params_present(query_pairs: list[tuple[str, str]]) -> RuleViolation | None:
    present = {k for k, _ in query_pairs}
    missing = [p for p in REQUIRED_PARAMS if p not in present]
    if missing:
        return RuleViolation("missing_required_param", f"missing required parameter(s): {missing}")
    return None
