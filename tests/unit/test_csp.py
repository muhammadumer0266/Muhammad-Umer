"""CSP and header hardening tests.

Includes the explicit gate the brief calls for: fail if any inline <script>
appears without a nonce. We currently have zero inline scripts (everything
is an external self-hosted file), so this also guards against a future
regression, not just documents the current state.
"""

import re

import pytest
from django.urls import reverse

PUBLIC_PAGES = [
    "portfolio:home",
    "portfolio:work_list",
    "portfolio:about",
    "contact:contact",
    "ai:ask",
    "core:privacy",
]

_SCRIPT_TAG = re.compile(r"<script\b([^>]*)>", re.IGNORECASE)


@pytest.mark.django_db
def test_no_inline_script_without_a_nonce(client):
    """CSP's script-src only governs executable-JS script elements: a
    <script type="application/ld+json"> block (our JSON-LD) is not JS and
    browsers never run it, so CSP doesn't gate it and it needs no nonce."""
    non_js_types = ("application/ld+json",)

    for name in PUBLIC_PAGES:
        response = client.get(reverse(name))
        html = response.content.decode()
        for attrs in _SCRIPT_TAG.findall(html):
            if any(f'type="{t}"' in attrs for t in non_js_types):
                continue
            has_src = "src=" in attrs
            has_nonce = "nonce=" in attrs
            assert has_src or has_nonce, f"{name} has an inline <script> without a nonce: {attrs!r}"


@pytest.mark.django_db
def test_content_security_policy_header_present(client):
    response = client.get(reverse("portfolio:home"))

    csp = response.get("Content-Security-Policy", "")
    assert csp, "no Content-Security-Policy header"
    assert "'self'" in csp


@pytest.mark.django_db
def test_script_src_never_allows_unsafe_inline(client):
    """The security-critical directive: script-src must stay nonce-only.

    style-src legitimately carries 'unsafe-inline' (see the comment on
    CONTENT_SECURITY_POLICY in config/settings/base.py -- it's caused by
    three.js's own internal WebGL-capability-probe canvas, not our code),
    but that must never spread to script-src.
    """
    response = client.get(reverse("portfolio:home"))

    csp = response.get("Content-Security-Policy", "")
    script_src = next(part for part in csp.split(";") if part.strip().startswith("script-src"))
    assert "'unsafe-inline'" not in script_src


@pytest.mark.django_db
def test_permissions_policy_header_present(client):
    response = client.get(reverse("portfolio:home"))

    assert "geolocation=()" in response.get("Permissions-Policy", "")


@pytest.mark.django_db
def test_x_frame_options_denies_framing(client):
    response = client.get(reverse("portfolio:home"))

    assert response.get("X-Frame-Options") == "DENY"
