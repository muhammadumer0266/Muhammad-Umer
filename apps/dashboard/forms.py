from django import forms
from django.db import models

from apps.ai.models import GuardrailPolicy
from apps.portfolio.models import Entry, Profile, Resume


class ListField(forms.CharField):
    """A JSON list edited as one item per line (or comma-separated)."""

    def __init__(self, *args, separator: str = "\n", **kwargs) -> None:
        self.separator = separator
        kwargs.setdefault("required", False)
        rows = 4 if separator == "\n" else 1
        kwargs.setdefault(
            "widget",
            forms.Textarea(attrs={"rows": rows}) if separator == "\n" else forms.TextInput(),
        )
        super().__init__(*args, **kwargs)

    def prepare_value(self, value):
        if isinstance(value, list | tuple):
            joiner = "\n" if self.separator == "\n" else ", "
            return joiner.join(str(v) for v in value)
        return value

    def to_python(self, value) -> list[str]:
        value = super().to_python(value) or ""
        parts = value.splitlines() if self.separator == "\n" else value.split(self.separator)
        return [p.strip() for p in parts if p.strip()]


def dashboard_formfield(field: models.Field, **kwargs):
    """Consistent widgets for every model form in the dashboard."""
    if isinstance(field, models.DateField):
        kwargs["widget"] = forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")
    elif isinstance(field, models.ManyToManyField):
        kwargs["widget"] = forms.CheckboxSelectMultiple
    elif isinstance(field, models.TextField):
        kwargs["widget"] = forms.Textarea(attrs={"rows": 14, "class": "is-markdown"})
    elif isinstance(field, models.URLField):
        kwargs["assume_scheme"] = "https"
    return field.formfield(**kwargs)


class DashboardModelForm(forms.ModelForm):
    formfield_callback = dashboard_formfield


class ProfileForm(DashboardModelForm):
    alternate_names = ListField(
        separator=",",
        help_text="Other names people search for you by, comma-separated (e.g. Umer).",
    )

    class Meta:
        model = Profile
        fields = [
            "full_name",
            "alternate_names",
            "headline",
            "bio_short",
            "bio_md",
            "photo",
            "location_display",
            "available_for_work",
            "public_email_visible",
        ]
        labels = {
            "headline": "Title / headline",
            "bio_short": "Summary (also the Google snippet)",
            "bio_md": "Long bio (Markdown)",
            "location_display": "Location",
            "public_email_visible": "Show my email on the contact page",
        }
        help_texts = {
            "headline": "Shown under your name, in the browser tab and in search results.",
            "bio_short": "One or two sentences, max 300 characters.",
        }


class EntryForm(DashboardModelForm):
    metrics = ListField(help_text="One result per line, e.g. '40% faster imports'.")

    class Meta:
        model = Entry
        fields = [
            "title",
            "slug",
            "kind",
            "status",
            "date",
            "summary",
            "body_md",
            "tags",
            "metrics",
            "live_url",
            "repo_url",
            "writeup_url",
            "cover_image",
            "featured",
            "is_published",
            "is_sample",
            "seo_title",
            "seo_description",
        ]
        labels = {"body_md": "Case study (Markdown)", "is_sample": "Sample / placeholder"}
        widgets = {"summary": forms.Textarea(attrs={"rows": 3})}


class GuardrailPolicyForm(DashboardModelForm):
    class Meta:
        model = GuardrailPolicy
        fields = [
            "enabled",
            "disabled_message",
            "rate_limit_per_hour",
            "min_question_length",
            "max_question_length",
            "similarity_threshold",
            "top_k",
            "require_citations",
            "redact_pii",
            "max_answer_chars",
            "refusal_message",
            "no_answer_message",
        ]


class ResumeForm(DashboardModelForm):
    class Meta:
        model = Resume
        fields = ["label", "file", "is_active"]
        # Private storage has no public URL, so the default "Currently: <link>"
        # widget can't render; the template links to the owner-only preview.
        widgets = {"file": forms.FileInput(attrs={"accept": "application/pdf"})}
        labels = {"is_active": "Make this the active résumé"}
