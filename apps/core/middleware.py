from __future__ import annotations

from collections.abc import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponsePermanentRedirect


class CanonicalHostMiddleware:
    """Redirect any non-canonical host (e.g. www) to the one true host.

    Controlled by SITE_URL: if its host differs from the request host, the
    request is 301-redirected, preserving path and query string. A no-op
    when SITE_URL is unset or already matches (e.g. local dev on localhost).
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        canonical_host, canonical_scheme = self._canonical_origin()
        if (
            canonical_host
            and request.get_host().split(":")[0] != canonical_host
            and not settings.DEBUG
        ):
            url = f"{canonical_scheme}://{canonical_host}{request.get_full_path()}"
            return HttpResponsePermanentRedirect(url)
        return self.get_response(request)

    @staticmethod
    def _canonical_origin() -> tuple[str, str]:
        from urllib.parse import urlparse

        parsed = urlparse(settings.SITE_URL)
        return parsed.netloc.split(":")[0], parsed.scheme or "https"


class PermissionsPolicyMiddleware:
    """Sets Permissions-Policy, disabling browser features this site never
    uses. No dedicated package for one header."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        policy = getattr(settings, "PERMISSIONS_POLICY", "")
        if policy:
            response["Permissions-Policy"] = policy
        return response


class NoindexAdminAndApiMiddleware:
    """X-Robots-Tag: noindex on admin and API paths."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        if request.path.startswith(f"/{settings.ADMIN_URL}") or request.path.startswith("/api/"):
            response["X-Robots-Tag"] = "noindex"
        return response
