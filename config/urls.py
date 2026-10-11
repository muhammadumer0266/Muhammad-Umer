from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    # The private management dashboard (replaces Django's admin) lives at a
    # secret path; see apps/dashboard and docs/SECURITY.md.
    path(settings.ADMIN_URL, include("apps.dashboard.urls")),
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
