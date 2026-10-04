import json
from collections.abc import Iterable

from django import template
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.safestring import SafeString, mark_safe

from apps.portfolio.models import Profile, SocialLink
from apps.seo.jsonld import build_person, build_profile_page, build_website

register = template.Library()


@register.simple_tag
def jsonld_script(data: dict) -> SafeString:
    """Render a dict as a <script type="application/ld+json"> block.

    json.dumps output is HTML-escaped for the </script> and <!-- cases
    (the only injection vectors inside a JSON-LD block) before being marked
    safe; every value here comes from apps.seo.jsonld builders, never raw
    user input.
    """
    payload = json.dumps(data, cls=DjangoJSONEncoder)
    payload = payload.replace("</", "<\\/").replace("<!--", "<\\!--")
    return mark_safe(  # noqa: S308 # nosec B308 B703 -- payload is JSON-escaped above
        f'<script type="application/ld+json">{payload}</script>'
    )


@register.simple_tag
def site_jsonld(profile: Profile, social_links: Iterable[SocialLink] = ()) -> SafeString:
    """Person + WebSite JSON-LD, present on every page.

    Takes the already-fetched `social_links` from the page context instead
    of querying SocialLink itself, to stay within the per-page query budget.
    """
    person_script = jsonld_script(build_person(profile, social_links))
    website_script = jsonld_script(build_website())
    return mark_safe(  # noqa: S308 # nosec B308 B703 -- both parts already escaped
        f"{person_script}\n{website_script}"
    )


@register.simple_tag
def profile_page_jsonld(profile: Profile) -> SafeString:
    return jsonld_script(build_profile_page(profile))
