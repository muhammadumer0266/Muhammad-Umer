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
        f"Sitemap: {settings.SITE_URL}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")


def llms_txt(request: HttpRequest) -> HttpResponse:
    profile = Profile.get_solo()
    template = loader.get_template("seo/llms.txt")
    content = template.render({"profile": profile, "SITE_URL": settings.SITE_URL}, request)
    return HttpResponse(content, content_type="text/plain")
