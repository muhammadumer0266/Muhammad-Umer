from apps.ai.chunking import MAX_WORDS, TARGET_WORDS, chunk_markdown


def test_empty_text_returns_no_chunks():
    assert chunk_markdown("") == []
    assert chunk_markdown("   ") == []


def test_short_text_becomes_one_chunk():
    chunks = chunk_markdown("# Heading\n\nA short paragraph.")

    assert len(chunks) == 1
    assert "Heading" in chunks[0]
    assert "short paragraph" in chunks[0]


def test_splits_on_headings():
    text = "# One\n\nFirst section body.\n\n# Two\n\nSecond section body."

    chunks = chunk_markdown(text)

    assert any("First section" in c for c in chunks)
    assert any("Second section" in c for c in chunks)
    assert not any("First section" in c and "Second section" in c for c in chunks)


def test_long_section_splits_into_multiple_chunks_near_target_size():
    paragraph = " ".join(f"word{i}" for i in range(80))  # ~80 words
    text = "# Long\n\n" + "\n\n".join([paragraph] * 8)  # ~640 words

    chunks = chunk_markdown(text)

    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk.split()) <= MAX_WORDS + 20  # some slack for the heading/overlap


def test_chunks_stay_close_to_target_word_count():
    paragraph = " ".join(f"word{i}" for i in range(50))
    text = "\n\n".join([paragraph] * 20)

    chunks = chunk_markdown(text)

    assert len(chunks) >= 2
    # every chunk but possibly the last should be near the target size
    for chunk in chunks[:-1]:
        assert len(chunk.split()) >= TARGET_WORDS * 0.5
