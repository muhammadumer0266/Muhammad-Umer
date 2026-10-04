import pytest
from django.test import override_settings
from django.urls import reverse

from apps.ai.providers.fake import FakeProvider
from apps.ai.tests.factories import RagChunkFactory


@pytest.mark.django_db
def test_ask_get_renders_form_with_noindex(client):
    response = client.get(reverse("ai:ask"))

    assert response.status_code == 200
    assert response.content.count(b"<h1") == 1
    assert b'name="robots" content="noindex"' in response.content


@pytest.mark.django_db
def test_ask_post_relevant_question_shows_answer_and_citation(client):
    provider = FakeProvider()
    (embedding,) = provider.embed(["xl-diff is a Rust-backed Excel comparison engine."])
    RagChunkFactory(text="xl-diff is a Rust-backed Excel comparison engine.", embedding=embedding)

    response = client.post(reverse("ai:ask"), {"question": "What is xl-diff written in?"})

    assert response.status_code == 200
    assert b"Based on the site" in response.content


@pytest.mark.django_db
def test_ask_post_off_topic_question_shows_honest_refusal(client):
    response = client.post(reverse("ai:ask"), {"question": "What is the meaning of life?"})

    assert response.status_code == 200
    assert b"don&#x27;t have anything on this site" in response.content


@pytest.mark.django_db
def test_ask_post_too_long_question_is_rejected_by_form(client):
    response = client.post(reverse("ai:ask"), {"question": "a" * 400})

    assert response.status_code == 200
    assert b"field-error" in response.content


@pytest.mark.django_db
@override_settings(RATELIMIT_ENABLE=True)
def test_ask_post_is_rate_limited_after_twenty_per_hour(client):
    from django.core.cache import cache

    cache.clear()
    for _ in range(20):
        response = client.post(reverse("ai:ask"), {"question": "What is the meaning of life?"})
        assert response.status_code == 200

    limited_response = client.post(reverse("ai:ask"), {"question": "One more question"})

    assert b"wait a bit" in limited_response.content
    cache.clear()
