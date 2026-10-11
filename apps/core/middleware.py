from __future__ import annotations

import ipaddress
from collections.abc import Callable

from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponse, HttpResponsePermanentRedirect

from .net import client_ip


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


def _is_admin_path(request: HttpRequest) -> bool:
    return request.path.startswith(f"/{settings.ADMIN_URL}")


class AdminAccessMiddleware:
    """Zero-trust gate in front of the admin, before auth even runs.

    If ADMIN_ALLOWED_IPS is set, any other client gets a plain 404 -- the
    admin's existence isn't confirmed to them at all, so there's no login
    form to brute-force or fingerprint. Uses apps.core.net.client_ip so the
    check can't be bypassed with a forged X-Forwarded-For. Admin responses
    are also marked no-store so authenticated pages never land in a shared
    or browser cache.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not _is_admin_path(request):
            return self.get_response(request)

        allowed = getattr(settings, "ADMIN_ALLOWED_IPS", [])
        if allowed and not _ip_allowed(client_ip(request), allowed):
            raise Http404

        response = self.get_response(request)
        response["Cache-Control"] = "no-store, private"
        return response


def _ip_allowed(ip: str, allowed: list[str]) -> bool:
    try:
        address = ipaddress.ip_address(ip)
    except ValueError:
        return False
    for entry in allowed:
        try:
            if address in ipaddress.ip_network(entry, strict=False):
                return True
        except ValueError:
            continue
    return False


class IsolationHeadersMiddleware:
    """Cross-origin isolation headers Django doesn't set on its own.

    Cross-Origin-Opener-Policy is Django's SECURE_CROSS_ORIGIN_OPENER_POLICY;
    this adds Cross-Origin-Resource-Policy (other origins can't embed our
    responses -- uploaded files included) and Origin-Agent-Cluster.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        response.setdefault("Cross-Origin-Resource-Policy", "same-origin")
        response.setdefault("Origin-Agent-Cluster", "?1")
        response.setdefault("X-Permitted-Cross-Domain-Policies", "none")
        return response


class NoindexAdminAndApiMiddleware:
    """X-Robots-Tag: noindex on admin and API paths."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        if _is_admin_path(request) or request.path.startswith("/api/"):
            response["X-Robots-Tag"] = "noindex"
        return response
