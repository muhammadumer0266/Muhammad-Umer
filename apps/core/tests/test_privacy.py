import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_privacy_page_renders(client):
    response = client.get(reverse("core:privacy"))

    assert response.status_code == 200
    assert response.content.count(b"<h1") == 1
    assert b"contact form" in response.content
