from collections.abc import Iterator
from typing import Protocol


class Provider(Protocol):
    """Interface every AI provider adapter implements.

    Swapping providers means adding a class that satisfies this Protocol --
    call sites never change. Selected by the AI_PROVIDER env var.

    Embeddings are represented as a sparse {feature: weight} mapping rather
    than a fixed-length list. A real provider's dense vector still fits this
    (wrap it as {str(i): v for i, v in enumerate(vector)} at the adapter
    boundary) -- cosine similarity over these dicts works the same either
    way, and it's what lets FakeProvider avoid fixed-dimension hash
    collisions (see apps/ai/providers/fake.py).
    """

    def embed(self, texts: list[str]) -> list[dict[str, float]]: ...

    def generate(self, messages: list[dict[str, str]], *, stream: bool = False) -> Iterator[str]:
        """Yields the response in chunks (a single chunk if stream=False)."""
        ...
