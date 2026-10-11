from .base import *  # noqa: F403
from .base import env

DEBUG = False

SECRET_KEY = env.str("DJANGO_SECRET_KEY")  # fails fast if missing
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")  # fails fast if missing
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS")  # fails fast if missing

SECURE_SSL_REDIRECT = True
# Caddy terminates TLS and always overwrites X-Forwarded-Proto, so it's safe
# to trust -- *only* because the web container is not reachable except
# through Caddy (see docker-compose.yml: no public port on `web`). Without
# this, every request looks like plain HTTP and SECURE_SSL_REDIRECT loops.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_REDIRECT_EXEMPT = [r"^healthz/$"]
# Caddy is the one proxy in front of Django (see apps/core/net.py).
TRUSTED_PROXY_COUNT = env.int("TRUSTED_PROXY_COUNT", default=1)

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# __Host- prefix: browser enforces Secure, Path=/ and no Domain, so a
# compromised subdomain can't plant or read these cookies.
SESSION_COOKIE_NAME = "__Host-sessionid"
CSRF_COOKIE_NAME = "__Host-csrftoken"

ADMIN_REQUIRE_OTP = env.bool("ADMIN_REQUIRE_OTP", default=True)

# No browsable HTML API in production: JSON only, smaller attack surface.
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}

CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        **CONTENT_SECURITY_POLICY["DIRECTIVES"],  # noqa: F405
        "upgrade-insecure-requests": True,
    },
}
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=3600)  # raise once confirmed stable
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = False  # TODO(owner): opt in explicitly once ready, this is hard to reverse

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env.str("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env.str("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = True

SENTRY_DSN = env.str("SENTRY_DSN", default="")
if SENTRY_DSN:
    import sentry_sdk

    sentry_sdk.init(dsn=SENTRY_DSN, traces_sample_rate=0.05, profiles_sample_rate=0.0)
