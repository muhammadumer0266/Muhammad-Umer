from apps.ai.providers.fake import REFUSAL, FakeProvider


def test_embed_returns_one_vector_per_text():
    provider = FakeProvider()

    vectors = provider.embed(["hello world", "goodbye"])

    assert len(vectors) == 2


def test_embed_ignores_stopwords():
    provider = FakeProvider()

    vector = provider.embed(["what is the meaning of this"])[0]

    assert "meaning" in vector
    assert "is" not in vector
    assert "the" not in vector
    assert "what" not in vector


def test_embed_empty_text_returns_empty_vector():
    provider = FakeProvider()

    assert provider.embed([""])[0] == {}


def test_embed_is_deterministic():
    provider = FakeProvider()

    assert provider.embed(["Rust and Python"]) == provider.embed(["Rust and Python"])


def test_generate_refuses_when_no_context_chunks_present():
    provider = FakeProvider()

    result = "".join(provider.generate([{"role": "user", "content": "hi"}]))

    assert result == REFUSAL


def test_generate_answers_and_cites_first_chunk():
    messages = [
        {"role": "system", "content": "[chunk:1] xl-diff is written in Rust."},
        {"role": "user", "content": "What is xl-diff written in?"},
    ]
    provider = FakeProvider()

    result = "".join(provider.generate(messages))

    assert "[chunk:1]" in result
    assert "xl-diff is written in Rust" in result


def test_generate_streaming_yields_multiple_chunks():
    messages = [{"role": "system", "content": "[chunk:1] Some content here."}]
    provider = FakeProvider()

    parts = list(provider.generate(messages, stream=True))

    assert len(parts) > 1
    assert "".join(parts).strip().endswith("[chunk:1]")
