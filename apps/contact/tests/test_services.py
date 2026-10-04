import pytest
from django.core import mail
from django.test import RequestFactory

from apps.contact.models import ContactMessage
from apps.contact.services import save_contact_message


@pytest.mark.django_db
def test_save_contact_message_never_stores_raw_ip():
    request = RequestFactory().post("/contact/", REMOTE_ADDR="203.0.113.5")

    message = save_contact_message(request, name="Jane", email="jane@example.com", message="Hi")

    assert "203.0.113.5" not in message.ip_hash
    assert message.ip_hash != ""
    assert len(message.ip_hash) == 64  # sha256 hex digest


@pytest.mark.django_db
def test_save_contact_message_persists_fields():
    request = RequestFactory().post("/contact/")

    save_contact_message(request, name="Jane", email="jane@example.com", message="Hi there")

    saved = ContactMessage.objects.get()
    assert saved.name == "Jane"
    assert saved.email == "jane@example.com"
    assert saved.message == "Hi there"
    assert saved.status == ContactMessage.Status.NEW


@pytest.mark.django_db
def test_save_contact_message_queues_notification_email_on_commit(
    settings, django_capture_on_commit_callbacks
):
    settings.CONTACT_EMAIL = "muhammadumer0266@gmail.com"
    request = RequestFactory().post("/contact/")

    with django_capture_on_commit_callbacks(execute=True):
        save_contact_message(request, name="Jane", email="jane@example.com", message="Hi there")

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["muhammadumer0266@gmail.com"]
    assert "Jane" in mail.outbox[0].subject


@pytest.mark.django_db
def test_save_contact_message_skips_email_when_no_recipient_configured(
    settings, django_capture_on_commit_callbacks
):
    settings.CONTACT_EMAIL = ""
    request = RequestFactory().post("/contact/")

    with django_capture_on_commit_callbacks(execute=True):
        save_contact_message(request, name="Jane", email="jane@example.com", message="Hi there")

    assert len(mail.outbox) == 0
