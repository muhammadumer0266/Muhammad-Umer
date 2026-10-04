from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("entries", views.EntryViewSet, basename="entry")
router.register("tags", views.TagViewSet, basename="tag")

app_name = "api"

urlpatterns = [
    path("v1/profile/", views.ProfileView.as_view(), name="profile"),
    path("v1/", include(router.urls)),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="api:schema"), name="docs"),
]
