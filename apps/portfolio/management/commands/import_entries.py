import datetime
import json
from pathlib import Path
from typing import Any

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import URLValidator
from django.db import transaction
from django.utils.text import slugify

from apps.portfolio.models import Entry, Tag

_url_validator = URLValidator()

# Fields accepted straight from the fixture shape.
_REQUIRED_FIELDS = {"slug", "title", "kind", "date", "summary"}
_URL_FIELDS = ("live_url", "repo_url", "writeup_url")


def _validate_url(value: str, field: str, slug: str) -> None:
    if not value:
        return
    try:
        _url_validator(value)
    except ValidationError as exc:
        raise CommandError(f"Entry '{slug}': invalid {field} '{value}'") from exc


class Command(BaseCommand):
    help = "Idempotently import Entry rows from a JSON fixture."

    def add_arguments(self, parser) -> None:
        parser.add_argument("file", type=str, help="Path to a JSON file: a list of entry dicts.")

    def handle(self, *args: Any, **options: Any) -> None:
        path = Path(options["file"])
        if not path.exists():
            raise CommandError(f"File not found: {path}")

        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CommandError(f"Invalid JSON in {path}: {exc}") from exc

        if not isinstance(rows, list):
            raise CommandError("Expected the JSON file to contain a list of entry objects.")

        created, updated = 0, 0
        with transaction.atomic():
            for row in rows:
                missing = _REQUIRED_FIELDS - row.keys()
                if missing:
                    raise CommandError(f"Entry missing required fields {missing}: {row}")

                slug = row["slug"]
                for field in _URL_FIELDS:
                    _validate_url(row.get(field, ""), field, slug)

                date = datetime.date.fromisoformat(row["date"]).replace(day=1)
                tag_names = row.get("tags", [])
                tags = [
                    Tag.objects.get_or_create(name=name, defaults={"slug": slugify(name)})[0]
                    for name in tag_names
                ]

                defaults = {
                    "title": row["title"],
                    "kind": row["kind"],
                    "status": row.get("status", ""),
                    "date": date,
                    "summary": row["summary"],
                    "body_md": row.get("body_md", ""),
                    "metrics": row.get("metrics", []),
                    "live_url": row.get("live_url", ""),
                    "repo_url": row.get("repo_url", ""),
                    "writeup_url": row.get("writeup_url", ""),
                    "featured": row.get("featured", False),
                    "is_published": row.get("is_published", False),
                    "is_sample": row.get("is_sample", False),
                    "seo_title": row.get("seo_title", ""),
                    "seo_description": row.get("seo_description", ""),
                }
                entry, was_created = Entry.objects.update_or_create(slug=slug, defaults=defaults)
                entry.tags.set(tags)
                created += was_created
                updated += not was_created

        self.stdout.write(self.style.SUCCESS(f"Imported: {created} created, {updated} updated."))
