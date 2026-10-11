"""Base settings shared by every environment.

Nothing environment-specific (debug flags, hosts, secret values) lives here.
Each environment module (dev/prod/test) imports this and overrides only what
must differ. See docs/ARCHITECTURE.md for the full settings strategy.
"""

from pathlib import Path

import environ
from csp import constants as csp_constants

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(str(env_file))

SECRET_KEY = env.str("DJANGO_SECRET_KEY", default="insecure-dev-key-do-not-use-in-prod")

SITE_URL = env.str("SITE_URL", default="http://localhost:8000")
SITE_NAME = "Muhammad Umer"
CONTACT_EMAIL = env.str("CONTACT_EMAIL", default="")

ADMIN_URL = env.str("ADMIN_URL", default="admin/")
# ADMIN_URL is the secret path of the management dashboard (apps.dashboard),
# which replaces Django's built-in admin.
# Zero-trust admin: when non-empty, only these IPs/CIDRs even see the dashboard
# (everyone else gets a 404). Empty means "no network restriction" -- auth,
# lockout and (in prod) OTP still apply. See apps.core.middleware.
ADMIN_ALLOWED_IPS = env.list("ADMIN_ALLOWED_IPS", default=[])
# Dashboard login requires a TOTP code from an enrolled device. Off here so dev
# and tests aren't forced through enrollment; on by default in prod.py.
# Enroll with: python manage.py enroll_admin_otp <username>
ADMIN_REQUIRE_OTP = env.bool("ADMIN_REQUIRE_OTP", default=False)

# Number of reverse proxies in front of Django that each append one
# X-Forwarded-For entry. 0 = Django is hit directly. See apps/core/net.py.
TRUSTED_PROXY_COUNT = env.int("TRUSTED_PROXY_COUNT", default=0)

GOOGLE_SITE_VERIFICATION = env.str("GOOGLE_SITE_VERIFICATION", default="")
BING_SITE_VERIFICATION = env.str("BING_SITE_VERIFICATION", default="")

# AI_PROVIDER "fake" needs no key and costs nothing; a real provider is
# undecided as of 2026-09-30 (see docs/TODO_OWNER.md). 0 means no budget cap
# enforced (fine for "fake", required before any real provider goes live).
AI_PROVIDER = env.str("AI_PROVIDER", default="fake")
AI_DAILY_BUDGET_USD = env.float("AI_DAILY_BUDGET_USD", default=0.0)
# Rebuild the RAG index automatically (via Celery) whenever published
# content changes in the admin. See apps/ai/signals.py.
AI_AUTO_REINDEX = env.bool("AI_AUTO_REINDEX", default=True)

DJANGO_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django.contrib.humanize",
]

THIRD_PARTY_APPS: list[str] = [
    "django_htmx",
    "rest_framework",
    "drf_spectacular",
    "csp",
    "axes",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "django_otp.plugins.otp_static",
]

LOCAL_APPS = [
    "apps.core",
    "apps.portfolio",
    "apps.contact",
    "apps.seo",
    "apps.ai",
    "apps.api",
    "apps.dashboard",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "apps.core.middleware.AdminAccessMiddleware",
    "csp.middleware.CSPMiddleware",
    "apps.core.middleware.PermissionsPolicyMiddleware",
    "apps.core.middleware.IsolationHeadersMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.http.ConditionalGetMiddleware",
    "apps.core.middleware.CanonicalHostMiddleware",
    "apps.core.middleware.NoindexAdminAndApiMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "axes.middleware.AxesMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.site_meta",
                "apps.portfolio.context_processors.profile_context",
                "apps.portfolio.context_processors.navigation",
                "apps.seo.context_processors.canonical_url",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = False
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
# Files that must never be publicly addressable (resumes). Not under
# MEDIA_ROOT, not served by Caddy; Django streams them only after the
# email gate (apps/portfolio/resume_views.py).
PRIVATE_MEDIA_ROOT = env.path("PRIVATE_MEDIA_ROOT", default=BASE_DIR / "private_media")

# Uploads: keep big files on disk (not in memory), never world-writable.
FILE_UPLOAD_MAX_MEMORY_SIZE = 2_621_440  # 2.5 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 2_621_440
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000
FILE_UPLOAD_PERMISSIONS = 0o640
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o750

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Security defaults (tightened further in prod.py) ---
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = True  # no JS on this site reads the CSRF cookie
# The only sessions on this site are admin logins: keep them short-lived and
# gone when the browser closes, so a forgotten/stolen session expires fast.
SESSION_COOKIE_AGE = 60 * 60 * 2
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# --- Structured logging ---
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {"handlers": ["console"], "level": env.str("DJANGO_LOG_LEVEL", default="INFO")},
}

