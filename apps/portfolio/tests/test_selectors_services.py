import pytest

from apps.portfolio.selectors import featured_entries, published_entries
from apps.portfolio.services import feature_entries, publish_entries, unpublish_entries
from apps.portfolio.tests.factories import EntryFactory, TagFactory


@pytest.mark.django_db
def test_published_entries_excludes_unpublished():
    published = EntryFactory(is_published=True)
    EntryFactory(is_published=False)

    result = list(published_entries())

    assert result == [published]


@pytest.mark.django_db
def test_published_entries_filters_by_kind_and_tag():
    tag = TagFactory(slug="django")
    match = EntryFactory(kind="project", is_published=True, tags=[tag])
    EntryFactory(kind="milestone", is_published=True, tags=[tag])
    EntryFactory(kind="project", is_published=True)

    result = list(published_entries(kind="project", tag_slug="django"))

    assert result == [match]


@pytest.mark.django_db
def test_featured_entries_only_returns_featured_projects():
    featured = EntryFactory(kind="project", is_published=True, featured=True)
    EntryFactory(kind="project", is_published=True, featured=False)
    EntryFactory(kind="milestone", is_published=True, featured=True)

    result = list(featured_entries())

    assert result == [featured]


@pytest.mark.django_db
def test_publish_entries_flips_flag_for_selected_only():
    a = EntryFactory(is_published=False)
    b = EntryFactory(is_published=False)

    count = publish_entries([a])

    assert count == 1
    a.refresh_from_db()
    b.refresh_from_db()
    assert a.is_published is True
    assert b.is_published is False


@pytest.mark.django_db
def test_unpublish_and_feature_entries():
    entry = EntryFactory(is_published=True, featured=False)

    unpublish_entries([entry])
    feature_entries([entry])
    entry.refresh_from_db()

    assert entry.is_published is False
    assert entry.featured is True
