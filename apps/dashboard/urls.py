from django.urls import path

from . import auth, views

app_name = "dashboard"

urlpatterns = [
    path("", views.overview, name="overview"),
    path("login/", auth.login_view, name="login"),
    path("logout/", auth.logout_view, name="logout"),
    path("profile/", views.profile_edit, name="profile"),
    path("ask-policy/", views.policy_edit, name="policy"),
    path("ask-policy/reindex/", views.reindex_now, name="reindex"),
    path("messages/<int:pk>/", views.message_detail, name="message_detail"),
    path("resumes/<int:pk>/file/", views.resume_file, name="resume_file"),
    path("resume-requests/export.csv", views.resume_requests_csv, name="resume_requests_csv"),
    path("<slug:section>/", views.section_list, name="list"),
    path("<slug:section>/new/", views.section_create, name="create"),
    path("<slug:section>/<int:pk>/", views.section_edit, name="edit"),
    path("<slug:section>/<int:pk>/delete/", views.section_delete, name="delete"),
]
