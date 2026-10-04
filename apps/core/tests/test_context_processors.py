from django.test import RequestFactory

from apps.core.context_processors import site_meta


def test_site_meta_exposes_name_and_url(settings):
    settings.SITE_NAME = "Muhammad Umer"
    settings.SITE_URL = "https://muhammadumer.dev"
    settings.GOOGLE_SITE_VERIFICATION = ""
    settings.BING_SITE_VERIFICATION = ""
    request = RequestFactory().get("/")

    context = site_meta(request)

    assert context == {
        "SITE_NAME": "Muhammad Umer",
        "SITE_URL": "https://muhammadumer.dev",
        "GOOGLE_SITE_VERIFICATION": "",
        "BING_SITE_VERIFICATION": "",
    }
