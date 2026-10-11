import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _clear_cache():
    """Guardrail policy/rules and the certification nav flag are cached;
    a rolled-back test must never leave cached state for the next one."""
    cache.clear()
    yield
    cache.clear()
