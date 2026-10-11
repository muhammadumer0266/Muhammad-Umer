from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.db import models, transaction

from apps.core.models import TimeStampedModel
from apps.core.uploads import (
    RandomFilename,
    SeoFilename,
    image_or_pdf_validators,
    image_validators,
    pdf_validators,
)


class Profile(TimeStampedModel):
    """Singleton profile. Always fetch/save via get_solo(); pk is pinned to 1."""

    full_name = models.CharField(max_length=200, default="Muhammad Umer")
    alternate_names = models.JSONField(default=list, blank=True)
    headline = models.CharField(max_length=200, blank=True)
    bio_short = models.CharField(max_length=300, blank=True)
    bio_md = models.TextField(blank=True)
    photo = models.ImageField(
        upload_to=SeoFilename("profile"),
        validators=image_validators,
        blank=True,
        null=True,
        help_text=(
            "A clear, well-lit headshot (square, at least 800x800). Used on the site, in "
            "link previews and in search results -- use the same photo as on LinkedIn/GitHub."
        ),
    )
    available_for_work = models.BooleanField(default=False)
    public_email_visible = models.BooleanField(default=False)
    location_display = models.CharField(max_length=120, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(pk=1), name="portfolio_profile_singleton")
        ]

    def __str__(self) -> str:
        return self.full_name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("The singleton Profile cannot be deleted.")

    @classmethod
    def get_solo(cls) -> "Profile":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class SocialLink(TimeStampedModel):
    class Platform(models.TextChoices):
        GITHUB = "github", "GitHub"
        LINKEDIN = "linkedin", "LinkedIn"
        STACKOVERFLOW = "stackoverflow", "Stack Overflow"
        DEVTO = "devto", "dev.to"
        HASHNODE = "hashnode", "Hashnode"
        PYPI = "pypi", "PyPI"
        CRATESIO = "cratesio", "crates.io"
        X = "x", "X"
        YOUTUBE = "youtube", "YouTube"
        OTHER = "other", "Other"

    platform = models.CharField(max_length=20, choices=Platform.choices)
    url = models.URLField()
    rel_me = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "platform"]

    def __str__(self) -> str:
        return f"{self.get_platform_display()}: {self.url}"


class Tag(TimeStampedModel):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=60, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Entry(TimeStampedModel):
    class Kind(models.TextChoices):
        PROJECT = "project", "Project"
        MILESTONE = "milestone", "Milestone"
        LEARNING = "learning", "Learning"

    class Status(models.TextChoices):
        SHIPPED = "shipped", "Shipped"
        BUILDING = "building", "Building"
        ARCHIVED = "archived", "Archived"

    slug = models.SlugField(max_length=200, unique=True)
    title = models.CharField(max_length=200)
    kind = models.CharField(max_length=20, choices=Kind.choices)
    status = models.CharField(max_length=20, choices=Status.choices, blank=True)
    date = models.DateField(help_text="Stored at month precision (first of the month).")
    summary = models.CharField(max_length=600)
    body_md = models.TextField(blank=True)
    tags = models.ManyToManyField(Tag, related_name="entries", blank=True)
    metrics = models.JSONField(default=list, blank=True)
    live_url = models.URLField(blank=True)
    repo_url = models.URLField(blank=True)
    writeup_url = models.URLField(blank=True)
    featured = models.BooleanField(default=False)
    cover_image = models.ImageField(
        upload_to=RandomFilename("entries"), validators=image_validators, blank=True, null=True
    )
    is_published = models.BooleanField(default=False)
    is_sample = models.BooleanField(
        default=False,
        help_text="Sample/placeholder content. Excluded from sitemaps, JSON-LD and search.",
    )
    seo_title = models.CharField(max_length=60, blank=True)
    seo_description = models.CharField(max_length=160, blank=True)

    class Meta:
        ordering = ["-date", "title"]
        verbose_name_plural = "entries"
        indexes = [models.Index(fields=["kind", "is_published"])]

    def __str__(self) -> str:
        return self.title

    def clean(self) -> None:
        self.date = self.date.replace(day=1)

    @property
    def has_case_study(self) -> bool:
        return self.kind == self.Kind.PROJECT and bool(self.body_md)


class SkillGroup(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self) -> str:
        return self.name


class Skill(TimeStampedModel):
    group = models.ForeignKey(SkillGroup, on_delete=models.CASCADE, related_name="skills")
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        constraints = [
            models.UniqueConstraint(fields=["group", "name"], name="unique_skill_per_group")
        ]

    def __str__(self) -> str:
        return f"{self.group.name} / {self.name}"


