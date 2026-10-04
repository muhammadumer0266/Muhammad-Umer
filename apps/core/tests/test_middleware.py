import pytest
from django.test import override_settings


@pytest.mark.django_db
@override_settings(
    DEBUG=False,
    SITE_URL="https://muhammadumer.dev",
    ALLOWED_HOSTS=["muhammadumer.dev", "www.muhammadumer.dev"],
)
def test_non_canonical_host_redirects_permanently(client):
    response = client.get("/healthz/", HTTP_HOST="www.muhammadumer.dev")

    assert response.status_code == 301
    assert response["Location"] == "https://muhammadumer.dev/healthz/"


@pytest.mark.django_db
@override_settings(
    DEBUG=False,
    SITE_URL="https://muhammadumer.dev",
    ALLOWED_HOSTS=["muhammadumer.dev"],
)
def test_canonical_host_passes_through(client):
    response = client.get("/healthz/", HTTP_HOST="muhammadumer.dev")

    assert response.status_code == 200
