from django.conf import settings
from django.http import HttpRequest


def site_meta(request: HttpRequest) -> dict[str, str]:
    """Site-wide values available to every template (name, canonical site URL)."""
    return {
        "SITE_NAME": settings.SITE_NAME,
        "SITE_URL": settings.SITE_URL,
        "GOOGLE_SITE_VERIFICATION": settings.GOOGLE_SITE_VERIFICATION,
        "BING_SITE_VERIFICATION": settings.BING_SITE_VERIFICATION,
    }
