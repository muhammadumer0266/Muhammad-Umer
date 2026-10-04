import math
import re
from collections import Counter
from collections.abc import Iterator

REFUSAL = (
    "I don't have anything on this site that answers that. Try asking about "
    "Muhammad's projects, stack, or how to get in touch."
)

# Matches the "[chunk:<id>] <text>" blocks that apps.ai.services builds into
# the system prompt for each retrieved chunk.
_CHUNK_BLOCK = re.compile(r"\[chunk:(\d+)\]\s*(.+?)(?=\n\[chunk:\d+\]|\Z)", re.DOTALL)

_WORD_RE = re.compile(r"[a-z0-9]+")
# Common English filler words, removed before vectorizing. Without this, two
# unrelated short texts (e.g. a real question and an off-topic one) share
# enough "the", "is", "what" etc. to push cosine similarity above the
# retrieval threshold even with no real topical overlap -- this was a real
# bug (irrelevant questions were getting "answered" instead of refused)
# caught by manually exercising apps.ai.services.ask() with an off-topic
# question.
_STOPWORDS = frozenset(
    [
        "a",
        "an",
        "the",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "do",
        "does",
        "did",
        "have",
        "has",
        "had",
        "of",
        "in",
        "on",
        "at",
        "to",
        "for",
        "with",
        "from",
        "by",
        "as",
        "it",
        "its",
        "this",
        "that",
        "these",
        "those",
        "and",
        "or",
        "but",
        "if",
        "then",
        "so",
        "than",
        "not",
        "no",
        "nor",
        "what",
        "who",
        "whom",
        "whose",
        "which",
        "how",
        "why",
        "when",
        "where",
        "i",
        "you",
        "he",
        "she",
        "we",
        "they",
        "me",
        "him",
        "her",
        "us",
        "them",
        "my",
        "your",
        "his",
        "our",
        "their",
        "can",
        "could",
        "will",
        "would",
        "should",
        "may",
        "might",
        "must",
        "shall",
    ]
)


class FakeProvider:
    """No-cost, deterministic provider for tests and local dev.

    embed() returns a sparse bag-of-words vector: {word: normalized count}.
    Unlike a fixed-size hashed vector, this has no collisions, so cosine
    similarity between two fake embeddings only reflects real shared
    vocabulary -- which is what keeps retrieval (and the honest-refusal
    behavior for off-topic questions) meaningful in tests without a real
    embedding model or API key. See
    docs/adr/0003-json-embeddings-instead-of-pgvector-for-now.md.
    """

    def embed(self, texts: list[str]) -> list[dict[str, float]]:
        return [self._embed_one(text) for text in texts]

    @staticmethod
    def _embed_one(text: str) -> dict[str, float]:
        words = [w for w in _WORD_RE.findall(text.lower()) if w not in _STOPWORDS]
        counts = Counter(words)
        norm = math.sqrt(sum(c * c for c in counts.values()))
        if norm == 0:
            return {}
        return {word: count / norm for word, count in counts.items()}

    def generate(self, messages: list[dict[str, str]], *, stream: bool = False) -> Iterator[str]:
        system_content = next((m["content"] for m in messages if m["role"] == "system"), "")
        chunks = _CHUNK_BLOCK.findall(system_content)
        if not chunks:
            yield REFUSAL
            return

        chunk_id, text = chunks[0]
        snippet = text.strip().replace("\n", " ")[:240]
        answer = f"Based on the site's content: {snippet} [chunk:{chunk_id}]"
        if stream:
            for word in answer.split(" "):
                yield word + " "
        else:
            yield answer
