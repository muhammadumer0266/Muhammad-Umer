import pytest
from django.urls import reverse

from apps.portfolio.tests.factories import EntryFactory, TagFactory


@pytest.mark.django_db
def test_entry_detail_renders_case_study(client, django_assert_max_num_queries):
    entry = EntryFactory(kind="project", body_md="# Case study body", is_published=True)

    with django_assert_max_num_queries(8):
        response = client.get(reverse("portfolio:entry_detail", args=[entry.slug]))

    assert response.status_code == 200
    assert response.content.count(b"<h1") == 1  # heading demotion keeps page title the sole h1
    assert b"<h2>Case study body</h2>" in response.content


@pytest.mark.django_db
def test_entry_detail_404s_for_milestone_kind(client):
    entry = EntryFactory(kind="milestone", body_md="# Notes", is_published=True)

    response = client.get(reverse("portfolio:entry_detail", args=[entry.slug]))

    assert response.status_code == 404


@pytest.mark.django_db
def test_entry_detail_404s_when_no_body(client):
    entry = EntryFactory(kind="project", body_md="", is_published=True)

    response = client.get(reverse("portfolio:entry_detail", args=[entry.slug]))

    assert response.status_code == 404


@pytest.mark.django_db
def test_entry_detail_404s_when_unpublished(client):
    entry = EntryFactory(kind="project", body_md="# Notes", is_published=False)

    response = client.get(reverse("portfolio:entry_detail", args=[entry.slug]))

    assert response.status_code == 404


@pytest.mark.django_db
def test_tag_detail_renders_only_matching_entries(client, django_assert_max_num_queries):
    tag = TagFactory(slug="django", name="Django")
    matching = EntryFactory(is_published=True, tags=[tag], title="Matching entry")
    other = EntryFactory(is_published=True, title="Other entry")

    with django_assert_max_num_queries(8):
        response = client.get(reverse("portfolio:tag_detail", args=[tag.slug]))

    assert response.status_code == 200
    assert response.content.count(b"<h1") == 1
    assert matching.title.encode() in response.content
    assert other.title.encode() not in response.content


@pytest.mark.django_db
def test_tag_detail_404s_for_unknown_tag(client):
    response = client.get(reverse("portfolio:tag_detail", args=["does-not-exist"]))

    assert response.status_code == 404


@pytest.mark.django_db
def test_tag_detail_marks_noindex_when_fewer_than_two_entries(client):
    tag = TagFactory(slug="rust", name="Rust")
    EntryFactory(is_published=True, tags=[tag])

    response = client.get(reverse("portfolio:tag_detail", args=[tag.slug]))

    assert b'name="robots" content="noindex"' in response.content


@pytest.mark.django_db
def test_tag_detail_no_noindex_with_two_or_more_entries(client):
    tag = TagFactory(slug="python", name="Python")
    EntryFactory(is_published=True, tags=[tag])
    EntryFactory(is_published=True, tags=[tag])

    response = client.get(reverse("portfolio:tag_detail", args=[tag.slug]))

    assert b'name="robots" content="noindex"' not in response.content


@pytest.mark.django_db
def test_work_list_htmx_request_returns_partial_only(client):
    EntryFactory(is_published=True)

    response = client.get(reverse("portfolio:work_list"), HTTP_HX_REQUEST="true")

    assert response.status_code == 200
    assert response.templates[0].name == "partials/_work_panel.html"
    assert b"<html" not in response.content


@pytest.mark.django_db
def test_work_list_normal_request_returns_full_page(client):
    response = client.get(reverse("portfolio:work_list"))

    assert response.templates[0].name == "pages/work_list.html"
    assert b"<html" in response.content
