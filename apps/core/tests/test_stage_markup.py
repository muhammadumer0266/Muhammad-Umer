import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_home_includes_canvas_and_scripts_for_js_enhancement(client):
    response = client.get(reverse("portfolio:home"))

    assert b'<canvas id="gl" aria-hidden="true">' in response.content
    assert b'src="/static/js/htmx.min.js"' in response.content
    assert b'src="/static/js/main.js"' in response.content
    assert b'type="module"' in response.content


@pytest.mark.django_db
def test_home_includes_accessible_sound_toggle(client):
    response = client.get(reverse("portfolio:home"))

    assert b'id="sound-toggle"' in response.content
    assert b'aria-pressed="false"' in response.content


@pytest.mark.django_db
def test_page_is_fully_readable_without_js_content_present_in_initial_html(client):
    """The canvas/scripts are enhancements layered on top of real server HTML."""
    response = client.get(reverse("portfolio:home"))

    assert b"Muhammad Umer" in response.content
    assert b"Featured work" in response.content
