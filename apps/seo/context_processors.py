from django.conf import settings
from django.http import HttpRequest


def canonical_url(request: HttpRequest) -> dict[str, str]:
    """Self-referencing canonical URL, query string stripped.

    This is also how the SEO rule ("canonical for filtered
    lists points at the unfiltered list") is satisfied for /work/?kind=...:
    the canonical always points at the bare path. Real tag landing pages
    (/work/tag/<slug>/) are their own path, so they canonicalize to
    themselves correctly with no special-casing needed.
    """
    return {"CANONICAL_URL": f"{settings.SITE_URL}{request.path}"}
