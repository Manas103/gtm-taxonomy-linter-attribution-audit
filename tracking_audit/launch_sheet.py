"""Seeded generators for a campaign launch sheet: 400 genuinely valid links
(zero violations) and 180 deliberately broken links, 20 for each of 9 named
violation kinds, each corrupting exactly one aspect of an otherwise-valid
link so the lint battery measures catching a real, isolated defect rather
than a link that happens to be broken in several ways at once.
"""
from __future__ import annotations

import random

from tracking_audit.linter import LaunchLinkRow
from tracking_audit.registry import RegisteredCampaign, build_registry
from tracking_audit.taxonomy import ALLOWED_MEDIUM_BY_SOURCE

_ALL_MEDIUMS = ("cpc", "organic", "paid-social", "organic-social", "email", "affiliate")

VIOLATION_KINDS: tuple[str, ...] = (
    "missing_required_param",
    "unknown_utm_source",
    "medium_not_valid_for_source",
    "campaign_code_wrong_shape",
    "campaign_code_not_lowercase",
    "campaign_not_registered",
    "not_https",
    "landing_domain_not_allowed",
    "duplicate_query_param",
)

_CONTENT_VARIANTS = ("hero-banner", "sidebar", "footer-link", "email-cta", "social-post", "none", "retarget-ad")


def _valid_url(campaign: RegisteredCampaign, content: str) -> str:
    return (
        f"https://www.example-saas.com/lp?utm_source={campaign.source}"
        f"&utm_medium={campaign.medium}&utm_campaign={campaign.code}&utm_content={content}"
    )


def build_valid_rows(seed: int, registry: dict[str, RegisteredCampaign], n: int = 400) -> list[LaunchLinkRow]:
    rng = random.Random(seed)
    campaigns = list(registry.values())
    rows = []
    for i in range(n):
        campaign = campaigns[i % len(campaigns)]
        content = rng.choice(_CONTENT_VARIANTS)
        rows.append(LaunchLinkRow(row_id=i, url=_valid_url(campaign, content)))
    return rows


def _corrupt(kind: str, campaign: RegisteredCampaign, content: str) -> str:
    base = _valid_url(campaign, content)
    if kind == "missing_required_param":
        return base.replace(f"&utm_medium={campaign.medium}", "")
    if kind == "unknown_utm_source":
        return base.replace(f"utm_source={campaign.source}", "utm_source=bing")
    if kind == "medium_not_valid_for_source":
        allowed = ALLOWED_MEDIUM_BY_SOURCE[campaign.source]
        wrong_medium = next(m for m in _ALL_MEDIUMS if m not in allowed)
        return base.replace(f"utm_medium={campaign.medium}", f"utm_medium={wrong_medium}")
    if kind == "campaign_code_wrong_shape":
        mangled = campaign.code.replace("-", "_").upper()
        return base.replace(f"utm_campaign={campaign.code}", f"utm_campaign={mangled}")
    if kind == "campaign_code_not_lowercase":
        mangled = campaign.code[0].upper() + campaign.code[1:]
        return base.replace(f"utm_campaign={campaign.code}", f"utm_campaign={mangled}")
    if kind == "campaign_not_registered":
        fake = campaign.code.rsplit("-", 1)[0] + "-2099q1"
        return base.replace(f"utm_campaign={campaign.code}", f"utm_campaign={fake}")
    if kind == "not_https":
        return base.replace("https://", "http://")
    if kind == "landing_domain_not_allowed":
        return base.replace("www.example-saas.com", "example-saas.net")
    if kind == "duplicate_query_param":
        return base + f"&utm_source={campaign.source}"
    raise ValueError(f"unknown violation kind {kind!r}")


def build_broken_rows(
    seed: int, registry: dict[str, RegisteredCampaign], per_kind: int = 20
) -> list[tuple[LaunchLinkRow, str]]:
    """Returns (row, expected_rule_id) pairs so the battery can check each
    seeded violation was caught by the exact rule it was built to break,
    not just caught by something."""
    rng = random.Random(seed)
    campaigns = list(registry.values())
    out: list[tuple[LaunchLinkRow, str]] = []
    row_id = 100000  # disjoint id space from the valid rows
    for kind in VIOLATION_KINDS:
        for _ in range(per_kind):
            campaign = rng.choice(campaigns)
            content = rng.choice(_CONTENT_VARIANTS)
            url = _corrupt(kind, campaign, content)
            out.append((LaunchLinkRow(row_id=row_id, url=url), kind))
            row_id += 1
    return out
