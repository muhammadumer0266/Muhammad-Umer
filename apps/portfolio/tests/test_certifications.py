from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from apps.portfolio.models import Certification, Profile


def _cert(**kwargs) -> Certification:
    defaults = {
        "title": "AWS Certified Developer",
        "issuer": "Amazon Web Services",
        "issue_date": date(2025, 3, 1),
        "is_published": True,
    }
    defaults.update(kwargs)
    return Certification.objects.create(**defaults)


@pytest.mark.django_db
def test_certifications_page_lists_only_published(client):
    _cert(title="Visible Cert")
    _cert(title="Draft Cert", is_published=False)

    response = client.get(reverse("portfolio:certifications"))

    assert response.status_code == 200
    assert b"Visible Cert" in response.content
    assert b"Draft Cert" not in response.content
    assert response.content.count(b"<h1") == 1


@pytest.mark.django_db
def test_empty_certifications_page_is_noindex(client):
    response = client.get(reverse("portfolio:certifications"))

    assert b'name="robots" content="noindex"' in response.content


@pytest.mark.django_db
def test_nav_shows_certifications_only_once_one_is_published(client):
    url = reverse("portfolio:certifications").encode()

    assert url not in client.get(reverse("portfolio:home")).content

    _cert()

    assert url in client.get(reverse("portfolio:home")).content


@pytest.mark.django_db
def test_certifications_appear_on_about_and_home(client):
    _cert(title="Kubernetes Admin", credential_url="https://verify.example.com/abc")

    about = client.get(reverse("portfolio:about")).content
    home = client.get(reverse("portfolio:home")).content

    assert b"Kubernetes Admin" in about
    assert b"Verify with issuer" in about
    assert b"Kubernetes Admin" in home


@pytest.mark.django_db
def test_expired_certification_is_labelled():
    cert = _cert(expiry_date=date(2020, 1, 1), issue_date=date(2019, 1, 1))

    assert cert.is_expired is True


@pytest.mark.django_db
def test_expiry_before_issue_is_invalid():
    cert = Certification(
        title="X", issuer="Y", issue_date=date(2025, 5, 1), expiry_date=date(2024, 1, 1)
    )

    with pytest.raises(ValidationError):
        cert.full_clean()


@pytest.mark.django_db
def test_certifications_api_lists_published_only(client):
    _cert(title="Public")
    _cert(title="Hidden", is_published=False)

    data = client.get("/api/v1/certifications/").json()

    assert [c["title"] for c in data] == ["Public"]


# --- dynamic content / UI consistency ---------------------------------------


@pytest.mark.django_db
def test_nav_marks_current_section(client):
    import re

    html = client.get(reverse("portfolio:work_list")).content.decode()

    current = re.findall(r'href="([^"]+)"\s+aria-current="page"', html)
    assert current
    assert set(current) == {"/work/"}


@pytest.mark.django_db
def test_header_has_monogram_cta_and_no_js_mobile_menu(client):
    html = client.get(reverse("portfolio:home")).content.decode()

    assert '<span class="brand__mark" aria-hidden="true"><span>MU</span></span>' in html
    assert 'class="nav-cta"' in html
    assert '<details class="nav-drawer"' in html


@pytest.mark.django_db
def test_sound_toggle_is_hidden_until_js_runs(client):
    html = client.get(reverse("portfolio:home")).content.decode()

    start = html.index('id="sound-toggle"')
    toggle = html[start : html.index(">", start)]
    assert "hidden" in toggle


@pytest.mark.django_db
@pytest.mark.parametrize(
    "name", ["portfolio:home", "portfolio:about", "contact:contact", "portfolio:work_list"]
)
def test_no_owner_placeholders_leak_onto_public_pages(client, name):
    assert b"TODO(owner)" not in client.get(reverse(name)).content


@pytest.mark.django_db
def test_headline_and_name_come_from_profile(client):
    profile = Profile.get_solo()
    profile.full_name = "Test Person"
    profile.headline = "Platform engineer"
    profile.save()

    response = client.get(reverse("portfolio:home"))

    assert b"Platform engineer" in response.content
    assert b"<title>Test Person | Platform engineer</title>" in response.content


@pytest.mark.django_db
def test_contact_email_shown_only_when_owner_opts_in(client, settings):
    settings.CONTACT_EMAIL = "owner@example.com"
    profile = Profile.get_solo()

    assert b"owner@example.com" not in client.get(reverse("contact:contact")).content

    profile.public_email_visible = True
    profile.save()

    assert b"mailto:owner@example.com" in client.get(reverse("contact:contact")).content
