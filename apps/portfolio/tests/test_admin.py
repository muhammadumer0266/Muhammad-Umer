import pytest
from django.urls import reverse

from apps.portfolio.tests.factories import EntryFactory


@pytest.fixture
def admin_client_logged_in(client, django_user_model):
    admin = django_user_model.objects.create_superuser(
        username="admin", email="admin@example.com", password="x"
    )
    client.force_login(admin)
    return client


@pytest.mark.django_db
def test_entry_admin_changelist_loads(admin_client_logged_in):
    EntryFactory()

    response = admin_client_logged_in.get(reverse("admin:portfolio_entry_changelist"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_entry_admin_change_page_shows_markdown_preview(admin_client_logged_in):
    entry = EntryFactory(body_md="# Heading")

    response = admin_client_logged_in.get(reverse("admin:portfolio_entry_change", args=[entry.pk]))

    assert response.status_code == 200
    assert b"<h2>Heading</h2>" in response.content  # headings demoted, see apps.core.markdown


@pytest.mark.django_db
def test_profile_admin_only_allows_one_instance(admin_client_logged_in):
    from apps.portfolio.models import Profile

    Profile.get_solo()

    response = admin_client_logged_in.get(reverse("admin:portfolio_profile_add"))

    assert response.status_code == 403
