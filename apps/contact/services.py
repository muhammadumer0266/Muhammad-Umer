import hashlib

from django.conf import settings
from django.db import transaction
from django.http import HttpRequest

from .models import ContactMessage
from .tasks import send_contact_notification


def _salted_hash(value: str) -> str:
    if not value:
        return ""
    return hashlib.sha256(f"{settings.SECRET_KEY}:{value}".encode()).hexdigest()


def save_contact_message(
    request: HttpRequest, *, name: str, email: str, message: str
) -> ContactMessage:
    """Persist a contact submission and queue an email notification.

    Never stores a raw IP or user agent. The notification is queued with
    on_commit so it never fires for a save that later rolls back.
    """
    contact_message = ContactMessage.objects.create(
        name=name,
        email=email,
        message=message,
        ip_hash=_salted_hash(request.META.get("REMOTE_ADDR", "")),
        user_agent_hash=_salted_hash(request.META.get("HTTP_USER_AGENT", "")),
    )
    transaction.on_commit(lambda: send_contact_notification.delay(message_id=contact_message.pk))
    return contact_message
