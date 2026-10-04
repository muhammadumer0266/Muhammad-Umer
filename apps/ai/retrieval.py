"""Retrieval: embed the question, rank chunks by cosine similarity.

Runs the similarity math in Python rather than a pgvector query -- see
docs/adr/0003-json-embeddings-instead-of-pgvector-for-now.md for why, and
what changes when a real Postgres+pgvector instance is available.
"""

import math
from dataclasses import dataclass

from .models import RagChunk
from .providers.base import Provider

TOP_K = 6
SIMILARITY_THRESHOLD = 0.15


@dataclass
class RetrievedChunk:
    chunk: RagChunk
    similarity: float


def _cosine_similarity(a: dict[str, float], b: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    shared_keys = a.keys() & b.keys()
    dot = sum(a[k] * b[k] for k in shared_keys)
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def retrieve(question: str, provider: Provider) -> list[RetrievedChunk]:
    (question_embedding,) = provider.embed([question])

    scored = [
        RetrievedChunk(
            chunk=chunk, similarity=_cosine_similarity(question_embedding, chunk.embedding)
        )
        for chunk in RagChunk.objects.select_related("document").all()
    ]
    scored.sort(key=lambda r: r.similarity, reverse=True)
    above_threshold = [r for r in scored if r.similarity >= SIMILARITY_THRESHOLD]
    return above_threshold[:TOP_K]
