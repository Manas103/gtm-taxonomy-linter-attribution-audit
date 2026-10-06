import pytest

from tracking_audit.registry import build_registry


@pytest.fixture
def registry():
    return build_registry()
