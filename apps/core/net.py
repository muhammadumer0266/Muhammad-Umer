"""Client IP resolution that can't be spoofed through X-Forwarded-For.

Behind Caddy, REMOTE_ADDR is always the proxy's address, so keying rate
limits and admin lockouts on it would put every visitor in one shared
bucket. Trusting X-Forwarded-For blindly is worse: any client can send its
own. The safe rule is to count from the right: each trusted proxy appends
exactly one address, so with N trusted proxies the real client is the N-th
entry from the end. Anything to the left of that was supplied by the client
and is ignored.

TRUSTED_PROXY_COUNT is 0 by default (no proxy, use REMOTE_ADDR) and must be
set to the real number of proxies in front of Django in production -- see
config/settings/prod.py and docker/Caddyfile.
"""

import ipaddress

from django.conf import settings
from django.http import HttpRequest


def _valid_ip(value: str) -> str | None:
    value = value.strip()
    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        return None


def client_ip(request: HttpRequest) -> str:
    remote_addr = request.META.get("REMOTE_ADDR", "") or "0.0.0.0"  # noqa: S104  # nosec B104
    proxy_count = getattr(settings, "TRUSTED_PROXY_COUNT", 0)
    if proxy_count <= 0:
        return remote_addr

    forwarded = [
        part for part in request.META.get("HTTP_X_FORWARDED_FOR", "").split(",") if part.strip()
    ]
    if len(forwarded) < proxy_count:
        # Fewer hops than configured proxies: the request didn't come through
        # the proxy chain (or it's misconfigured). Never trust the header then.
        return remote_addr
    return _valid_ip(forwarded[-proxy_count]) or remote_addr
