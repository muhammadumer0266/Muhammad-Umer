from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.portfolio.models import Entry, Tag


class StaticViewSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.8

    def items(self) -> list[str]:
        return [
            "portfolio:home",
            "portfolio:work_list",
            "portfolio:about",
            "contact:contact",
            "core:privacy",
        ]

    def location(self, item: str) -> str:
        return reverse(item)


class EntrySitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return (
            Entry.objects.filter(is_published=True, is_sample=False, kind=Entry.Kind.PROJECT)
            .exclude(body_md="")
            .order_by("slug")
        )

    def lastmod(self, obj: Entry):
        return obj.updated_at

    def location(self, obj: Entry) -> str:
        return reverse("portfolio:entry_detail", args=[obj.slug])


class TagSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.4

    def items(self):
        # Only tags with 2+ published, non-sample entries are indexable
        # landing pages.
        return [
            tag
            for tag in Tag.objects.order_by("slug")
            if tag.entries.filter(is_published=True, is_sample=False).count() >= 2
        ]

    def location(self, obj: Tag) -> str:
        return reverse("portfolio:tag_detail", args=[obj.slug])
