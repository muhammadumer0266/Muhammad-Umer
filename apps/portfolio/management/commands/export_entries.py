import json
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand

from apps.portfolio.models import Entry


class Command(BaseCommand):
    help = "Export all Entry rows to a JSON file in the import_entries fixture shape."

    def add_arguments(self, parser) -> None:
        parser.add_argument("file", type=str, help="Path to write the JSON file to.")

    def handle(self, *args: Any, **options: Any) -> None:
        path = Path(options["file"])
        rows = [
            {
                "slug": entry.slug,
                "title": entry.title,
                "kind": entry.kind,
                "status": entry.status,
                "date": entry.date.isoformat(),
                "summary": entry.summary,
                "body_md": entry.body_md,
                "tags": list(entry.tags.values_list("name", flat=True)),
                "metrics": entry.metrics,
                "live_url": entry.live_url,
                "repo_url": entry.repo_url,
                "writeup_url": entry.writeup_url,
                "featured": entry.featured,
                "is_published": entry.is_published,
                "is_sample": entry.is_sample,
                "seo_title": entry.seo_title,
                "seo_description": entry.seo_description,
            }
            for entry in Entry.objects.prefetch_related("tags").order_by("slug")
        ]

        path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Exported {len(rows)} entries to {path}."))
