"""JSON-LD builders. Each returns a plain dict built
only from real model/settings data -- never fabricated ratings, reviews or
facts. Callers serialize with json.dumps into a nonce-carrying <script>.
"""

from collections.abc import Iterable
from typing import Any

from django.conf import settings

from apps.portfolio.models import Profile, SocialLink

PERSON_ID = "#person"
WEBSITE_ID = "#website"

KNOWS_ABOUT = [
    "Django",
    "Python",
    "PostgreSQL",
    "REST APIs",
    "Retrieval-augmented generation",
    "Rust bindings for Python",
]


def _person_id() -> str:
    return f"{settings.SITE_URL}/{PERSON_ID}"


def build_person(profile: Profile, social_links: Iterable[SocialLink] = ()) -> dict[str, Any]:
    data: dict[str, Any] = {
        "@type": "Person",
        "@id": _person_id(),
        "name": profile.full_name,
        "url": settings.SITE_URL,
        "jobTitle": profile.headline or "Django developer and AI engineer",
        "knowsAbout": KNOWS_ABOUT,
    }
    if profile.alternate_names:
        data["alternateName"] = profile.alternate_names
    if profile.bio_short:
        data["description"] = profile.bio_short
    if profile.photo:
        data["image"] = profile.photo.url
    same_as = [link.url for link in social_links if link.rel_me]
    if same_as:
        data["sameAs"] = same_as
    if profile.public_email_visible and settings.CONTACT_EMAIL:
        data["email"] = settings.CONTACT_EMAIL
    return data


def build_website() -> dict[str, Any]:
    return {
        "@type": "WebSite",
        "@id": f"{settings.SITE_URL}/{WEBSITE_ID}",
        "name": settings.SITE_NAME,
        "url": settings.SITE_URL,
        "publisher": {"@id": _person_id()},
    }


def build_profile_page(profile: Profile) -> dict[str, Any]:
    return {
        "@type": "ProfilePage",
        "url": f"{settings.SITE_URL}/about/",
        "mainEntity": {"@id": _person_id()},
    }
