from django.db import models

from apps.core.models import TimeStampedModel


class RagDocument(TimeStampedModel):
    class SourceType(models.TextChoices):
        ENTRY = "entry", "Entry"
        PROFILE = "profile", "Profile"

    source_type = models.CharField(max_length=20, choices=SourceType.choices)
    source_id = models.CharField(max_length=64)
    title = models.CharField(max_length=200)
    url = models.CharField(max_length=500, blank=True)
    content_hash = models.CharField(max_length=64)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source_type", "source_id"], name="unique_rag_document_source"
            )
        ]

    def __str__(self) -> str:
        return self.title


class RagChunk(TimeStampedModel):
    document = models.ForeignKey(RagDocument, on_delete=models.CASCADE, related_name="chunks")
    text = models.TextField()
    token_count = models.PositiveIntegerField()
    # Sparse {feature: weight} mapping, not a fixed-length vector -- see
    # docs/adr/0003 for why this isn't a pgvector VectorField yet, and
    # apps/ai/providers/base.py for why it's a dict rather than a list.
    embedding = models.JSONField(default=dict)

    def __str__(self) -> str:
        return f"{self.document.title} chunk ({self.token_count} tokens)"


class AskLog(TimeStampedModel):
    question = models.CharField(max_length=300)
    matched_chunk_ids = models.JSONField(default=list)
    latency_ms = models.PositiveIntegerField(default=0)
    prompt_tokens = models.PositiveIntegerField(default=0)
    completion_tokens = models.PositiveIntegerField(default=0)
    cost_estimate_usd = models.FloatField(default=0.0)
    refused = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.question


class DailyBudget(TimeStampedModel):
    date = models.DateField(unique=True)
    spent_usd = models.FloatField(default=0.0)

    def __str__(self) -> str:
        return f"{self.date}: ${self.spent_usd:.4f}"