# --- Celery (wired up when apps.contact / apps.ai tasks exist; safe no-op until then) ---
CELERY_BROKER_URL = env.str("REDIS_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=True)

# --- Read-only public API ---
REST_FRAMEWORK = {
    # Zero trust: the public API is anonymous and read-only, so it accepts no
    # credentials at all -- an admin's session cookie can never elevate an
    # API request, and there's no CSRF surface to defend.
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["apps.api.permissions.ReadOnly"],
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.AnonRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {"anon": "60/min"},
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Muhammad Umer -- Portfolio API",
    "DESCRIPTION": "Read-only public API for portfolio entries, tags and profile.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# --- Content Security Policy ---
# script-src has NO 'unsafe-inline': 'self' covers our own external JS files
# (htmx.min.js, main.js, stage.js, etc. -- there are zero inline <script>
# blocks anywhere in templates/, verified by tests/unit/test_csp.py), with a
# per-request nonce as the sanctioned escape hatch for a future inline
# script. That's the security-critical directive and it stays strict.
#
# style-src DOES allow 'unsafe-inline', which needs explaining since the
# brief's default is "no unsafe-inline" anywhere: three.js's vendored,
# self-hosted WebGLRenderer creates a throwaway canvas internally to probe
# WebGL support and sets its `.style.display` directly (see the minified
# `oi()` helper in static/js/vendor/three.module.min.js) -- CSP treats any
# JS `.style` mutation the same as a static style="" attribute, and there is
# no nonce mechanism for a third-party library's internal DOM manipulation.
# Our own code (apps/core/middleware.py's PermissionsPolicyMiddleware
# neighbor, static/js/tilt.js) deliberately avoids inline style mutation
# entirely (tilt.js uses a nonce'd <style> + CSSOM rule mutation instead,
# specifically so it doesn't need this). CSS injection alone can't execute
# JavaScript, so this is a materially smaller relaxation than 'unsafe-inline'
# on script-src would be. Revisit if a future three.js release fixes this
# internally, or if the canvas capability probe can be avoided some other
# way -- tracked in docs/TODO_OWNER.md.
CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": [csp_constants.SELF],
        "script-src": [csp_constants.SELF, csp_constants.NONCE],
        "style-src": [csp_constants.SELF, csp_constants.UNSAFE_INLINE],
        "img-src": [csp_constants.SELF, "data:"],
        "font-src": [csp_constants.SELF],
        "connect-src": [csp_constants.SELF],
        "object-src": [csp_constants.NONE],
        "base-uri": [csp_constants.SELF],
        "frame-ancestors": [csp_constants.NONE],
        "form-action": [csp_constants.SELF],
        "frame-src": [csp_constants.NONE],
        "worker-src": [csp_constants.SELF],
        "manifest-src": [csp_constants.SELF],
    },
}

# --- Permissions-Policy: disable unused browser features ---
PERMISSIONS_POLICY = (
    "accelerometer=(), autoplay=(), camera=(), display-capture=(), "
    "encrypted-media=(), fullscreen=(self), geolocation=(), gyroscope=(), "
    "hid=(), magnetometer=(), microphone=(), midi=(), "
    "payment=(), publickey-credentials-get=(), serial=(), usb=(), "
    "xr-spatial-tracking=()"
)

# --- django-axes: lock out the admin after repeated failed logins ---
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1  # hours
AXES_LOCKOUT_PARAMETERS = ["ip_address", "username"]
AXES_RESET_ON_SUCCESS = True
AXES_CLIENT_IP_CALLABLE = "apps.core.net.client_ip"

# --- django-ratelimit: same proxy-aware client IP as axes ---
RATELIMIT_IP_META_KEY = "apps.core.net.client_ip"
