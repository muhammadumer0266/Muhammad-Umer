import pytest

from apps.portfolio.models import Profile, SocialLink
from apps.seo.jsonld import build_person, build_profile_page, build_website


@pytest.mark.django_db
def test_build_person_minimal_profile():
    profile = Profile.get_solo()

    data = build_person(profile)

    assert data["@type"] == "Person"
    assert data["name"] == "Muhammad Umer"
    assert "alternateName" not in data
    assert "description" not in data
    assert "image" not in data
    assert "sameAs" not in data
    assert "email" not in data


@pytest.mark.django_db
def test_build_person_includes_optional_fields_when_present(settings):
    settings.CONTACT_EMAIL = "muhammadumer0266@gmail.com"
    profile = Profile.get_solo()
    profile.alternate_names = ["Umer"]
    profile.bio_short = "Django developer and AI engineer."
    profile.public_email_visible = True
    profile.save()
    rel_me_link = SocialLink.objects.create(
        platform=SocialLink.Platform.GITHUB, url="https://github.com/muhammadumer0266", rel_me=True
    )
    SocialLink.objects.create(
        platform=SocialLink.Platform.OTHER, url="https://example.com/no-rel", rel_me=False
    )

    data = build_person(profile, SocialLink.objects.all())

    assert data["alternateName"] == ["Umer"]
    assert data["description"] == "Django developer and AI engineer."
    assert data["sameAs"] == [rel_me_link.url]
    assert data["email"] == "muhammadumer0266@gmail.com"


@pytest.mark.django_db
def test_build_website_publisher_references_person_id():
    website = build_website()

    assert website["@type"] == "WebSite"
    assert website["publisher"]["@id"].endswith("#person")


@pytest.mark.django_db
def test_build_profile_page_references_person_as_main_entity():
    profile = Profile.get_solo()

    page = build_profile_page(profile)

    assert page["@type"] == "ProfilePage"
    assert page["mainEntity"]["@id"].endswith("#person")
