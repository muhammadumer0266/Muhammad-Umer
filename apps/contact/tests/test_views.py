import time

import pytest
from django.core import signing
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse

from apps.contact.models import ContactMessage

_SALT = "apps.contact.forms.ContactForm.rendered_at"


def _rendered_at(seconds_ago: float = 5) -> str:
    return signing.dumps(time.time() - seconds_ago, salt=_SALT)


@pytest.mark.django_db
def test_contact_get_renders_form(client):
    response = client.get(reverse("contact:contact"))

    assert response.status_code == 200
    assert response.content.count(b"<h1") == 1
    assert b'name="message"' in response.content


@pytest.mark.django_db
def test_contact_post_valid_saves_and_redirects(client):
    response = client.post(
        reverse("contact:contact"),
        {
            "name": "Jane",
            "email": "jane@example.com",
            "message": "Hello there",
            "rendered_at": _rendered_at(),
        },
    )

    assert response.status_code == 302
    assert ContactMessage.objects.count() == 1


@pytest.mark.django_db
def test_contact_post_honeypot_filled_does_not_save(client):
    response = client.post(
        reverse("contact:contact"),
        {
            "name": "Bot",
            "email": "bot@example.com",
            "message": "spam",
            "website": "http://spam.example",
            "rendered_at": _rendered_at(),
        },
    )

    assert response.status_code == 200
    assert ContactMessage.objects.count() == 0


@pytest.mark.django_db
def test_contact_post_submitted_too_fast_does_not_save(client):
    response = client.post(
        reverse("contact:contact"),
        {
            "name": "Bot",
            "email": "bot@example.com",
            "message": "instant spam",
            "rendered_at": _rendered_at(0),
        },
    )

    assert response.status_code == 200
    assert ContactMessage.objects.count() == 0


@pytest.mark.django_db
@override_settings(RATELIMIT_ENABLE=True)
def test_contact_post_is_rate_limited_after_five_per_hour(client):
    cache.clear()
    payload = {
        "name": "Jane",
        "email": "jane@example.com",
        "message": "Hello there",
    }
    for _ in range(5):
        response = client.post(
            reverse("contact:contact"), {**payload, "rendered_at": _rendered_at()}
        )
        assert response.status_code == 302

    sixth = client.post(reverse("contact:contact"), {**payload, "rendered_at": _rendered_at()})

    assert sixth.status_code == 429
    assert ContactMessage.objects.count() == 5
    cache.clear()


@pytest.mark.django_db
def test_contact_post_invalid_reshows_form_with_errors(client):
    response = client.post(reverse("contact:contact"), {"name": "", "email": "", "message": ""})

    assert response.status_code == 200
    assert ContactMessage.objects.count() == 0
    assert b"field-error" in response.content
