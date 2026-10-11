"""Keeps Ask in sync with the admin, with no manual steps.

- Content edits (entries, profile, certifications) schedule a RAG reindex
  after the transaction commits, so Ask never answers from stale or
  unpublished content.
- Guardrail policy/rule edits invalidate the guardrail cache immediately,
  so a new rule (or the kill switch) applies to the very next question.
"""

import structlog
from django.conf import settings
from django.db import transaction
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from apps.portfolio.models import Certification, Entry, Profile
from apps.portfolio.signals import content_changed

from . import guardrails
from .models import GuardrailPolicy, GuardrailRule

logger = structlog.get_logger(__name__)


def schedule_reindex(**kwargs) -> None:
    if not getattr(settings, "AI_AUTO_REINDEX", True):
        return

    def _enqueue() -> None:
        from .tasks import reindex_rag

        try:
            reindex_rag.delay()
        except Exception:  # broker down must never break an admin save
            logger.exception("rag.reindex_enqueue_failed")

    transaction.on_commit(_enqueue)


for _model in (Entry, Profile, Certification):
    post_save.connect(schedule_reindex, sender=_model, dispatch_uid=f"rag-save-{_model.__name__}")
    post_delete.connect(schedule_reindex, sender=_model, dispatch_uid=f"rag-del-{_model.__name__}")
m2m_changed.connect(
    schedule_reindex, sender=Certification.tags.through, dispatch_uid="rag-cert-tags"
)
content_changed.connect(schedule_reindex, dispatch_uid="rag-content-changed")


@receiver(post_save, sender=GuardrailPolicy, dispatch_uid="guardrail-policy-save")
@receiver(post_save, sender=GuardrailRule, dispatch_uid="guardrail-rule-save")
@receiver(post_delete, sender=GuardrailRule, dispatch_uid="guardrail-rule-delete")
def _invalidate_guardrails(**kwargs) -> None:
    guardrails.invalidate_cache()
