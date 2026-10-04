import structlog
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from .models import ContactMessage

logger = structlog.get_logger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_contact_notification(self, message_id: int) -> None:
    try:
        message = ContactMessage.objects.get(pk=message_id)
    except ContactMessage.DoesNotExist:
        logger.warning("contact_notification.message_missing", message_id=message_id)
        return

    if not settings.CONTACT_EMAIL:
        logger.info("contact_notification.no_recipient_configured", message_id=message_id)
        return

    try:
        send_mail(
            subject=f"New contact message from {message.name}",
            message=(
                f"From: {message.name} <{message.email}>\n\n{message.message}\n\n"
                f"Manage: {settings.SITE_URL}/{settings.ADMIN_URL}contact/contactmessage/"
                f"{message.pk}/change/"
            ),
            from_email=None,
            recipient_list=[settings.CONTACT_EMAIL],
            fail_silently=False,
        )
    except Exception as exc:
        raise self.retry(exc=exc) from exc
