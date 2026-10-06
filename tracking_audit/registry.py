"""The campaign registry: every campaign code a launch sheet is allowed to
reference. A link whose utm_campaign has the right shape but was never
actually registered (a typo'd code, or a code copied from last quarter) is
a real, separate failure mode from a malformed code, and is linted against
this registry rather than against the naming regex.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from tracking_audit.taxonomy import ALLOWED_SOURCES, ALLOWED_MEDIUM_BY_SOURCE

DEFAULT_SEED = 20260701
PRODUCTS = ("coresuite", "payhub", "insightsapp")
THEMES = ("springsale", "webinarseries", "partnerkit", "enterpriseupgrade", "renewalpush", "betalaunch")
QUARTERS = ("2026q1", "2026q2", "2026q3", "2026q4")


@dataclass(frozen=True)
class RegisteredCampaign:
    code: str
    source: str
    medium: str


def build_registry(seed: int = DEFAULT_SEED, n: int = 60) -> dict[str, RegisteredCampaign]:
    rng = random.Random(seed)
    registry: dict[str, RegisteredCampaign] = {}
    attempts = 0
    while len(registry) < n and attempts < n * 20:
        attempts += 1
        product = rng.choice(PRODUCTS)
        theme = rng.choice(THEMES)
        quarter = rng.choice(QUARTERS)
        code = f"{product}-{theme}-{quarter}"
        if code in registry:
            continue
        source = rng.choice(ALLOWED_SOURCES)
        medium = rng.choice(ALLOWED_MEDIUM_BY_SOURCE[source])
        registry[code] = RegisteredCampaign(code, source, medium)
    return registry
