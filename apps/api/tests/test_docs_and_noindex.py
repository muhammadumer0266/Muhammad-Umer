import pytest
import yaml
from django.urls import reverse


@pytest.mark.django_db
def test_schema_endpoint_is_valid_openapi(client):
    response = client.get(reverse("api:schema"))

    assert response.status_code == 200
    body = yaml.safe_load(response.content)
    assert "openapi" in body
    assert "paths" in body


@pytest.mark.django_db
def test_docs_page_loads(client):
    response = client.get(reverse("api:docs"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_api_paths_carry_noindex_header(client):
    response = client.get(reverse("api:entry-list"))

    assert response["X-Robots-Tag"] == "noindex"


@pytest.mark.django_db
def test_api_docs_carry_noindex_header(client):
    response = client.get(reverse("api:docs"))

    assert response["X-Robots-Tag"] == "noindex"
