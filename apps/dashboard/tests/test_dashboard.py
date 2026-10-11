import io
from datetime import date

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from apps.ai.models import GuardrailPolicy, GuardrailRule
from apps.contact.models import ContactMessage
from apps.dashboard.sections import SECTIONS
from apps.portfolio.models import Certification, Entry, Photo, Profile, Resume, ResumeRequest

PDF = b"%PDF-1.7\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"


def _png() -> SimpleUploadedFile:
    buffer = io.BytesIO()
    Image.new("RGB", (40, 40), "white").save(buffer, format="PNG")
    return SimpleUploadedFile("badge.png", buffer.getvalue(), content_type="image/png")


@pytest.fixture
def storage(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.PRIVATE_MEDIA_ROOT = tmp_path / "private"
    return tmp_path


@pytest.fixture
def staff_client(client, django_user_model):
    user = django_user_model.objects.create_user("owner", password="pw", is_staff=True)
    client.force_login(user)
    return client


# --- access control --------------------------------------------------------


@pytest.mark.django_db
def test_django_admin_is_gone(client):
    from django.conf import settings

    assert "django.contrib.admin" not in settings.INSTALLED_APPS
    # The secret ADMIN_URL path now serves the dashboard (here: its login).
    response = client.get(f"/{settings.ADMIN_URL}")
    assert response["Location"].startswith(reverse("dashboard:login"))


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url_name", ["dashboard:overview", "dashboard:profile", "dashboard:policy"]
)
def test_anonymous_users_are_sent_to_login(client, url_name):
    response = client.get(reverse(url_name))

    assert response.status_code == 302
    assert response["Location"].startswith(reverse("dashboard:login"))


@pytest.mark.django_db
def test_non_staff_users_are_refused(client, django_user_model):
    user = django_user_model.objects.create_user("visitor", password="pw")
    client.force_login(user)

    response = client.get(reverse("dashboard:list", args=["work"]))

    assert response.status_code == 302
    assert "_auth_user_id" not in client.session  # logged out, not just bounced


@pytest.mark.django_db
def test_non_staff_password_login_is_rejected(client, django_user_model):
    django_user_model.objects.create_user("visitor", password="pw")

    response = client.post(reverse("dashboard:login"), {"username": "visitor", "password": "pw"})

    assert response.status_code == 400


@pytest.mark.django_db
def test_login_next_cannot_redirect_off_site(client, django_user_model):
    django_user_model.objects.create_user("owner", password="pw", is_staff=True)

    response = client.post(
        reverse("dashboard:login") + "?next=https://evil.example/",
        {"username": "owner", "password": "pw"},
    )

    assert response["Location"] == reverse("dashboard:overview")


@pytest.mark.django_db
def test_logout_requires_post(staff_client):
    assert staff_client.get(reverse("dashboard:logout")).status_code == 405
    assert staff_client.post(reverse("dashboard:logout")).status_code == 302


@pytest.mark.django_db
def test_dashboard_pages_are_never_cached_or_indexed(staff_client):
    response = staff_client.get(reverse("dashboard:overview"))

    assert "no-store" in response["Cache-Control"]
    assert response["X-Robots-Tag"] == "noindex"


# --- every section renders -------------------------------------------------------


@pytest.mark.django_db
def test_overview_renders(staff_client):
    assert staff_client.get(reverse("dashboard:overview")).status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize("section", [s.slug for s in SECTIONS])
def test_every_section_list_renders(staff_client, section):
    assert staff_client.get(reverse("dashboard:list", args=[section])).status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize("section", [s.slug for s in SECTIONS if s.can_add])
def test_every_create_form_renders(staff_client, section):
    assert staff_client.get(reverse("dashboard:create", args=[section])).status_code == 200


@pytest.mark.django_db
def test_read_only_sections_cannot_be_created(staff_client):
    assert staff_client.get(reverse("dashboard:create", args=["messages"])).status_code == 404
    assert staff_client.get(reverse("dashboard:create", args=["ask-logs"])).status_code == 404


@pytest.mark.django_db
def test_unknown_section_404s(staff_client):
    assert staff_client.get(reverse("dashboard:list", args=["users"])).status_code == 404


# --- content management (CMS) ---------------------------------------------------


@pytest.mark.django_db
def test_edit_profile_title_and_summary_goes_live(staff_client, client):
    response = staff_client.post(
        reverse("dashboard:profile"),
        {
            "full_name": "Muhammad Umer",
            "alternate_names": "Umer, M. Umer",
            "headline": "Backend & AI Engineer",
            "bio_short": "I build Django backends and retrieval-augmented AI tools.",
            "bio_md": "",
            "location_display": "Lahore, Pakistan",
        },
    )

    assert response.status_code == 302
    profile = Profile.get_solo()
    assert profile.headline == "Backend & AI Engineer"
    assert profile.alternate_names == ["Umer", "M. Umer"]
    home = client.get(reverse("portfolio:home")).content.decode()
    assert "Backend &amp; AI Engineer" in home
    assert "I build Django backends" in home


@pytest.mark.django_db
def test_create_project_with_metrics_lines(staff_client):
    response = staff_client.post(
        reverse("dashboard:create", args=["work"]),
        {
            "title": "xl-diff",
            "slug": "xl-diff",
            "kind": "project",
            "status": "shipped",
            "date": "2026-03-15",
            "summary": "A Rust-backed Excel diff engine.",
            "body_md": "# Why\nBecause.",
            "metrics": "10x faster\n\n0 dependencies",
            "is_published": "on",
        },
    )

    assert response.status_code == 302
    entry = Entry.objects.get(slug="xl-diff")
    assert entry.metrics == ["10x faster", "0 dependencies"]
    assert entry.date == date(2026, 3, 1)  # month precision, via Entry.clean


