import itertools

from django.core.cache import cache
from django.db.models import QuerySet, Value
from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from .models import Certification, Entry, Photo, Profile, Resume, Tag

NAV_FLAGS_CACHE_KEY = "portfolio:nav-flags"


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


def published_certifications() -> QuerySet[Certification]:
    return Certification.objects.filter(is_published=True).prefetch_related("tags")


def nav_flags() -> dict[str, bool]:
    """Which optional sections have published content, for the nav.

    Asked on every page, so it's one UNION query, cached, and invalidated
    on any certification/photo change (apps/portfolio/signals.py).
    """
    flags = cache.get(NAV_FLAGS_CACHE_KEY)
    if flags is None:
        certs = (
            Certification.objects.filter(is_published=True)
            .order_by()
            .values(kind=Value("certifications"))
        )
        photos = Photo.objects.filter(is_published=True).order_by().values(kind=Value("photos"))
        resumes = Resume.objects.filter(is_active=True).order_by().values(kind=Value("resume"))
        present = {row["kind"] for row in certs.union(photos, resumes)}
        flags = {
            "certifications": "certifications" in present,
            "photos": "photos" in present,
            "resume": "resume" in present,
        }
        cache.set(NAV_FLAGS_CACHE_KEY, flags, 60 * 60)
    return flags


def has_published_certifications() -> bool:
    return nav_flags()["certifications"]


def get_profile(request: HttpRequest | None = None) -> Profile:
    """The singleton profile, fetched at most once per request."""
    if request is None:
        return Profile.get_solo()
    profile = getattr(request, "_portfolio_profile", None)
    if profile is None:
        profile = Profile.get_solo()
        request._portfolio_profile = profile  # type: ignore[attr-defined]
    return profile


def published_photos() -> QuerySet[Photo]:
    return Photo.objects.filter(is_published=True)


def has_published_photos() -> bool:
    return nav_flags()["photos"]
