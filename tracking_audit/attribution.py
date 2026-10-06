"""Re-attributes a direct/none session to the campaign that actually earned
it, within a bounded lookback window, without ever looking at the ground
truth the session generator attached for scoring.

The model is last-tagged-touch: for a visitor's session with no UTM
parameters, look back through that same visitor's own prior sessions (never
a different visitor's) for the most recent one that actually carried a
utm_campaign, and only within LOOKBACK_DAYS. A tagged touch older than the
window, or no tagged touch at all, means the session stays genuinely
unattributed; this is a deliberate scope boundary, not a missed case.
"""
from __future__ import annotations

from dataclasses import dataclass

from tracking_audit.sessions import LOOKBACK_DAYS, Session


def naive_channel(session: Session) -> str:
    return "(direct)/(none)" if session.utm_campaign is None else session.utm_campaign


@dataclass
class RecoveryResult:
    session_id: int
    recovered_campaign: str | None


def recover_attribution(sessions: list[Session], lookback_days: float = LOOKBACK_DAYS) -> list[RecoveryResult]:
    by_visitor: dict[int, list[Session]] = {}
    for s in sessions:
        by_visitor.setdefault(s.visitor_id, []).append(s)

    results: dict[int, RecoveryResult] = {}
    for visitor_id, visitor_sessions in by_visitor.items():
        ordered = sorted(visitor_sessions, key=lambda s: s.day)
        last_tagged_campaign: str | None = None
        last_tagged_day: float | None = None
        for s in ordered:
            if s.utm_campaign is not None:
                last_tagged_campaign = s.utm_campaign
                last_tagged_day = s.day
                results[s.session_id] = RecoveryResult(s.session_id, s.utm_campaign)
                continue
            recovered = None
            if last_tagged_campaign is not None and (s.day - last_tagged_day) <= lookback_days:
                recovered = last_tagged_campaign
            results[s.session_id] = RecoveryResult(s.session_id, recovered)

    return [results[s.session_id] for s in sessions]
