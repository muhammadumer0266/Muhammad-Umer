import pytest
from django.urls import reverse

from apps.portfolio.tests.factories import EntryFactory, TagFactory


@pytest.mark.django_db
def test_list_only_returns_published_non_sample_entries(client):
    published = EntryFactory(is_published=True, is_sample=False, title="Real")
    EntryFactory(is_published=False, is_sample=False, title="Draft")
    EntryFactory(is_published=True, is_sample=True, title="Sample")

    response = client.get(reverse("api:entry-list"))

    assert response.status_code == 200
    slugs = [e["slug"] for e in response.json()["results"]]
    assert slugs == [published.slug]


@pytest.mark.django_db
def test_detail_lookup_by_slug(client):
    entry = EntryFactory(is_published=True, is_sample=False)

    response = client.get(reverse("api:entry-detail", args=[entry.slug]))

    assert response.status_code == 200
    assert response.json()["slug"] == entry.slug


@pytest.mark.django_db
def test_detail_404s_for_unpublished_entry(client):
    entry = EntryFactory(is_published=False)

    response = client.get(reverse("api:entry-detail", args=[entry.slug]))

    assert response.status_code == 404


@pytest.mark.django_db
def test_filters_by_kind(client):
    project = EntryFactory(is_published=True, is_sample=False, kind="project")
    EntryFactory(is_published=True, is_sample=False, kind="milestone")

    response = client.get(reverse("api:entry-list"), {"kind": "project"})

    slugs = [e["slug"] for e in response.json()["results"]]
    assert slugs == [project.slug]


@pytest.mark.django_db
def test_filters_by_tag(client):
    tag = TagFactory(slug="django")
    tagged = EntryFactory(is_published=True, is_sample=False, tags=[tag])
    EntryFactory(is_published=True, is_sample=False)

    response = client.get(reverse("api:entry-list"), {"tag": "django"})

    slugs = [e["slug"] for e in response.json()["results"]]
    assert slugs == [tagged.slug]


@pytest.mark.django_db
def test_response_includes_serialized_tags(client):
    tag = TagFactory(name="Django", slug="django")
    entry = EntryFactory(is_published=True, is_sample=False, tags=[tag])

    response = client.get(reverse("api:entry-detail", args=[entry.slug]))

    assert response.json()["tags"] == [{"name": "Django", "slug": "django"}]


@pytest.mark.django_db
def test_response_never_includes_is_sample_or_is_published_fields(client):
    entry = EntryFactory(is_published=True, is_sample=False)

    response = client.get(reverse("api:entry-detail", args=[entry.slug]))

    body = response.json()
    assert "is_sample" not in body
    assert "is_published" not in body
    assert "body_md" not in body
