from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from . import selectors
from .models import Entry, SkillGroup


def home(request: HttpRequest) -> HttpResponse:
    context = {
        "featured_entries": selectors.featured_entries(),
        "page_title": "Muhammad Umer | Django & AI Engineer",
        "page_description": (
            "Muhammad Umer is a Django developer and AI engineer building "
            "production-grade backends, retrieval-augmented tools, and this "
            "site itself."
        ),
    }
    return render(request, "pages/home.html", context)


def work_list(request: HttpRequest) -> HttpResponse:
    kind = request.GET.get("kind") or None
    tag_slug = request.GET.get("tag") or None
    entries = selectors.published_entries(kind=kind, tag_slug=tag_slug)

    context = {
        "entries_by_year": selectors.entries_grouped_by_year(entries),
        "kinds": Entry.Kind.choices,
        "active_kind": kind,
        "active_tag": tag_slug,
        "page_title": "Work | Muhammad Umer",
        "page_description": (
            "Projects, milestones, and what Muhammad Umer is building, in order, "
            "newest first, with real repositories and live links where they exist."
        ),
    }
    template = (
        "partials/_work_panel.html" if getattr(request, "htmx", False) else "pages/work_list.html"
    )
    return render(request, template, context)


def tag_detail(request: HttpRequest, slug: str) -> HttpResponse:
    tag = selectors.get_tag_or_404(slug)
    kind = request.GET.get("kind") or None
    entries = selectors.published_entries(kind=kind, tag_slug=tag.slug)
    # Avoid a second query in the common case (no kind filter): the
    # unfiltered set for noindex purposes is then exactly `entries`.
    unfiltered_count = (
        len(entries) if kind is None else selectors.published_entries(tag_slug=tag.slug).count()
    )

    context = {
        "entries_by_year": selectors.entries_grouped_by_year(entries),
        "kinds": Entry.Kind.choices,
        "active_kind": kind,
        "active_tag": tag.slug,
        "tag": tag,
        "noindex": unfiltered_count < 2,
        "page_title": f"{tag.name} | Work | Muhammad Umer",
        "page_description": f"Entries tagged {tag.name} by Muhammad Umer.",
    }
    template = (
        "partials/_work_panel.html" if getattr(request, "htmx", False) else "pages/tag_detail.html"
    )
    return render(request, template, context)


def entry_detail(request: HttpRequest, slug: str) -> HttpResponse:
    entry = selectors.get_case_study_or_404(slug)
    context = {
        "entry": entry,
        "page_title": entry.seo_title or f"{entry.title} | Muhammad Umer",
        "page_description": entry.seo_description or entry.summary,
    }
    return render(request, "pages/entry_detail.html", context)


def about(request: HttpRequest) -> HttpResponse:
    context = {
        "skill_groups": SkillGroup.objects.prefetch_related("skills"),
        "page_title": "About | Muhammad Umer",
        "page_description": (
            "Who Muhammad Umer is, what he builds, and the stack behind this site, "
            "in his own words."
        ),
    }
    return render(request, "pages/about.html", context)
