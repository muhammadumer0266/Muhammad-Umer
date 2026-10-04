from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("", include("apps.core.urls")),
    path("", include("apps.seo.urls")),
    path("contact/", include("apps.contact.urls")),
    path("ask/", include("apps.ai.urls")),
    path("api/", include("apps.api.urls")),
    path("", include("apps.portfolio.urls")),
]

handler404 = "apps.core.views.handler404"
handler500 = "apps.core.views.handler500"