@pytest.mark.django_db
def test_upload_certification_with_badge(staff_client, storage):
    response = staff_client.post(
        reverse("dashboard:create", args=["certifications"]),
        {
            "title": "AWS Developer",
            "issuer": "Amazon",
            "issue_date": "2025-06-01",
            "is_published": "on",
            "order": "0",
            "badge_image": _png(),
        },
    )

    assert response.status_code == 302
    cert = Certification.objects.get()
    assert cert.badge_image.name.startswith("certifications/badges/")


@pytest.mark.django_db
def test_invalid_upload_is_rejected_with_message(staff_client, storage):
    fake = SimpleUploadedFile("evil.png", b"<svg onload=alert(1)>", content_type="image/png")

    response = staff_client.post(
        reverse("dashboard:create", args=["photos"]),
        {"title": "x", "alt_text": "x", "is_published": "on", "order": "0", "image": fake},
    )

    assert response.status_code == 400
    assert not Photo.objects.exists()
    assert b"field__error" in response.content


@pytest.mark.django_db
def test_delete_requires_confirmation_post(staff_client):
    cert = Certification.objects.create(title="T", issuer="I", issue_date=date(2025, 1, 1))
    url = reverse("dashboard:delete", args=["certifications", cert.pk])

    assert staff_client.get(url).status_code == 200
    assert Certification.objects.exists()
    staff_client.post(url)
    assert not Certification.objects.exists()


@pytest.mark.django_db
def test_list_search(staff_client):
    Certification.objects.create(title="Kubernetes", issuer="CNCF", issue_date=date(2025, 1, 1))
    Certification.objects.create(title="Azure", issuer="Microsoft", issue_date=date(2025, 1, 1))

    html = staff_client.get(reverse("dashboard:list", args=["certifications"]), {"q": "cncf"})

    assert b"Kubernetes" in html.content
    assert b"Azure" not in html.content


# --- résumés ---------------------------------------------------------------


@pytest.mark.django_db
def test_upload_resume_is_private_and_becomes_active(staff_client, storage):
    old = Resume.objects.create(
        label="Old", file=SimpleUploadedFile("a.pdf", PDF, content_type="application/pdf")
    )

    response = staff_client.post(
        reverse("dashboard:create", args=["resumes"]),
        {
            "label": "October",
            "is_active": "on",
            "file": SimpleUploadedFile("cv.pdf", PDF, content_type="application/pdf"),
        },
    )

    assert response.status_code == 302
    new = Resume.objects.get(label="October")
    old.refresh_from_db()
    assert new.is_active
    assert not old.is_active
    assert (storage / "private" / new.file.name).exists()
    assert not (storage / "media" / new.file.name).exists()
    # Owner-only preview works; the edit form renders without a public URL.
    assert staff_client.get(reverse("dashboard:resume_file", args=[new.pk])).status_code == 200
    assert staff_client.get(reverse("dashboard:edit", args=["resumes", new.pk])).status_code == 200


@pytest.mark.django_db
def test_resume_must_be_a_real_pdf(staff_client, storage):
    response = staff_client.post(
        reverse("dashboard:create", args=["resumes"]),
        {
            "label": "x",
            "is_active": "on",
            "file": SimpleUploadedFile("cv.pdf", b"<html>", content_type="application/pdf"),
        },
    )

    assert response.status_code == 400
    assert not Resume.objects.exists()


@pytest.mark.django_db
def test_resume_requests_csv_neutralises_formulas(staff_client):
    ResumeRequest.objects.create(email="=cmd@example.com")
    ResumeRequest.objects.create(email="hr@example.com")

    body = staff_client.get(reverse("dashboard:resume_requests_csv")).content.decode()

    assert "'=cmd@example.com" in body
    assert "hr@example.com" in body


# --- inbox & AI ----------------------------------------------------------------


@pytest.mark.django_db
def test_opening_a_message_marks_it_read_and_status_can_change(staff_client):
    message = ContactMessage.objects.create(name="Ali", email="ali@example.com", message="Hi")
    url = reverse("dashboard:message_detail", args=[message.pk])

    assert b"Hi" in staff_client.get(url).content
    message.refresh_from_db()
    assert message.status == "read"

    staff_client.post(url, {"status": "spam"})
    message.refresh_from_db()
    assert message.status == "spam"


@pytest.mark.django_db
def test_guardrail_policy_and_rules_editable(staff_client):
    staff_client.post(
        reverse("dashboard:policy"),
        {
            "enabled": "",
            "disabled_message": "Back soon.",
            "rate_limit_per_hour": "10",
            "min_question_length": "3",
            "max_question_length": "200",
            "similarity_threshold": "0.2",
            "top_k": "4",
            "require_citations": "on",
            "redact_pii": "on",
            "max_answer_chars": "1500",
            "refusal_message": "No.",
            "no_answer_message": "Don't know.",
        },
    )
    staff_client.post(
        reverse("dashboard:create", args=["guardrail-rules"]),
        {
            "name": "no salary",
            "stage": "input",
            "match_type": "keyword",
            "pattern": "salary",
            "action": "block",
            "priority": "100",
            "is_active": "on",
        },
    )

    policy = GuardrailPolicy.get_solo()
    assert policy.enabled is False
    assert policy.max_question_length == 200
    assert GuardrailRule.objects.filter(name="no salary").exists()


@pytest.mark.django_db
def test_reindex_button_requires_post(staff_client):
    url = reverse("dashboard:reindex")

    assert staff_client.get(url).status_code == 405
    assert staff_client.post(url).status_code == 302
