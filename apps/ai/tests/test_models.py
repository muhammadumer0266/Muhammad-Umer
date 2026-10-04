import pytest
from django.db import IntegrityError

from apps.ai.models import RagChunk, RagDocument
from apps.ai.tests.factories import RagChunkFactory, RagDocumentFactory


@pytest.mark.django_db
def test_rag_document_source_type_and_id_must_be_unique_together():
    RagDocument.objects.create(
        source_type=RagDocument.SourceType.ENTRY,
        source_id="1",
        title="A",
        content_hash="x",
    )

    with pytest.raises(IntegrityError):
        RagDocument.objects.create(
            source_type=RagDocument.SourceType.ENTRY,
            source_id="1",
            title="B",
            content_hash="y",
        )


@pytest.mark.django_db
def test_deleting_document_cascades_to_chunks():
    document = RagDocumentFactory()
    RagChunkFactory(document=document)
    document_pk = document.pk

    document.delete()

    assert RagChunk.objects.filter(document_id=document_pk).count() == 0
