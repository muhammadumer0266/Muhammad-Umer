"""Shared Markdown-to-safe-HTML rendering, used by admin previews and public templates.

Renders with markdown-it-py, then sanitizes the output through an allowlist
(nh3) so user-authored Markdown can never inject scripts or unexpected
attributes, regardless of who wrote it.
"""

import re

import nh3
from django.utils.safestring import SafeString, mark_safe
from markdown_it import MarkdownIt

_md = MarkdownIt("commonmark", {"typographer": True}).enable(["table", "strikethrough"])

_ALLOWED_TAGS = {
    "p",
    "br",
    "hr",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "strong",
    "em",
    "blockquote",
    "code",
    "pre",
    "ul",
    "ol",
    "li",
    "a",
    "img",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
}
_ALLOWED_ATTRIBUTES = {
    "a": {"href", "title"},
    "img": {"src", "alt", "width", "height"},
}


def _demote_headings(html: str) -> str:
    """Shift h1-h5 down one level (h1->h2, ..., h5->h6).

    Markdown body content is always rendered inside a page that already has
    its own <h1> (the entry/profile title) -- the SEO requirements require
    exactly one h1 per page, so author-written "# Heading" markdown must
    never be allowed to compete with it. Processed highest-level-first so a
    freshly demoted h2 (from an original h1) is never re-matched as if it
    were an original h2.
    """
    for level in range(5, 0, -1):
        new_level = level + 1
        html = re.sub(rf"<h{level}(\b[^>]*)>", rf"<h{new_level}\1>", html)
        html = html.replace(f"</h{level}>", f"</h{new_level}>")
    return html


def render_markdown(text: str) -> SafeString:
    html = _md.render(text or "")
    clean = nh3.clean(
        html,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        link_rel="noopener noreferrer",
    )
    demoted = _demote_headings(clean)
    # demoted is nh3-sanitized against an explicit tag/attribute allowlist above.
    return mark_safe(demoted)  # noqa: S308 # nosec B308 B703
