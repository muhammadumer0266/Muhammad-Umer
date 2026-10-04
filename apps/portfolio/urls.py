from django.urls import path

from . import views

app_name = "portfolio"

urlpatterns = [
    path("", views.home, name="home"),
    path("work/", views.work_list, name="work_list"),
    path("work/tag/<slug:slug>/", views.tag_detail, name="tag_detail"),
    path("work/<slug:slug>/", views.entry_detail, name="entry_detail"),
    path("about/", views.about, name="about"),
]
