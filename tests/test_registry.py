from tracking_audit.registry import build_registry
from tracking_audit.taxonomy import ALLOWED_MEDIUM_BY_SOURCE, CAMPAIGN_CODE_RE


def test_registry_has_the_requested_size():
    registry = build_registry(n=60)
    assert len(registry) == 60


def test_every_registered_code_matches_the_taxonomy_shape(registry):
    for code in registry:
        assert CAMPAIGN_CODE_RE.match(code), code


def test_every_registered_source_medium_pair_is_itself_valid(registry):
    for campaign in registry.values():
        assert campaign.medium in ALLOWED_MEDIUM_BY_SOURCE[campaign.source]


def test_registry_is_deterministic():
    a = build_registry(seed=111, n=30)
    b = build_registry(seed=111, n=30)
    assert a == b
