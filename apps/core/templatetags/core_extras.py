from django import template
from django.utils.safestring import SafeString

from apps.core.markdown import render_markdown

register = template.Library()


@register.filter(name="markdown", is_safe=True)
def markdown_filter(text: str) -> SafeString:
    return render_markdown(text)


@register.filter(name="initials")
def initials_filter(name: str) -> str:
    """'Muhammad Umer' -> 'MU'. At most two letters, for the header monogram."""
    words = [w for w in (name or "").split() if w[:1].isalpha()]
    if not words:
        return ""
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[-1][0]).upper()
