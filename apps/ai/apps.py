from django.apps import AppConfig


class AiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ai"
    label = "ai"

    def ready(self) -> None:
        from . import signals  # noqa: F401 -- connects reindex + cache-invalidation hooks
