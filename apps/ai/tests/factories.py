import factory
from factory.django import DjangoModelFactory

from apps.ai.models import RagChunk, RagDocument


class RagDocumentFactory(DjangoModelFactory):
    class Meta:
        model = RagDocument

    source_type = RagDocument.SourceType.ENTRY
    source_id = factory.Sequence(lambda n: str(n))
    title = factory.Sequence(lambda n: f"Document {n}")
    url = "/work/example/"
    content_hash = factory.Sequence(lambda n: f"hash-{n}")


class RagChunkFactory(DjangoModelFactory):
    class Meta:
        model = RagChunk

    document = factory.SubFactory(RagDocumentFactory)
    text = "Some chunk text."
    token_count = 3
    embedding: dict = {}
