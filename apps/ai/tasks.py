import structlog
from celery import shared_task

from .indexing import reindex

logger = structlog.get_logger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def reindex_rag(self) -> None:
    try:
        stats = reindex()
    except Exception as exc:
        logger.exception("rag.reindex_failed")
        raise self.retry(exc=exc) from exc
    logger.info(
        "rag.reindexed",
        indexed=stats.indexed,
        skipped=stats.skipped,
        removed=stats.removed,
        chunks=stats.chunks,
    )