class Certification(TimeStampedModel):
    """A certificate or credential, managed entirely from the admin.

    Upload a badge image and/or the certificate itself (PDF or image), tick
    "published", and it appears on /certifications/, the About page, the
    public API and (after the automatic RAG reindex) in Ask answers.
    """

    title = models.CharField(max_length=200)
    issuer = models.CharField(max_length=200)
    issue_date = models.DateField(help_text="Stored at month precision (first of the month).")
    expiry_date = models.DateField(
        blank=True, null=True, help_text="Leave empty if it doesn't expire."
    )
    credential_id = models.CharField(max_length=200, blank=True)
    credential_url = models.URLField(
        blank=True, help_text="Public verification link from the issuer, if any."
    )
    description = models.CharField(max_length=500, blank=True)
    tags = models.ManyToManyField(Tag, related_name="certifications", blank=True)
    badge_image = models.ImageField(
        upload_to=RandomFilename("certifications/badges"),
        validators=image_validators,
        blank=True,
        null=True,
        help_text="JPG/PNG/WebP, max 5 MB. Shown on the card.",
    )
    certificate_file = models.FileField(
        upload_to=RandomFilename("certifications/files"),
        validators=image_or_pdf_validators,
        blank=True,
        null=True,
        help_text="The certificate itself: PDF (max 10 MB) or JPG/PNG/WebP (max 5 MB).",
    )
    is_published = models.BooleanField(default=True)
    order = models.PositiveIntegerField(
        default=0, help_text="Lower numbers show first; ties are newest first."
    )

    class Meta:
        ordering = ["order", "-issue_date", "title"]
        indexes = [models.Index(fields=["is_published", "order"])]

    def __str__(self) -> str:
        return f"{self.title} ({self.issuer})"

    def clean(self) -> None:
        if self.issue_date:
            self.issue_date = self.issue_date.replace(day=1)
        if self.expiry_date and self.issue_date and self.expiry_date < self.issue_date:
            raise ValidationError({"expiry_date": "Expiry date can't be before the issue date."})

    @property
    def is_expired(self) -> bool:
        from django.utils import timezone

        return bool(self.expiry_date and self.expiry_date < timezone.localdate())

    @property
    def certificate_is_pdf(self) -> bool:
        return bool(self.certificate_file) and self.certificate_file.name.lower().endswith(".pdf")


class Photo(TimeStampedModel):
    """A photo of the owner, shown on /photos/ and submitted to image search.

    Upload from the admin; title + alt text drive the file name, alt
    attribute, structured data and image sitemap entry, so describe what's
    actually in the picture.
    """

    title = models.CharField(
        max_length=120, help_text="Short title, e.g. 'Speaking at PyCon Pakistan 2025'."
    )
    alt_text = models.CharField(
        max_length=200,
        help_text=(
            "What the photo shows, for screen readers and image search, e.g. "
            "'Muhammad Umer presenting a Django talk on stage'."
        ),
    )
    caption = models.CharField(max_length=300, blank=True)
    image = models.ImageField(
        upload_to=SeoFilename("photos", title_field="title"),
        validators=image_validators,
        width_field="width",
        height_field="height",
        help_text="JPG/PNG/WebP, max 5 MB. At least 1200px wide works best for search.",
    )
    width = models.PositiveIntegerField(default=0, editable=False)
    height = models.PositiveIntegerField(default=0, editable=False)
    taken_on = models.DateField(blank=True, null=True)
    location = models.CharField(max_length=120, blank=True)
    is_published = models.BooleanField(default=True)
    show_on_home = models.BooleanField(
        default=False, help_text="Also show in the home page photo strip (first 4)."
    )
    order = models.PositiveIntegerField(default=0, help_text="Lower numbers show first.")

    class Meta:
        ordering = ["order", "-taken_on", "-created_at"]
        indexes = [models.Index(fields=["is_published", "order"])]

    def __str__(self) -> str:
        return self.title


class PrivateStorage(FileSystemStorage):
    """Files outside MEDIA_ROOT that have no URL at all.

    A plain FileSystemStorage(base_url=None) silently falls back to
    MEDIA_URL, so .url would still hand out a /media/... address. This one
    refuses, and reads PRIVATE_MEDIA_ROOT on every access instead of caching
    it at import time.
    """

    @property
    def base_location(self):
        return str(settings.PRIVATE_MEDIA_ROOT)

    @property
    def location(self):
        import os

        return os.path.abspath(self.base_location)

    def url(self, name):
        raise ValueError("This file is not accessible via a URL.")


def private_storage() -> PrivateStorage:
    """Callable storage, so migrations don't bake in a machine-specific path."""
    return PrivateStorage()


class Resume(TimeStampedModel):
    """An uploaded resume. Exactly one can be active: the one visitors get."""

    label = models.CharField(
        max_length=120, help_text="For you only, e.g. 'October 2026 - backend roles'."
    )
    file = models.FileField(
        upload_to=RandomFilename("resumes"), storage=private_storage, validators=pdf_validators
    )
    is_active = models.BooleanField(
        default=True, help_text="The active resume is the one visitors download."
    )
    download_count = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        ordering = ["-is_active", "-created_at"]

    def __str__(self) -> str:
        return self.label

    def save(self, *args, **kwargs) -> None:
        with transaction.atomic():
            super().save(*args, **kwargs)
            if self.is_active:
                Resume.objects.exclude(pk=self.pk).filter(is_active=True).update(is_active=False)

    @classmethod
    def active(cls) -> "Resume | None":
        return cls.objects.filter(is_active=True).first()


class ResumeRequest(TimeStampedModel):
    """Someone who entered their email to download the resume."""

    email = models.EmailField()
    resume = models.ForeignKey(
        Resume, on_delete=models.SET_NULL, null=True, blank=True, related_name="requests"
    )
    downloaded = models.BooleanField(default=False)
    ip_hash = models.CharField(max_length=64, blank=True, help_text="Salted hash, never a raw IP.")
    user_agent_hash = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.email} ({self.created_at:%Y-%m-%d})"
