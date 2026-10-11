from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.template import loader

from apps.portfolio.models import Profile


def robots_txt(request: HttpRequest) -> HttpResponse:
    lines = [
        "User-agent: *",
        "Allow: /",
        f"Disallow: /{settings.ADMIN_URL}",
        "Disallow: /api/",
        "Disallow: /ask/",
        "Disallow: /resume/download/",
        f"Sitemap: {settings.SITE_URL}/sitemap.xml",
        f"Sitemap: {settings.SITE_URL}/sitemap-images.xml",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")


def llms_txt(request: HttpRequest) -> HttpResponse:
    profile = Profile.get_solo()
    template = loader.get_template("seo/llms.txt")
    content = template.render({"profile": profile, "SITE_URL": settings.SITE_URL}, request)
    return HttpResponse(content, content_type="text/plain")


def image_sitemap(request: HttpRequest) -> HttpResponse:
    """Google image sitemap: every public photo, listed under the page it's on.

    Kept separate from /sitemap.xml because Django's sitemap framework has no
    image extension; both are referenced from robots.txt.
    """
    from xml.sax.saxutils import escape

    from apps.portfolio.models import Photo
    from apps.seo.jsonld import absolute

    pages: dict[str, list[str]] = {}
    profile = Profile.get_solo()
    if profile.photo:
        for path in ("/", "/about/"):
            pages.setdefault(f"{settings.SITE_URL}{path}", []).append(absolute(profile.photo.url))
    for photo in Photo.objects.filter(is_published=True):
        pages.setdefault(f"{settings.SITE_URL}/photos/", []).append(absolute(photo.image.url))
        if photo.show_on_home:
            pages.setdefault(f"{settings.SITE_URL}/", []).append(absolute(photo.image.url))

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">',
    ]
    for page, images in pages.items():
        lines.append(f"<url><loc>{escape(page)}</loc>")
        lines.extend(
            f"<image:image><image:loc>{escape(img)}</image:loc></image:image>"
            for img in dict.fromkeys(images)
        )
        lines.append("</url>")
    lines.append("</urlset>")
    return HttpResponse("\n".join(lines), content_type="application/xml")
