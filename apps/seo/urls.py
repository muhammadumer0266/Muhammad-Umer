from django.contrib.sitemaps.views import sitemap
from django.urls import path

from . import views
from .sitemaps import EntrySitemap, StaticViewSitemap, TagSitemap

sitemaps = {
    "static": StaticViewSitemap,
    "entries": EntrySitemap,
    "tags": TagSitemap,
}

urlpatterns = [
    path("robots.txt", views.robots_txt, name="robots_txt"),
    path("llms.txt", views.llms_txt, name="llms_txt"),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
]
