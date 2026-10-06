"""Seeded, synthetic sessions with a ground-truth label the recovery
algorithm is never given: `true_origin_campaign`. No real visitor, no real
session. This is what makes "traced back out of direct/none to the campaign
that earned them" measurable rather than asserted: the generator knows which
campaign actually earned a session, and the battery checks the recovery
algorithm's answer against that, never against itself.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from tracking_audit.registry import RegisteredCampaign

LOOKBACK_DAYS = 30


@dataclass(frozen=True)
class Session:
    session_id: int
    visitor_id: int
    day: float  # days since day 0 of the simulation window
    utm_campaign: str | None  # None means the session arrived with no UTM at all
    true_origin_campaign: str | None  # ground truth; never given to the recovery algorithm


def build_sessions(
    seed: int,
    registry: dict[str, RegisteredCampaign],
    n_campaign_visitors: int = 300,
    n_organic_visitors: int = 200,
) -> list[Session]:
    rng = random.Random(seed)
    campaigns = list(registry.keys())
    sessions: list[Session] = []
    session_id = 0
    visitor_id = 0

    for _ in range(n_campaign_visitors):
        campaign = rng.choice(campaigns)
        t0 = rng.uniform(0, 60)
        sessions.append(Session(session_id, visitor_id, t0, campaign, campaign))
        session_id += 1
        n_followups = rng.randint(1, 3)
        for _ in range(n_followups):
            if rng.random() < 0.7:
                delta = rng.uniform(1, LOOKBACK_DAYS - 1)  # recoverable: inside the window
                true_origin = campaign
            else:
                delta = rng.uniform(LOOKBACK_DAYS + 5, LOOKBACK_DAYS + 25)  # genuinely out of window
                true_origin = None
            sessions.append(Session(session_id, visitor_id, t0 + delta, None, true_origin))
            session_id += 1
        visitor_id += 1

    for _ in range(n_organic_visitors):
        n_sessions = rng.randint(1, 3)
        base_day = rng.uniform(0, 60)
        for _ in range(n_sessions):
            day = base_day + rng.uniform(0, 10)
            sessions.append(Session(session_id, visitor_id, day, None, None))
            session_id += 1
        visitor_id += 1

    return sessions
