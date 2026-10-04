import pytest


@pytest.mark.django_db
def test_llms_txt_returns_plain_text_summary(client, settings):
    response = client.get("/llms.txt")

    assert response.status_code == 200
    assert response["Content-Type"] == "text/plain"
    body = response.content.decode()
    assert "Muhammad Umer" in body
    assert settings.SITE_URL in body


@pytest.mark.django_db
def test_robots_txt_content_type_is_plain_text(client):
    response = client.get("/robots.txt")

    assert response["Content-Type"] == "text/plain"
