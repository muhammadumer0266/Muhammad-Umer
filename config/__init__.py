# Ensures the Celery app is loaded when Django starts, so shared_task-decorated
# tasks bind to it (with Django settings, including CELERY_TASK_ALWAYS_EAGER,
# applied) instead of an unconfigured default Celery instance.
from .celery import app as celery_app

__all__ = ["celery_app"]
