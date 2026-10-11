"""Deploy checks for this project's own security settings.

Run with `python manage.py check --deploy` (CI and before every release);
these complement Django's built-in security.W0xx checks.
"""

from django.conf import settings
from django.core.checks import Error, Tags, Warning, register


@register(Tags.security, deploy=True)
def project_security_checks(app_configs, **kwargs):
    issues = []
    if settings.ADMIN_URL.strip("/") == "admin":
        issues.append(
            Warning(
                "ADMIN_URL is the default 'admin/'.",
                hint="Set ADMIN_URL to a non-guessable path.",
                id="core.W001",
            )
        )
    if not settings.ADMIN_REQUIRE_OTP:
        issues.append(
            Warning(
                "Admin login does not require a one-time password.",
                hint="Set ADMIN_REQUIRE_OTP=True after running manage.py enroll_admin_otp.",
                id="core.W002",
            )
        )
    if getattr(settings, "TRUSTED_PROXY_COUNT", 0) <= 0:
        issues.append(
            Warning(
                "TRUSTED_PROXY_COUNT is 0: rate limits and lockouts key on REMOTE_ADDR.",
                hint="Behind Caddy this must be 1, or every visitor shares one rate-limit bucket.",
                id="core.W003",
            )
        )
    if settings.AI_PROVIDER != "fake" and settings.AI_DAILY_BUDGET_USD <= 0:
        issues.append(
            Error(
                "A paid AI provider is configured with no daily budget cap.",
                hint="Set AI_DAILY_BUDGET_USD to a positive value.",
                id="core.E001",
            )
        )
    return issues
