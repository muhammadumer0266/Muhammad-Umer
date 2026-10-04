from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html
from django.utils.safestring import SafeString, mark_safe

from apps.core.markdown import render_markdown

from . import services
from .models import Entry, Profile, Skill, SkillGroup, SocialLink, Tag


class MarkdownPreviewMixin:
    """Adds a read-only rendered-HTML preview of a `body_md`/`bio_md` field."""

    markdown_field = "body_md"

    @admin.display(description="Preview")
    def markdown_preview(self, obj) -> SafeString:
        text = getattr(obj, self.markdown_field, "") or ""
        if not text:
            return mark_safe("<em>Nothing to preview yet.</em>")  # nosec B308
        return format_html('<div class="markdown-preview">{}</div>', render_markdown(text))


class ImagePreviewMixin:
    image_field = "cover_image"

    @admin.display(description="Image")
    def image_preview(self, obj) -> SafeString:
        image = getattr(obj, self.image_field, None)
        if not image:
            return mark_safe("<em>No image</em>")  # nosec B308
        return format_html('<img src="{}" style="max-height:120px" />', image.url)


@admin.register(Profile)
class ProfileAdmin(MarkdownPreviewMixin, ImagePreviewMixin, admin.ModelAdmin):
    markdown_field = "bio_md"
    image_field = "photo"
    readonly_fields = ["markdown_preview", "image_preview"]
    list_display = ["full_name", "headline", "available_for_work", "public_email_visible"]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return not Profile.objects.exists()

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    list_display = ["platform", "url", "rel_me", "order"]
    list_filter = ["platform", "rel_me"]
    search_fields = ["url"]
    ordering = ["order"]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Entry)
class EntryAdmin(MarkdownPreviewMixin, ImagePreviewMixin, admin.ModelAdmin):
    list_display = [
        "title",
        "kind",
        "status",
        "date",
        "featured",
        "is_published",
        "is_sample",
    ]
    list_filter = ["kind", "status", "featured", "is_published", "is_sample", "tags"]
    search_fields = ["title", "slug", "summary"]
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ["tags"]
    readonly_fields = ["markdown_preview", "image_preview", "created_at", "updated_at"]
    date_hierarchy = "date"
    actions = ["publish", "unpublish", "feature", "unfeature"]

    @admin.action(description="Publish selected entries")
    def publish(self, request: HttpRequest, queryset: QuerySet[Entry]) -> None:
        services.publish_entries(list(queryset))

    @admin.action(description="Unpublish selected entries")
    def unpublish(self, request: HttpRequest, queryset: QuerySet[Entry]) -> None:
        services.unpublish_entries(list(queryset))

    @admin.action(description="Feature selected entries")
    def feature(self, request: HttpRequest, queryset: QuerySet[Entry]) -> None:
        services.feature_entries(list(queryset))

    @admin.action(description="Unfeature selected entries")
    def unfeature(self, request: HttpRequest, queryset: QuerySet[Entry]) -> None:
        services.unfeature_entries(list(queryset))


class SkillInline(admin.TabularInline):
    model = Skill
    extra = 1


@admin.register(SkillGroup)
class SkillGroupAdmin(admin.ModelAdmin):
    list_display = ["name", "order"]
    inlines = [SkillInline]
