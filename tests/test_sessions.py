from tracking_audit.sessions import LOOKBACK_DAYS, build_sessions


def test_sessions_are_deterministic(registry):
    a = build_sessions(42, registry)
    b = build_sessions(42, registry)
    assert a == b


def test_every_campaign_visitor_first_session_is_tagged(registry):
    sessions = build_sessions(5, registry, n_campaign_visitors=50, n_organic_visitors=0)
    by_visitor = {}
    for s in sessions:
        by_visitor.setdefault(s.visitor_id, []).append(s)
    for visitor_sessions in by_visitor.values():
        ordered = sorted(visitor_sessions, key=lambda s: s.day)
        assert ordered[0].utm_campaign is not None


def test_organic_visitors_never_have_a_true_origin_campaign(registry):
    sessions = build_sessions(6, registry, n_campaign_visitors=0, n_organic_visitors=50)
    assert all(s.true_origin_campaign is None and s.utm_campaign is None for s in sessions)


def test_out_of_window_followups_have_no_true_origin(registry):
    sessions = build_sessions(7, registry, n_campaign_visitors=200, n_organic_visitors=0)
    by_visitor = {}
    for s in sessions:
        by_visitor.setdefault(s.visitor_id, []).append(s)
    found_out_of_window = False
    for visitor_sessions in by_visitor.values():
        ordered = sorted(visitor_sessions, key=lambda s: s.day)
        first = ordered[0]
        for s in ordered[1:]:
            gap = s.day - first.day
            if gap > LOOKBACK_DAYS:
                found_out_of_window = True
                assert s.true_origin_campaign is None
    assert found_out_of_window, "test fixture did not exercise the out-of-window case"
