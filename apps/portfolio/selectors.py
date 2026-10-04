import itertools

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from .models import Entry, Tag


def published_entries(*, kind: str | None = None, tag_slug: str | None = None) -> QuerySet[Entry]:
    qs = Entry.objects.filter(is_published=True).prefetch_related("tags")
    if kind:
        qs = qs.filter(kind=kind)
    if tag_slug:
        qs = qs.filter(tags__slug=tag_slug)
    return qs.distinct()


def featured_entries(limit: int = 3) -> QuerySet[Entry]:
    return published_entries(kind=Entry.Kind.PROJECT).filter(featured=True)[:limit]


def entries_grouped_by_year(entries: QuerySet[Entry]) -> list[tuple[int, list[Entry]]]:
    # Relies on Entry.Meta.ordering (-date) rather than re-ordering here, so
    # callers that already evaluated `entries` don't trigger a second query.
    return [
        (year, list(group)) for year, group in itertools.groupby(entries, key=lambda e: e.date.year)
    ]


def get_case_study_or_404(slug: str) -> Entry:
    return get_object_or_404(
        Entry.objects.exclude(body_md=""),
        slug=slug,
        kind=Entry.Kind.PROJECT,
        is_published=True,
    )


def get_tag_or_404(slug: str) -> Tag:
    return get_object_or_404(Tag, slug=slug)
