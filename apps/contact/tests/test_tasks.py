import pytest
from django.core import mail

from apps.contact.models import ContactMessage
from apps.contact.tasks import send_contact_notification


@pytest.mark.django_db
def test_send_contact_notification_handles_missing_message_gracefully():
    send_contact_notification(message_id=999999)

    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_send_contact_notification_sends_email(settings):
    settings.CONTACT_EMAIL = "muhammadumer0266@gmail.com"
    message = ContactMessage.objects.create(name="Jane", email="jane@example.com", message="Hi")

    send_contact_notification(message_id=message.pk)

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["muhammadumer0266@gmail.com"]
