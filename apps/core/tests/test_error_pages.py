import pytest
from django.test import Client, override_settings


@override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver"])
@pytest.mark.django_db
def test_404_page_renders_with_noindex_header():
    client = Client(raise_request_exception=False)

    response = client.get("/this-page-does-not-exist/")

    assert response.status_code == 404
    assert response["X-Robots-Tag"] == "noindex"
    assert b"Page not found" in response.content


@override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver"])
def test_500_handler_renders_standalone_page_without_db(rf):
    from apps.core.views import handler500

    request = rf.get("/")

    response = handler500(request)

    assert response.status_code == 500
    assert response["X-Robots-Tag"] == "noindex"
    assert b"Something went wrong" in response.content
