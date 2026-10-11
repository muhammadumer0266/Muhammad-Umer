from django.db.models import QuerySet
from django.http import HttpRequest
from django.urls import reverse

from .models import Profile, SocialLink
from .selectors import get_profile, nav_flags


def profile_context(request: HttpRequest) -> dict[str, Profile | QuerySet[SocialLink]]:
    """Profile and social links, available to every template (header/footer)."""
    return {
        "profile": get_profile(request),
        "social_links": SocialLink.objects.all(),
    }


def navigation(request: HttpRequest) -> dict[str, list[dict[str, object]]]:
    """Primary nav, with the current section marked for aria-current.

    Certifications only appears once at least one is published, so the nav
    never links to an empty page.
    """
    items = [
        ("Home", reverse("portfolio:home")),
        ("Work", reverse("portfolio:work_list")),
        ("About", reverse("portfolio:about")),
    ]
    flags = nav_flags()
    if flags["certifications"]:
        items.append(("Certifications", reverse("portfolio:certifications")))
    if flags["photos"]:
        items.append(("Photos", reverse("portfolio:photos")))
    items += [
        ("Ask", reverse("ai:ask")),
        ("Contact", reverse("contact:contact")),
    ]

    path = request.path
    nav = []
    for label, url in items:
        # Home only matches exactly; every other section also owns its subpaths
        # (e.g. /work/<slug>/ keeps "Work" current).
        current = path == url if url == "/" else path.startswith(url)
        # Contact renders as the header's call-to-action, not a plain link.
        nav.append({"label": label, "url": url, "current": current, "cta": label == "Contact"})
    return {"nav_items": nav, "has_resume": flags["resume"]}
