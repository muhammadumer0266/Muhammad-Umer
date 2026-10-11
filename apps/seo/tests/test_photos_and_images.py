import io
import json
import re

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from apps.portfolio.models import Photo, Profile


def _jpeg(name: str = "IMG_0001.JPG") -> SimpleUploadedFile:
    buffer = io.BytesIO()
    Image.new("RGB", (1200, 1500), "white").save(buffer, format="JPEG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/jpeg")


@pytest.fixture
def media_root(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    return tmp_path


@pytest.fixture
def photo(media_root):
    return Photo.objects.create(
        title="Speaking at PyCon",
        alt_text="Muhammad Umer presenting a Django talk on stage",
        caption="Talk on retrieval-augmented Django apps",
        image=_jpeg(),
    )


def _jsonld(html: str) -> list[dict]:
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    return [json.loads(b) for b in blocks]


@pytest.mark.django_db
def test_photo_filename_is_descriptive_not_camera_default(photo):
    name = photo.image.name

    assert name.startswith("photos/muhammad-umer-speaking-at-pycon-")
    assert name.endswith(".jpg")
    assert "IMG_0001" not in name
    assert (photo.width, photo.height) == (1200, 1500)


@pytest.mark.django_db
def test_photos_page_has_alt_text_and_image_jsonld(client, photo, settings):

    html = client.get(reverse("portfolio:photos")).content.decode()

    assert 'alt="Muhammad Umer presenting a Django talk on stage"' in html
    gallery = next(b for b in _jsonld(html) if b.get("@type") == "ImageGallery")
    image = gallery["image"][0]
    assert image["contentUrl"].startswith("http://testserver/media/photos/")
    assert image["creator"]["@id"] == "http://testserver/#person"
    assert image["width"] == 1200
    assert f'og:image" content="{image["contentUrl"]}"' in html


@pytest.mark.django_db
def test_photos_nav_and_sitemap_appear_once_published(client, photo):
    assert b'href="/photos/"' in client.get(reverse("portfolio:home")).content
    assert b"/photos/</loc>" in client.get("/sitemap.xml").content


@pytest.mark.django_db
def test_unpublished_photo_is_hidden_everywhere(client, photo):
    photo.is_published = False
    photo.save()

    assert b'href="/photos/"' not in client.get(reverse("portfolio:home")).content
    assert photo.image.name.encode() not in client.get("/sitemap-images.xml").content
    assert b"noindex" in client.get(reverse("portfolio:photos")).content


@pytest.mark.django_db
def test_image_sitemap_lists_profile_and_gallery_photos(client, photo, settings):
    profile = Profile.get_solo()
    profile.photo = _jpeg("me.png")
    profile.save()

    xml = client.get("/sitemap-images.xml").content.decode()

    assert 'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"' in xml
    assert "<loc>http://testserver/photos/</loc>" in xml
    assert f"http://testserver/media/{photo.image.name}" in xml
    assert "http://testserver/media/profile/muhammad-umer-" in xml


@pytest.mark.django_db
def test_robots_txt_lists_image_sitemap(client, settings):

    body = client.get("/robots.txt").content.decode()

    assert "Sitemap: http://testserver/sitemap-images.xml" in body


@pytest.mark.django_db
def test_profile_photo_drives_og_tags_person_image_and_home_portrait(client, media_root, settings):
    profile = Profile.get_solo()
    profile.photo = _jpeg("headshot.jpg")
    profile.save()

    html = client.get(reverse("portfolio:home")).content.decode()
    absolute = f"http://testserver/media/{profile.photo.name}"

    assert f'<meta property="og:image" content="{absolute}">' in html
    assert 'name="twitter:card" content="summary_large_image"' in html
    assert 'class="hero__portrait"' in html
    person = next(b for b in _jsonld(html) if b.get("@type") == "Person")
    assert person["image"]["contentUrl"] == absolute


@pytest.mark.django_db
def test_og_title_and_description_match_page(client):
    html = client.get(reverse("portfolio:about")).content.decode()
    title = re.search(r"<title>(.*?)</title>", html).group(1)

    assert f'<meta property="og:title" content="{title}">' in html
    assert '<meta property="og:url" content="http://testserver/about/">' in html
