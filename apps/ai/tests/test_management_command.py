import pytest
from django.core.management import call_command

from apps.ai.models import RagChunk, RagDocument
from apps.portfolio.tests.factories import EntryFactory


@pytest.mark.django_db
def test_reindex_rag_indexes_published_non_sample_entries_with_body():
    EntryFactory(
        kind="project",
        body_md="# Title\n\nSome real content here about the project.",
        is_published=True,
        is_sample=False,
    )

    call_command("reindex_rag")

    assert RagDocument.objects.count() == 1
    assert RagChunk.objects.count() >= 1


@pytest.mark.django_db
def test_reindex_rag_skips_sample_entries():
    EntryFactory(
        kind="project", body_md="# Sample\n\nSample content.", is_sample=True, is_published=True
    )

    call_command("reindex_rag")

    assert RagDocument.objects.count() == 0


@pytest.mark.django_db
def test_reindex_rag_skips_unpublished_entries():
    EntryFactory(
        kind="project", body_md="# Draft\n\nDraft content.", is_published=False, is_sample=False
    )

    call_command("reindex_rag")

    assert RagDocument.objects.count() == 0


@pytest.mark.django_db
def test_reindex_rag_is_idempotent_for_unchanged_content():
    EntryFactory(kind="project", body_md="# Title\n\nContent.", is_published=True, is_sample=False)

    call_command("reindex_rag")
    first_chunk_ids = set(RagChunk.objects.values_list("pk", flat=True))
    call_command("reindex_rag")
    second_chunk_ids = set(RagChunk.objects.values_list("pk", flat=True))

    assert first_chunk_ids == second_chunk_ids


@pytest.mark.django_db
def test_reindex_rag_rebuilds_chunks_when_content_changes():
    entry = EntryFactory(
        kind="project", body_md="# Title\n\nOriginal content.", is_published=True, is_sample=False
    )

    call_command("reindex_rag")
    original_chunk = RagChunk.objects.get()

    entry.body_md = "# Title\n\nCompletely different content now."
    entry.save()
    call_command("reindex_rag")

    remaining = RagChunk.objects.get()
    assert remaining.text != original_chunk.text
