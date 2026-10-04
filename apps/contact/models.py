from django.db import models

from apps.core.models import TimeStampedModel


class ContactMessage(TimeStampedModel):
    class Status(models.TextChoices):
        NEW = "new", "New"
        READ = "read", "Read"
        SPAM = "spam", "Spam"

    name = models.CharField(max_length=200)
    email = models.EmailField()
    message = models.TextField(max_length=5000)
    ip_hash = models.CharField(max_length=64, blank=True, help_text="Salted hash, never a raw IP.")
    user_agent_hash = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.NEW)
    spam_score = models.FloatField(default=0.0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} <{self.email}> ({self.created_at:%Y-%m-%d})"
