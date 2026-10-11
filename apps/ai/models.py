import re

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel


class RagDocument(TimeStampedModel):
    class SourceType(models.TextChoices):
        ENTRY = "entry", "Entry"
        PROFILE = "profile", "Profile"
        CERTIFICATION = "certification", "Certification"

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
    guardrail = models.CharField(
        max_length=120, blank=True, help_text="Which guardrail stopped or altered this answer."
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.question


class DailyBudget(TimeStampedModel):
    date = models.DateField(unique=True)
    spent_usd = models.FloatField(default=0.0)

    def __str__(self) -> str:
        return f"{self.date}: ${self.spent_usd:.4f}"


class GuardrailPolicy(TimeStampedModel):
    """Runtime-tunable Ask settings, edited from the admin (singleton, pk=1).

    The built-in baseline in apps/ai/guardrails.py (prompt-injection
    detection, system-prompt leak blocking, citation validation, poisoned
    context filtering) always runs and can't be turned off here -- this only
    tunes thresholds and adds layers on top of it.
    """

    enabled = models.BooleanField(
        default=True, help_text="Kill switch: untick to take Ask offline immediately."
    )
    disabled_message = models.CharField(
        max_length=300, default="The Ask demo is temporarily offline. Please try again later."
    )
    refusal_message = models.CharField(
        max_length=300,
        default=(
            "I can only answer questions about the work published on this site, "
            "so I can't help with that one."
        ),
        help_text="Shown when an input guardrail blocks a question.",
    )
    no_answer_message = models.CharField(
        max_length=300,
        default=(
            "I don't have anything on this site that answers that. Try asking "
            "about the projects, stack, certifications, or how to get in touch."
        ),
        help_text="Shown when nothing relevant is indexed, or an answer fails output checks.",
    )
    min_question_length = models.PositiveIntegerField(
        default=3, validators=[MinValueValidator(1), MaxValueValidator(50)]
    )
    max_question_length = models.PositiveIntegerField(
        default=300,
        validators=[MinValueValidator(20), MaxValueValidator(1000)],
        help_text="Hard ceiling 1000 characters.",
    )
    similarity_threshold = models.FloatField(
        default=0.15,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Minimum chunk relevance. Higher = more refusals, fewer guesses.",
    )
    top_k = models.PositiveIntegerField(
        default=6, validators=[MinValueValidator(1), MaxValueValidator(20)]
    )
    max_answer_chars = models.PositiveIntegerField(
        default=2000, validators=[MinValueValidator(200), MaxValueValidator(8000)]
    )
    rate_limit_per_hour = models.PositiveIntegerField(
        default=20,
        validators=[MinValueValidator(1), MaxValueValidator(1000)],
        help_text="Questions per visitor IP per hour.",
    )
    require_citations = models.BooleanField(
        default=True,
        help_text="Refuse any answer that doesn't cite at least one retrieved source.",
    )
    redact_pii = models.BooleanField(
        default=True,
        help_text="Redact emails, phone numbers and secret-looking tokens from answers.",
    )

    class Meta:
        verbose_name = "guardrail policy"
        verbose_name_plural = "guardrail policy"
        constraints = [
            models.CheckConstraint(condition=models.Q(pk=1), name="ai_guardrailpolicy_singleton")
        ]

    def __str__(self) -> str:
        return "Ask guardrail policy"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("The guardrail policy cannot be deleted.")

    def clean(self) -> None:
        if self.min_question_length >= self.max_question_length:
            raise ValidationError(
                {"min_question_length": "Must be smaller than the maximum question length."}
            )

    @classmethod
    def get_solo(cls) -> "GuardrailPolicy":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


# Nested quantifiers like (a+)+ or (\w*)* can backtrack exponentially
# (ReDoS). Admin-entered patterns are rejected if they contain one.
_NESTED_QUANTIFIER = re.compile(r"\([^)]*[+*}][^)]*\)\s*[+*{]")
MAX_PATTERN_LENGTH = 200


class GuardrailRule(TimeStampedModel):
    """An admin-defined guardrail, applied live without a deploy."""

    class Stage(models.TextChoices):
        INPUT = "input", "Question (before retrieval)"
        CONTEXT = "context", "Retrieved context (before generation)"
        OUTPUT = "output", "Answer (before it's shown)"

    class MatchType(models.TextChoices):
        KEYWORD = "keyword", "Keyword / phrase (case-insensitive)"
        REGEX = "regex", "Regular expression (case-insensitive)"

    class Action(models.TextChoices):
        BLOCK = "block", "Block (refuse / drop)"
        REDACT = "redact", "Redact the match (output only)"

    name = models.CharField(max_length=100, unique=True)
    stage = models.CharField(max_length=10, choices=Stage.choices, default=Stage.INPUT)
    match_type = models.CharField(
        max_length=10, choices=MatchType.choices, default=MatchType.KEYWORD
    )
    pattern = models.CharField(max_length=MAX_PATTERN_LENGTH)
    action = models.CharField(max_length=10, choices=Action.choices, default=Action.BLOCK)
    message = models.CharField(
        max_length=300,
        blank=True,
        help_text="Optional custom refusal text; defaults to the policy's refusal message.",
    )
    is_active = models.BooleanField(default=True)
    priority = models.PositiveIntegerField(default=100, help_text="Lower runs first.")
    hit_count = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        ordering = ["stage", "priority", "name"]

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        if self.action == self.Action.REDACT and self.stage != self.Stage.OUTPUT:
            raise ValidationError(
                {"action": "Redaction only applies to the answer (output) stage."}
            )
        if self.match_type == self.MatchType.REGEX:
            if _NESTED_QUANTIFIER.search(self.pattern):
                raise ValidationError(
                    {
                        "pattern": (
                            "Nested quantifiers like (a+)+ aren't allowed "
                            "(catastrophic backtracking)."
                        )
                    }
                )
            try:
                re.compile(self.pattern)
            except re.error as exc:
                raise ValidationError({"pattern": f"Invalid regular expression: {exc}"}) from exc
        elif not self.pattern.strip():
            raise ValidationError({"pattern": "Enter a keyword or phrase."})
