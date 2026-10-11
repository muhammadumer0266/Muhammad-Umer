from django.dispatch import Signal

# Sent after bulk changes that bypass post_save (QuerySet.update() in
# services.py), so listeners like the RAG indexer still see them.
content_changed = Signal()


def _invalidate_certification_cache(**kwargs) -> None:
    from django.core.cache import cache

    from .selectors import HAS_CERTIFICATIONS_CACHE_KEY

    cache.delete(HAS_CERTIFICATIONS_CACHE_KEY)


def connect() -> None:
    from django.db.models.signals import post_delete, post_save

    from .models import Certification

    post_save.connect(
        _invalidate_certification_cache, sender=Certification, dispatch_uid="cert-cache-save"
    )
    post_delete.connect(
        _invalidate_certification_cache, sender=Certification, dispatch_uid="cert-cache-del"
    )
