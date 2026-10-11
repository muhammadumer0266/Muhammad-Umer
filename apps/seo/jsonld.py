"""JSON-LD builders. Each returns a plain dict built
only from real model/settings data -- never fabricated ratings, reviews or
facts. Callers serialize with json.dumps into a nonce-carrying <script>.
"""

from collections.abc import Iterable
from typing import Any

from django.conf import settings

from apps.portfolio.models import Photo, Profile, SocialLink

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


def absolute(url: str) -> str:
    """Media/static URLs are root-relative; search engines want absolute ones."""
    if url.startswith(("http://", "https://")):
        return url
    return f"{settings.SITE_URL}/{url.lstrip('/')}"


def build_image_object(
    url: str,
    *,
    name: str,
    caption: str = "",
    width: int = 0,
    height: int = 0,
    page_url: str = "",
) -> dict[str, Any]:
    """ImageObject with the creator/credit/copyright fields Google Images
    reads for its image metadata panel. Every photo is the owner's own."""
    data: dict[str, Any] = {
        "@type": "ImageObject",
        "contentUrl": absolute(url),
        "url": absolute(url),
        "name": name,
        "creator": {"@id": _person_id()},
        "creditText": settings.SITE_NAME,
        "copyrightNotice": f"(c) {settings.SITE_NAME}",
        "about": {"@id": _person_id()},
    }
    if caption:
        data["caption"] = caption
    if width and height:
        data["width"] = width
        data["height"] = height
    if page_url:
        data["mainEntityOfPage"] = page_url
    return data


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
        data["image"] = build_image_object(
            profile.photo.url,
            name=f"{profile.full_name}",
            caption=f"Photo of {profile.full_name}",
            page_url=f"{settings.SITE_URL}/about/",
        )
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


def build_photo_gallery(photos: Iterable[Photo]) -> dict[str, Any]:
    page_url = f"{settings.SITE_URL}/photos/"
    return {
        "@type": "ImageGallery",
        "url": page_url,
        "name": f"Photos of {settings.SITE_NAME}",
        "about": {"@id": _person_id()},
        "image": [
            build_image_object(
                photo.image.url,
                name=photo.title,
                caption=photo.caption or photo.alt_text,
                width=photo.width,
                height=photo.height,
                page_url=page_url,
            )
            for photo in photos
        ],
    }
