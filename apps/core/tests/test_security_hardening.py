import pytest
from django.core.checks import run_checks
from django.core.management import CommandError, call_command
from django.test import RequestFactory, override_settings
from django.urls import reverse

from apps.core.net import client_ip

rf = RequestFactory()


# --- client IP resolution ---------------------------------------------------


@override_settings(TRUSTED_PROXY_COUNT=0)
def test_client_ip_ignores_forwarded_header_without_trusted_proxy():
    request = rf.get("/", REMOTE_ADDR="10.0.0.5", HTTP_X_FORWARDED_FOR="1.2.3.4")

    assert client_ip(request) == "10.0.0.5"


@override_settings(TRUSTED_PROXY_COUNT=1)
def test_client_ip_uses_entry_appended_by_trusted_proxy():
    request = rf.get("/", REMOTE_ADDR="172.18.0.3", HTTP_X_FORWARDED_FOR="203.0.113.7")

    assert client_ip(request) == "203.0.113.7"


@override_settings(TRUSTED_PROXY_COUNT=1)
def test_client_ip_cannot_be_spoofed_by_prepending_entries():
    # Attacker sends "X-Forwarded-For: 1.1.1.1"; the proxy appends the real IP.
    request = rf.get("/", REMOTE_ADDR="172.18.0.3", HTTP_X_FORWARDED_FOR="1.1.1.1, 198.51.100.9")

    assert client_ip(request) == "198.51.100.9"


@override_settings(TRUSTED_PROXY_COUNT=1)
def test_client_ip_falls_back_on_garbage_header():
    request = rf.get("/", REMOTE_ADDR="172.18.0.3", HTTP_X_FORWARDED_FOR="not-an-ip")

    assert client_ip(request) == "172.18.0.3"


# --- admin zero-trust gate --------------------------------------------------


@pytest.mark.django_db
@override_settings(ADMIN_ALLOWED_IPS=["192.0.2.0/24"])
def test_admin_is_hidden_from_non_allowlisted_ips(client):
    response = client.get(reverse("admin:login"), REMOTE_ADDR="198.51.100.1")

    assert response.status_code == 404


@pytest.mark.django_db
@override_settings(ADMIN_ALLOWED_IPS=["192.0.2.0/24"])
def test_admin_is_reachable_from_allowlisted_ip_and_never_cached(client):
    response = client.get(reverse("admin:login"), REMOTE_ADDR="192.0.2.10")

    assert response.status_code == 200
    assert response["Cache-Control"] == "no-store, private"


@pytest.mark.django_db
@override_settings(ADMIN_ALLOWED_IPS=["192.0.2.0/24"], TRUSTED_PROXY_COUNT=1)
def test_admin_allowlist_cannot_be_bypassed_with_forged_forwarded_for(client):
    response = client.get(
        reverse("admin:login"),
        REMOTE_ADDR="172.18.0.3",
        HTTP_X_FORWARDED_FOR="192.0.2.10, 198.51.100.1",
    )

    assert response.status_code == 404


# --- headers ----------------------------------------------------------------


@pytest.mark.django_db
def test_isolation_headers_present(client):
    response = client.get(reverse("portfolio:home"))

    assert response["Cross-Origin-Opener-Policy"] == "same-origin"
    assert response["Cross-Origin-Resource-Policy"] == "same-origin"
    assert response["X-Content-Type-Options"] == "nosniff"


@pytest.mark.django_db
def test_csp_restricts_form_targets_and_frames(client):
    csp = client.get(reverse("portfolio:home"))["Content-Security-Policy"]

    assert "form-action 'self'" in csp
    assert "frame-src 'none'" in csp
    assert "object-src 'none'" in csp


# --- public API: anonymous and read-only ------------------------------------


@pytest.mark.django_db
def test_api_rejects_writes(client):
    response = client.post("/api/v1/entries/", {"title": "x"})

    assert response.status_code in (403, 405)


@pytest.mark.django_db
def test_api_ignores_admin_session(client, django_user_model):
    """An admin's session cookie must not grant the API any extra power."""
    admin = django_user_model.objects.create_superuser("root", "r@example.com", "x")
    client.force_login(admin)

    response = client.delete("/api/v1/tags/anything/")

    assert response.status_code in (403, 405)


# --- deploy checks ----------------------------------------------------------


@override_settings(ADMIN_URL="admin/", ADMIN_REQUIRE_OTP=False, TRUSTED_PROXY_COUNT=0)
def test_deploy_checks_flag_insecure_settings():
    ids = {issue.id for issue in run_checks(include_deployment_checks=True)}

    assert {"core.W001", "core.W002", "core.W003"} <= ids


@override_settings(AI_PROVIDER="paid", AI_DAILY_BUDGET_USD=0)
def test_deploy_checks_error_on_uncapped_paid_ai_provider():
    ids = {issue.id for issue in run_checks(include_deployment_checks=True)}

    assert "core.E001" in ids


# --- OTP enrollment ---------------------------------------------------------


@pytest.mark.django_db
def test_enroll_admin_otp_saves_nothing_on_wrong_code(django_user_model, monkeypatch):
    from django_otp.plugins.otp_totp.models import TOTPDevice

    user = django_user_model.objects.create_user("owner", password="x", is_staff=True)
    monkeypatch.setattr("builtins.input", lambda _prompt: "000000")
    monkeypatch.setattr(TOTPDevice, "verify_token", lambda self, token: False)

    with pytest.raises(CommandError):
        call_command("enroll_admin_otp", "owner")

    assert not TOTPDevice.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_enroll_admin_otp_confirms_device_and_issues_backup_codes(django_user_model, monkeypatch):
    from django_otp.plugins.otp_static.models import StaticToken
    from django_otp.plugins.otp_totp.models import TOTPDevice

    user = django_user_model.objects.create_user("owner", password="x", is_staff=True)
    monkeypatch.setattr("builtins.input", lambda _prompt: "123456")
    monkeypatch.setattr(TOTPDevice, "verify_token", lambda self, code: code == "123456")

    call_command("enroll_admin_otp", "owner")

    assert TOTPDevice.objects.get(user=user).confirmed is True
    assert StaticToken.objects.filter(device__user=user).count() == 10


@pytest.mark.django_db
def test_enroll_admin_otp_refuses_non_staff(django_user_model):
    django_user_model.objects.create_user("visitor", password="x")

    with pytest.raises(CommandError, match="staff"):
        call_command("enroll_admin_otp", "visitor")


@pytest.mark.django_db
def test_otp_admin_site_requires_token_field_and_verified_user(client, django_user_model):
    """What ADMIN_REQUIRE_OTP does in config/urls.py, exercised directly."""
    from django.contrib import admin
    from django_otp.admin import OTPAdminSite

    original = admin.site.__class__
    admin.site.__class__ = OTPAdminSite
    try:
        login_page = client.get(reverse("admin:login"))
        staff = django_user_model.objects.create_superuser("boss", "b@example.com", "x")
        client.force_login(staff)  # password only, no OTP device verified
        index = client.get(reverse("admin:index"))
    finally:
        admin.site.__class__ = original

    assert b'name="otp_token"' in login_page.content
    assert index.status_code == 302  # bounced back to login
