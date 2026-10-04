import pytest
from django.urls import reverse

from apps.ai.models import AskLog
from apps.ai.tests.factories import RagChunkFactory


@pytest.fixture
def admin_client_logged_in(client, django_user_model):
    admin = django_user_model.objects.create_superuser(
        username="admin", email="admin@example.com", password="x"
    )
    client.force_login(admin)
    return client


@pytest.mark.django_db
def test_rag_document_admin_changelist_loads(admin_client_logged_in):
    RagChunkFactory()

    response = admin_client_logged_in.get(reverse("admin:ai_ragdocument_changelist"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_rag_document_admin_has_no_add_permission(admin_client_logged_in):
    response = admin_client_logged_in.get(reverse("admin:ai_ragdocument_add"))

    assert response.status_code == 403


@pytest.mark.django_db
def test_asklog_admin_is_fully_read_only(admin_client_logged_in):
    log = AskLog.objects.create(question="Test question")

    add_response = admin_client_logged_in.get(reverse("admin:ai_asklog_add"))
    change_response = admin_client_logged_in.get(reverse("admin:ai_asklog_change", args=[log.pk]))

    assert add_response.status_code == 403
    assert change_response.status_code == 200
