from .base import *  # noqa: F403
from .base import BASE_DIR, env

DEBUG = False
SECRET_KEY = "test-secret-key-not-for-production"  # noqa: S105 -- not a real secret  # nosec B105
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
SITE_URL = "http://testserver"

DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'test_db.sqlite3'}",
    )
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

CELERY_TASK_ALWAYS_EAGER = True

# Rate limiting is exercised in its own isolated test (with the cache
# cleared and this flag overridden True); left off by default here so
# ordinary view tests don't trip a shared-cache rate limit across the run.
RATELIMIT_ENABLE = False
