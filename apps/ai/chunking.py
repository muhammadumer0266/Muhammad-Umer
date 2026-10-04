"""Splits Markdown into chunks by heading/paragraph, ~300-500 tokens with a
small overlap. "Tokens" here is a plain word count --
close enough for chunk sizing without pulling in a real tokenizer, and the
FakeProvider doesn't have a real token vocabulary to count against anyway.
"""

import re

TARGET_WORDS = 400
MAX_WORDS = 500
OVERLAP_WORDS = 40

_HEADING_RE = re.compile(r"^#{1,6}\s", re.MULTILINE)


def _split_into_sections(text: str) -> list[str]:
    """Splits on Markdown headings, keeping each heading with its body."""
    positions = [m.start() for m in _HEADING_RE.finditer(text)]
    if not positions:
        return [text]
    positions.append(len(text))
    return [text[positions[i] : positions[i + 1]].strip() for i in range(len(positions) - 1)]


def _split_section_into_chunks(section: str) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", section) if p.strip()]
    chunks: list[str] = []
    current: list[str] = []
    current_words = 0

    for paragraph in paragraphs:
        paragraph_words = len(paragraph.split())
        if current and current_words + paragraph_words > MAX_WORDS:
            chunks.append("\n\n".join(current))
            overlap_text = " ".join(" ".join(current).split()[-OVERLAP_WORDS:])
            current = [overlap_text] if overlap_text else []
            current_words = len(overlap_text.split())
        current.append(paragraph)
        current_words += paragraph_words
        if current_words >= TARGET_WORDS:
            chunks.append("\n\n".join(current))
            current = []
            current_words = 0

    if current:
        chunks.append("\n\n".join(current))
    return chunks


def chunk_markdown(text: str) -> list[str]:
    """Returns non-empty chunk strings for the given Markdown text."""
    if not text or not text.strip():
        return []
    chunks = []
    for section in _split_into_sections(text):
        chunks.extend(_split_section_into_chunks(section))
    return [c for c in chunks if c.strip()]
