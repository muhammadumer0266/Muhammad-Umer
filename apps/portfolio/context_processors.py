from django.db.models import QuerySet
from django.http import HttpRequest

from .models import Profile, SocialLink


def profile_context(request: HttpRequest) -> dict[str, Profile | QuerySet[SocialLink]]:
    """Profile and social links, available to every template (header/footer)."""
    return {
        "profile": Profile.get_solo(),
        "social_links": SocialLink.objects.all(),
    }
