"""SEO test suite.

Crawls the public pages with the Django test client and checks the things a
search engine or an LLM crawler would notice: title/description length and
uniqueness, a self-referencing absolute canonical, exactly one h1, valid
JSON-LD referencing one consistent Person @id, robots.txt/sitemap hygiene,
and noindex on admin/sample content.
"""

import json
import re

import pytest
from django.test import override_settings
from django.urls import reverse

from apps.portfolio.tests.factories import EntryFactory

PUBLIC_PAGES = [
    "portfolio:home",
    "portfolio:work_list",
    "portfolio:about",
    "contact:contact",
    "core:privacy",
]


def _titles_and_descriptions(client):
    pairs = []
    for name in PUBLIC_PAGES:
        response = client.get(reverse(name))
        html = response.content.decode()
        title = re.search(r"<title>(.*?)</title>", html, re.DOTALL).group(1).strip()
        description = (
            re.search(r'<meta name="description"\s+content="(.*?)">', html, re.DOTALL)
            .group(1)
            .strip()
        )
        pairs.append((name, title, description))
    return pairs


@pytest.mark.django_db
def test_titles_are_reasonable_length_and_unique(client):
    pairs = _titles_and_descriptions(client)
    titles = [t for _, t, _ in pairs]

    for name, title, _ in pairs:
        assert 10 <= len(title) <= 60, f"{name} title is {len(title)} chars: {title!r}"
    assert len(titles) == len(set(titles)), f"duplicate titles: {titles}"


@pytest.mark.django_db
def test_descriptions_are_reasonable_length_and_unique(client):
    pairs = _titles_and_descriptions(client)
    descriptions = [d for _, _, d in pairs]

    for name, _, description in pairs:
        assert 70 <= len(description) <= 160, (
            f"{name} description is {len(description)} chars: {description!r}"
        )
    assert len(descriptions) == len(set(descriptions)), f"duplicate descriptions: {descriptions}"


@pytest.mark.django_db
def test_every_public_page_has_a_self_referencing_absolute_canonical(client):
    for name in PUBLIC_PAGES:
        path = reverse(name)
        response = client.get(path)
        html = response.content.decode()
        match = re.search(r'<link rel="canonical" href="(.*?)">', html)
        assert match, f"{name} has no canonical link"
        canonical = match.group(1)
        assert canonical.startswith("http"), f"{name} canonical is not absolute: {canonical}"
        assert canonical.endswith(path), f"{name} canonical {canonical} doesn't match path {path}"


@pytest.mark.django_db
def test_every_public_page_has_exactly_one_h1(client):
    for name in PUBLIC_PAGES:
        response = client.get(reverse(name))
        count = response.content.count(b"<h1")
        assert count == 1, f"{name} has {count} <h1> tags"


@pytest.mark.django_db
def test_jsonld_blocks_parse_and_share_one_person_id(client):
    response = client.get(reverse("portfolio:home"))
    html = response.content.decode()
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
    assert blocks, "no JSON-LD blocks found on the home page"

    parsed = [json.loads(raw) for raw in blocks]
    types_seen = {block["@type"] for block in parsed}
    person_ids = {block["@id"] for block in parsed if block["@type"] == "Person"}
    website = next(block for block in parsed if block["@type"] == "WebSite")

    assert "Person" in types_seen
    assert "WebSite" in types_seen
    assert len(person_ids) == 1, f"expected one consistent Person @id, got {person_ids}"
    assert website["publisher"]["@id"] in person_ids


@pytest.mark.django_db
def test_jsonld_never_contains_sample_data(client):
    EntryFactory(is_sample=True, is_published=True, title="Totally Fake Sample Entry")

    response = client.get(reverse("portfolio:home"))
    html = response.content.decode()
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)

    assert blocks, "no JSON-LD blocks found"
    assert not any("Totally Fake Sample Entry" in block for block in blocks)


@pytest.mark.django_db
def test_robots_txt_references_sitemap_and_disallows_admin(client, settings):
    response = client.get("/robots.txt")

    assert response.status_code == 200
    body = response.content.decode()
    assert f"Sitemap: {settings.SITE_URL}/sitemap.xml" in body
    assert f"Disallow: /{settings.ADMIN_URL}" in body


@pytest.mark.django_db
def test_sitemap_excludes_sample_and_unpublished_entries(client):
    EntryFactory(
        kind="project", body_md="# x", is_published=True, is_sample=True, slug="sample-one"
    )
    EntryFactory(kind="project", body_md="# x", is_published=False, slug="unpublished-one")
    real = EntryFactory(
        kind="project", body_md="# x", is_published=True, is_sample=False, slug="real-one"
    )

    response = client.get("/sitemap.xml")
    body = response.content.decode()

    assert "sample-one" not in body
    assert "unpublished-one" not in body
    assert real.slug in body


@pytest.mark.django_db
@override_settings(ADMIN_URL="admin-portal/")
def test_admin_paths_carry_noindex_header(client):
    response = client.get("/admin-portal/login/")

    assert response["X-Robots-Tag"] == "noindex"


@pytest.mark.django_db
def test_sample_entry_detail_page_carries_noindex_meta(client):
    entry = EntryFactory(kind="project", body_md="# x", is_published=True, is_sample=True)

    response = client.get(reverse("portfolio:entry_detail", args=[entry.slug]))

    assert b'name="robots" content="noindex"' in response.content


@pytest.mark.django_db
def test_www_and_non_canonical_host_redirect_once(client, settings):
    settings.DEBUG = False
    settings.SITE_URL = "https://muhammadumer.dev"
    settings.ALLOWED_HOSTS = ["muhammadumer.dev", "www.muhammadumer.dev"]

    response = client.get("/healthz/", HTTP_HOST="www.muhammadumer.dev")

    assert response.status_code == 301
    assert response["Location"] == "https://muhammadumer.dev/healthz/"
