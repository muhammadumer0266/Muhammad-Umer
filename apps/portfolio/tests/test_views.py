import pytest
from django.urls import reverse

from apps.portfolio.tests.factories import EntryFactory, TagFactory


@pytest.mark.django_db
def test_home_renders_200_with_single_h1(client, django_assert_max_num_queries):
    EntryFactory(featured=True, kind="project", is_published=True)

    with django_assert_max_num_queries(8):
        response = client.get(reverse("portfolio:home"))

    assert response.status_code == 200
    assert response.content.count(b"<h1") == 1
    assert response.templates[0].name == "pages/home.html"


@pytest.mark.django_db
def test_home_only_shows_featured_published_projects(client):
    shown = EntryFactory(featured=True, kind="project", is_published=True, title="Shown")
    EntryFactory(featured=False, kind="project", is_published=True, title="Not featured")
    EntryFactory(featured=True, kind="project", is_published=False, title="Unpublished")

    response = client.get(reverse("portfolio:home"))

    assert shown.title.encode() in response.content
    assert b"Not featured" not in response.content
    assert b"Unpublished" not in response.content


@pytest.mark.django_db
def test_work_list_renders_and_groups_by_year(client, django_assert_max_num_queries):
    EntryFactory(is_published=True)

    with django_assert_max_num_queries(8):
        response = client.get(reverse("portfolio:work_list"))

    assert response.status_code == 200
    assert response.content.count(b"<h1") == 1


@pytest.mark.django_db
def test_work_list_filters_by_kind_via_query_param(client):
    project = EntryFactory(kind="project", is_published=True, title="A project")
    milestone = EntryFactory(kind="milestone", is_published=True, title="A milestone")

    response = client.get(reverse("portfolio:work_list"), {"kind": "project"})

    assert project.title.encode() in response.content
    assert milestone.title.encode() not in response.content


@pytest.mark.django_db
def test_work_list_filters_by_tag_via_query_param(client):
    tag = TagFactory(slug="django", name="Django")
    tagged = EntryFactory(is_published=True, tags=[tag], title="Tagged entry")
    untagged = EntryFactory(is_published=True, title="Untagged entry")

    response = client.get(reverse("portfolio:work_list"), {"tag": "django"})

    assert tagged.title.encode() in response.content
    assert untagged.title.encode() not in response.content


@pytest.mark.django_db
def test_about_renders_200_with_single_h1(client, django_assert_max_num_queries):
    with django_assert_max_num_queries(8):
        response = client.get(reverse("portfolio:about"))

    assert response.status_code == 200
    assert response.content.count(b"<h1") == 1
