from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import TimeStampedModel


class Profile(TimeStampedModel):
    """Singleton profile. Always fetch/save via get_solo(); pk is pinned to 1."""

    full_name = models.CharField(max_length=200, default="Muhammad Umer")
    alternate_names = models.JSONField(default=list, blank=True)
    headline = models.CharField(max_length=200, blank=True)
    bio_short = models.CharField(max_length=300, blank=True)
    bio_md = models.TextField(blank=True)
    photo = models.ImageField(upload_to="profile/", blank=True, null=True)
    resume_pdf = models.FileField(upload_to="resume/", blank=True, null=True)
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
    cover_image = models.ImageField(upload_to="entries/", blank=True, null=True)
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
