import pytest
from django.urls import reverse

from apps.portfolio.models import Profile
from apps.portfolio.tests.factories import TagFactory


@pytest.mark.django_db
def test_tag_list_returns_all_tags(client):
    TagFactory(name="Django", slug="django")
    TagFactory(name="Rust", slug="rust")

    response = client.get(reverse("api:tag-list"))

    assert response.status_code == 200
    slugs = {t["slug"] for t in response.json()}
    assert slugs == {"django", "rust"}


@pytest.mark.django_db
def test_profile_endpoint_returns_singleton(client):
    profile = Profile.get_solo()
    profile.headline = "Django and AI engineer"
    profile.save()

    response = client.get(reverse("api:profile"))

    assert response.status_code == 200
    body = response.json()
    assert body["full_name"] == "Muhammad Umer"
    assert body["headline"] == "Django and AI engineer"


@pytest.mark.django_db
def test_profile_endpoint_never_includes_bio_md_or_email(client):
    response = client.get(reverse("api:profile"))

    body = response.json()
    assert "bio_md" not in body
    assert "public_email_visible" not in body
