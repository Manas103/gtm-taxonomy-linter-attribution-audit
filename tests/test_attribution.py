from tracking_audit.attribution import naive_channel, recover_attribution
from tracking_audit.sessions import Session


def test_naive_channel_names_direct_none_only_when_there_is_no_utm():
    tagged = Session(0, 0, 1.0, "coresuite-springsale-2026q1", "coresuite-springsale-2026q1")
    direct = Session(1, 0, 2.0, None, None)
    assert naive_channel(tagged) == "coresuite-springsale-2026q1"
    assert naive_channel(direct) == "(direct)/(none)"


def test_recovers_a_direct_session_within_the_lookback_window():
    sessions = [
        Session(0, 1, 0.0, "coresuite-springsale-2026q1", "coresuite-springsale-2026q1"),
        Session(1, 1, 10.0, None, "coresuite-springsale-2026q1"),
    ]
    results = {r.session_id: r.recovered_campaign for r in recover_attribution(sessions)}
    assert results[1] == "coresuite-springsale-2026q1"


def test_does_not_recover_a_direct_session_outside_the_lookback_window():
    sessions = [
        Session(0, 1, 0.0, "coresuite-springsale-2026q1", None),
        Session(1, 1, 45.0, None, None),
    ]
    results = {r.session_id: r.recovered_campaign for r in recover_attribution(sessions)}
    assert results[1] is None


def test_never_recovers_a_session_from_a_different_visitor():
    sessions = [
        Session(0, 1, 0.0, "coresuite-springsale-2026q1", "coresuite-springsale-2026q1"),
        Session(1, 2, 1.0, None, None),  # different visitor, never touched by any campaign
    ]
    results = {r.session_id: r.recovered_campaign for r in recover_attribution(sessions)}
    assert results[1] is None


def test_genuinely_organic_visitor_is_never_recovered():
    sessions = [Session(0, 9, 0.0, None, None), Session(1, 9, 3.0, None, None)]
    results = {r.session_id: r.recovered_campaign for r in recover_attribution(sessions)}
    assert all(v is None for v in results.values())
