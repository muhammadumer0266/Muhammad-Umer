import pytest

from apps.ai.providers.fake import FakeProvider
from apps.ai.retrieval import SIMILARITY_THRESHOLD, TOP_K, retrieve
from apps.ai.tests.factories import RagChunkFactory


@pytest.mark.django_db
def test_retrieve_returns_relevant_chunk_above_threshold():
    provider = FakeProvider()
    (embedding,) = provider.embed(["xl-diff is a Rust-backed Excel comparison engine."])
    RagChunkFactory(text="xl-diff is a Rust-backed Excel comparison engine.", embedding=embedding)

    results = retrieve("What is xl-diff written in?", provider)

    assert len(results) == 1
    assert results[0].similarity >= SIMILARITY_THRESHOLD


@pytest.mark.django_db
def test_retrieve_returns_nothing_for_off_topic_question():
    provider = FakeProvider()
    (embedding,) = provider.embed(["xl-diff is a Rust-backed Excel comparison engine."])
    RagChunkFactory(text="xl-diff is a Rust-backed Excel comparison engine.", embedding=embedding)

    results = retrieve("What is the meaning of life?", provider)

    assert results == []


@pytest.mark.django_db
def test_retrieve_returns_no_more_than_top_k():
    provider = FakeProvider()
    for i in range(TOP_K + 5):
        (embedding,) = provider.embed([f"Django backend project number {i} with Django code"])
        RagChunkFactory(text=f"Django backend project number {i}", embedding=embedding)

    results = retrieve("Tell me about the Django backend project", provider)

    assert len(results) <= TOP_K


@pytest.mark.django_db
def test_retrieve_orders_by_similarity_descending():
    provider = FakeProvider()
    (strong,) = provider.embed(["Django REST Framework API backend Django Django"])
    (weak,) = provider.embed(["Django project"])
    RagChunkFactory(text="weak match", embedding=weak)
    RagChunkFactory(text="strong match", embedding=strong)

    results = retrieve("Django REST Framework API backend", provider)

    assert len(results) == 2
    assert results[0].similarity >= results[1].similarity


@pytest.mark.django_db
def test_retrieve_with_no_chunks_returns_empty():
    provider = FakeProvider()

    assert retrieve("anything", provider) == []
