from django.conf import settings

from .base import Provider
from .fake import FakeProvider


def get_provider() -> Provider:
    """Selects a provider adapter by the AI_PROVIDER env var.

    Only "fake" is implemented so far.
    real adapter behind this same interface once the owner picks a provider
    (undecided as of 2026-09-30, see docs/TODO_OWNER.md). Any other value
    fails loudly rather than silently falling back, so a misconfigured
    production deploy is never mistaken for a working one.
    """
    provider = getattr(settings, "AI_PROVIDER", "fake")
    if provider == "fake":
        return FakeProvider()
    raise ValueError(
        f"Unknown AI_PROVIDER {provider!r}. Only 'fake' is implemented; "
        "add a real adapter in apps/ai/providers/ before setting this."
    )
