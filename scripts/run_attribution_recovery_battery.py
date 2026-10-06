"""Measures the attribution recovery claim directly against the ground
truth the session generator attached (and the recovery algorithm never
sees): how many sessions that naive last-touch attribution would report as
"(direct)/(none)" are correctly traced back to the campaign that actually
earned them, how many genuinely organic sessions are correctly left
unattributed, and how many out-of-window touches are correctly NOT
recovered (the deliberate scope boundary).
"""
from __future__ import annotations

from tracking_audit.attribution import naive_channel, recover_attribution
from tracking_audit.registry import build_registry
from tracking_audit.sessions import build_sessions

SEED = 20260704


def main() -> int:
    registry = build_registry()
    sessions = build_sessions(SEED, registry)
    by_id = {s.session_id: s for s in sessions}

    naive_direct = [s for s in sessions if naive_channel(s) == "(direct)/(none)"]
    recoverable = [s for s in naive_direct if s.true_origin_campaign is not None]
    genuinely_organic = [s for s in naive_direct if s.true_origin_campaign is None]

    results = {r.session_id: r for r in recover_attribution(sessions)}

    correctly_recovered = sum(
        1 for s in recoverable if results[s.session_id].recovered_campaign == s.true_origin_campaign
    )
    false_recoveries = sum(1 for s in genuinely_organic if results[s.session_id].recovered_campaign is not None)

    print(f"total sessions: {len(sessions)}")
    print(f"naive (direct)/(none) sessions: {len(naive_direct)}")
    print(f"  of those, genuinely earned by a campaign within the lookback window: {len(recoverable)}")
    print(f"  of those, genuinely organic (no recoverable campaign, ever or in-window): {len(genuinely_organic)}")
    print()
    print(f"correctly traced back to the exact earning campaign: {correctly_recovered} / {len(recoverable)}")
    print(f"false recoveries on genuinely organic sessions: {false_recoveries} / {len(genuinely_organic)}")

    ok = correctly_recovered == len(recoverable) and false_recoveries == 0
    print()
    print(f"ATTRIBUTION RECOVERY BATTERY: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
