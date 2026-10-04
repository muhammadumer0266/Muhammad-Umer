from django import template
from django.utils.safestring import SafeString

from apps.core.markdown import render_markdown

register = template.Library()


@register.filter(name="markdown", is_safe=True)
def markdown_filter(text: str) -> SafeString:
    return render_markdown(text)
