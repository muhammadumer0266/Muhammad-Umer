import pytest
from django.urls import reverse

from apps.contact.models import ContactMessage


@pytest.fixture
def admin_client_logged_in(client, django_user_model):
    admin = django_user_model.objects.create_superuser(
        username="admin", email="admin@example.com", password="x"
    )
    client.force_login(admin)
    return client


@pytest.mark.django_db
def test_contact_message_admin_changelist_loads(admin_client_logged_in):
    ContactMessage.objects.create(name="Jane", email="jane@example.com", message="Hi")

    response = admin_client_logged_in.get(reverse("admin:contact_contactmessage_changelist"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_contact_message_admin_has_no_add_permission(admin_client_logged_in):
    response = admin_client_logged_in.get(reverse("admin:contact_contactmessage_add"))

    assert response.status_code == 403
