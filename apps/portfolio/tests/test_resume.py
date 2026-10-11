import time

import pytest
from django.core import signing
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from apps.contact.forms import _SIGNING_SALT as RENDER_SALT
from apps.portfolio.models import Resume, ResumeRequest

PDF = b"%PDF-1.7\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"


@pytest.fixture
def resume(settings, tmp_path):
    settings.PRIVATE_MEDIA_ROOT = tmp_path / "private"
    return Resume.objects.create(
        label="Current", file=SimpleUploadedFile("cv.pdf", PDF, content_type="application/pdf")
    )


def _form(email: str, **extra) -> dict:
    # A render timestamp from 10s ago passes the time-trap.
    data = {
        "email": email,
        "website": "",
        "rendered_at": signing.dumps(time.time() - 10, salt=RENDER_SALT),
    }
    data.update(extra)
    return data


def _download_url(response) -> str:
    return response.context["download_url"]


@pytest.mark.django_db
def test_resume_page_asks_for_email(client, resume):
    response = client.get(reverse("portfolio:resume"))

    assert response.status_code == 200
    assert b'type="email"' in response.content
    assert b'name="robots" content="noindex"' in response.content


@pytest.mark.django_db
def test_email_unlocks_download_and_records_lead(client, resume):
    response = client.post(reverse("portfolio:resume"), _form("hr@example.com"))

    assert response.status_code == 200
    lead = ResumeRequest.objects.get()
    assert lead.email == "hr@example.com"
    assert lead.resume == resume
    assert lead.ip_hash
    assert "127.0.0.1" not in lead.ip_hash

    download = client.get(_download_url(response))
    assert download.status_code == 200
    assert download["Content-Type"] == "application/pdf"
    assert "attachment" in download["Content-Disposition"]
    assert "muhammad-umer-resume.pdf" in download["Content-Disposition"]
    assert b"".join(download.streaming_content) == PDF
    assert "no-store" in download["Cache-Control"]
    lead.refresh_from_db()
    resume.refresh_from_db()
    assert lead.downloaded is True
    assert resume.download_count == 1


@pytest.mark.django_db
def test_invalid_email_does_not_unlock(client, resume):
    response = client.post(reverse("portfolio:resume"), _form("not-an-email"))

    assert b"field-error" in response.content
    assert not ResumeRequest.objects.exists()


@pytest.mark.django_db
def test_honeypot_blocks_bots(client, resume):
    client.post(reverse("portfolio:resume"), _form("bot@example.com", website="spam"))

    assert not ResumeRequest.objects.exists()


@pytest.mark.django_db
def test_forged_or_expired_token_404s(client, resume):
    assert client.get(reverse("portfolio:resume_download", args=["forged"])).status_code == 404

    response = client.post(reverse("portfolio:resume"), _form("hr@example.com"))
    url = _download_url(response)
    with override_settings():
        import apps.portfolio.resume as resume_module

        original = resume_module.DOWNLOAD_TOKEN_MAX_AGE
        resume_module.DOWNLOAD_TOKEN_MAX_AGE = -1
        try:
            assert client.get(url).status_code == 404
        finally:
            resume_module.DOWNLOAD_TOKEN_MAX_AGE = original


@pytest.mark.django_db
def test_resume_file_has_no_public_url(resume):
    with pytest.raises(ValueError, match="not accessible via a URL"):
        _ = resume.file.url


@pytest.mark.django_db
def test_no_active_resume_shows_message_and_hides_links(client):
    page = client.get(reverse("portfolio:resume")).content.decode()
    about = client.get(reverse("portfolio:about")).content.decode()

    assert "available for download right now" in page
    assert reverse("portfolio:resume") not in about


@pytest.mark.django_db
def test_resume_links_appear_once_uploaded(client, resume):
    assert reverse("portfolio:resume").encode() in client.get(reverse("portfolio:about")).content
    assert reverse("portfolio:resume").encode() in client.get(reverse("portfolio:home")).content


@pytest.mark.django_db
@override_settings(RATELIMIT_ENABLE=True)
def test_resume_requests_are_rate_limited(client, resume):
    from django.core.cache import cache

    cache.clear()
    for i in range(5):
        client.post(reverse("portfolio:resume"), _form(f"a{i}@example.com"))

    limited = client.post(reverse("portfolio:resume"), _form("six@example.com"))

    assert limited.status_code == 429
    assert ResumeRequest.objects.count() == 5
