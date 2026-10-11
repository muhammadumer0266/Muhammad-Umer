from django.dispatch import Signal

# Sent after bulk changes that bypass post_save (QuerySet.update() in
# services.py), so listeners like the RAG indexer still see them.
content_changed = Signal()


def _invalidate_nav_flags(**kwargs) -> None:
    from django.core.cache import cache

    from .selectors import NAV_FLAGS_CACHE_KEY

    cache.delete(NAV_FLAGS_CACHE_KEY)


def connect() -> None:
    from django.db.models.signals import post_delete, post_save

    from .models import Certification, Photo, Resume

    post_save.connect(_invalidate_nav_flags, sender=Certification, dispatch_uid="cert-cache-save")
    post_delete.connect(_invalidate_nav_flags, sender=Certification, dispatch_uid="cert-cache-del")
    post_save.connect(_invalidate_nav_flags, sender=Photo, dispatch_uid="photo-cache-save")
    post_delete.connect(_invalidate_nav_flags, sender=Photo, dispatch_uid="photo-cache-del")
    post_save.connect(_invalidate_nav_flags, sender=Resume, dispatch_uid="resume-cache-save")
    post_delete.connect(_invalidate_nav_flags, sender=Resume, dispatch_uid="resume-cache-del")
