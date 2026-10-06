from tracking_audit import taxonomy


def test_rule_source_known_flags_an_unknown_source():
    v = taxonomy.rule_source_known("bing")
    assert v is not None and v.rule_id == "unknown_utm_source"


def test_rule_source_known_accepts_an_allowed_source():
    assert taxonomy.rule_source_known("google") is None


def test_rule_medium_known_for_source_rejects_a_bad_pairing():
    v = taxonomy.rule_medium_known_for_source("google", "paid-social")
    assert v is not None and v.rule_id == "medium_not_valid_for_source"


def test_rule_campaign_code_shape_rejects_missing_quarter():
    v = taxonomy.rule_campaign_code_shape("coresuite-springsale")
    assert v is not None and v.rule_id == "campaign_code_wrong_shape"


def test_rule_campaign_code_shape_accepts_a_well_formed_code():
    assert taxonomy.rule_campaign_code_shape("coresuite-springsale-2026q3") is None


def test_rule_campaign_case_rejects_uppercase():
    v = taxonomy.rule_campaign_case("Coresuite-springsale-2026q3")
    assert v is not None and v.rule_id == "campaign_code_not_lowercase"
