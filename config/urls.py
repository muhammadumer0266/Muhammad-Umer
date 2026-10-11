from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django_otp.admin import OTPAdminSite

if settings.ADMIN_REQUIRE_OTP:
    # Every admin login then needs username + password + a TOTP (or backup)
    # code from a device enrolled via `manage.py enroll_admin_otp`. Swapping
    # the default site's class keeps every existing @admin.register intact.
    admin.site.__class__ = OTPAdminSite

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("", include("apps.core.urls")),
    path("", include("apps.seo.urls")),
    path("contact/", include("apps.contact.urls")),
    path("ask/", include("apps.ai.urls")),
    path("api/", include("apps.api.urls")),
    path("", include("apps.portfolio.urls")),
]

if settings.DEBUG:
    # Production serves /media/ from Caddy (see docker/Caddyfile), never Django.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "apps.core.views.handler404"
handler500 = "apps.core.views.handler500"
