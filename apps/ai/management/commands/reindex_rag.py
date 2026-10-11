from typing import Any

from django.core.management.base import BaseCommand

from apps.ai.indexing import reindex


class Command(BaseCommand):
    help = "Rebuild the RAG index from published entries, certifications and the profile bio."

    def handle(self, *args: Any, **options: Any) -> None:
        stats = reindex()
        self.stdout.write(
            self.style.SUCCESS(
                f"Indexed {stats.indexed} document(s) ({stats.chunks} chunks), "
                f"skipped {stats.skipped} unchanged, removed {stats.removed} unpublished."
            )
        )
