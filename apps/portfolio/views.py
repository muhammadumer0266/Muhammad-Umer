from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from . import selectors
from .models import Entry, SkillGroup


def _name(request: HttpRequest) -> str:
    return selectors.get_profile(request).full_name


def home(request: HttpRequest) -> HttpResponse:
    profile = selectors.get_profile(request)
    context = {
        "featured_entries": selectors.featured_entries(),
        "certifications": (
            selectors.published_certifications()[:3]
            if selectors.has_published_certifications()
            else []
        ),
        "home_photos": (
            selectors.published_photos().filter(show_on_home=True)[:4]
            if selectors.has_published_photos()
            else []
        ),
        "page_title": f"{profile.full_name} | {profile.headline or 'Django & AI Engineer'}",
        "page_description": profile.bio_short
        or (
            f"{profile.full_name} is a Django developer and AI engineer building "
            "production-grade backends, retrieval-augmented tools, and this "
            "site itself."
        ),
    }
    return render(request, "pages/home.html", context)


def work_list(request: HttpRequest) -> HttpResponse:
    kind = request.GET.get("kind") or None
    tag_slug = request.GET.get("tag") or None
    entries = selectors.published_entries(kind=kind, tag_slug=tag_slug)
    name = _name(request)

    context = {
        "entries_by_year": selectors.entries_grouped_by_year(entries),
        "kinds": Entry.Kind.choices,
        "active_kind": kind,
        "active_tag": tag_slug,
        "page_title": f"Work | {name}",
        "page_description": (
            f"Projects, milestones, and what {name} is building, in order, "
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
    name = _name(request)

    context = {
        "entries_by_year": selectors.entries_grouped_by_year(entries),
        "kinds": Entry.Kind.choices,
        "active_kind": kind,
        "active_tag": tag.slug,
        "tag": tag,
        "noindex": unfiltered_count < 2,
        "page_title": f"{tag.name} | Work | {name}",
        "page_description": f"Entries tagged {tag.name} by {name}.",
    }
    template = (
        "partials/_work_panel.html" if getattr(request, "htmx", False) else "pages/tag_detail.html"
    )
    return render(request, template, context)


def entry_detail(request: HttpRequest, slug: str) -> HttpResponse:
    entry = selectors.get_case_study_or_404(slug)
    context = {
        "entry": entry,
        "page_title": entry.seo_title or f"{entry.title} | {_name(request)}",
        "page_description": entry.seo_description or entry.summary,
    }
    return render(request, "pages/entry_detail.html", context)


def about(request: HttpRequest) -> HttpResponse:
    name = _name(request)
    context = {
        "skill_groups": SkillGroup.objects.prefetch_related("skills"),
        "certifications": (
            selectors.published_certifications() if selectors.has_published_certifications() else []
        ),
        "page_title": f"About | {name}",
        "page_description": (
            f"Who {name} is, what he builds, and the stack behind this site, in his own words."
        ),
    }
    return render(request, "pages/about.html", context)


def certifications(request: HttpRequest) -> HttpResponse:
    name = _name(request)
    context = {
        "certifications": selectors.published_certifications(),
        "page_title": f"Certifications | {name}",
        "page_description": (
            f"Certifications and credentials earned by {name}, with issuer "
            "verification links where available."
        ),
    }
    return render(request, "pages/certifications.html", context)


def photos(request: HttpRequest) -> HttpResponse:
    name = _name(request)
    context = {
        "photos": selectors.published_photos(),
        "page_title": f"Photos | {name}",
        "page_description": (
            f"Photos of {name}, Django developer and AI engineer: talks, events, "
            "work and portraits."
        ),
    }
    return render(request, "pages/photos.html", context)
