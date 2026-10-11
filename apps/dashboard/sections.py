"""Everything the dashboard can manage, declared once.

Each Section drives the shared list/create/edit/delete views in views.py:
which model, which form fields, which columns in the table, what's
searchable. Adding a new manageable model is one entry here.
"""

from dataclasses import dataclass, field
from typing import Any

from django.db import models

from apps.ai.models import AskLog, GuardrailRule
from apps.contact.models import ContactMessage
from apps.portfolio.models import (
    Certification,
    Entry,
    Photo,
    Resume,
    ResumeRequest,
    Skill,
    SkillGroup,
    SocialLink,
    Tag,
)

from .forms import DashboardModelForm, EntryForm, ResumeForm


@dataclass(frozen=True)
class Column:
    label: str
    attr: str
    kind: str = "text"  # text | bool | image | date | datetime | badge


@dataclass(frozen=True)
class Section:
    slug: str
    label: str
    singular: str
    model: type[models.Model]
    group: str
    icon: str
    columns: tuple[Column, ...]
    fields: tuple[str, ...] = ()
    form_class: type[DashboardModelForm] | None = None
    search: tuple[str, ...] = ()
    description: str = ""
    can_add: bool = True
    can_edit: bool = True
    can_delete: bool = True
    detail_url: str = ""  # named URL used instead of the generic edit view
    select_related: tuple[str, ...] = ()
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def read_only(self) -> bool:
        return not (self.can_add or self.can_edit)


SECTIONS: tuple[Section, ...] = (
    # --- Content ---
    Section(
        slug="work",
        label="Work",
        singular="project",
        model=Entry,
        group="Content",
        icon="briefcase",
        form_class=EntryForm,
        columns=(
            Column("Title", "title"),
            Column("Kind", "get_kind_display", "badge"),
            Column("Date", "date", "date"),
            Column("Featured", "featured", "bool"),
            Column("Published", "is_published", "bool"),
        ),
        search=("title", "summary", "slug"),
        description="Projects, milestones and learning. Case studies are written in Markdown.",
    ),
    Section(
        slug="certifications",
        label="Certifications",
        singular="certification",
        model=Certification,
        group="Content",
        icon="award",
        fields=(
            "title",
            "issuer",
            "description",
            "issue_date",
            "expiry_date",
            "credential_id",
            "credential_url",
            "tags",
            "badge_image",
            "certificate_file",
            "is_published",
            "order",
        ),
        columns=(
            Column("Badge", "badge_image", "image"),
            Column("Title", "title"),
            Column("Issuer", "issuer"),
            Column("Issued", "issue_date", "date"),
            Column("Published", "is_published", "bool"),
        ),
        search=("title", "issuer", "credential_id"),
        description="Upload a badge and/or the certificate (PDF or image).",
    ),
    Section(
        slug="photos",
        label="Photos",
        singular="photo",
        model=Photo,
        group="Content",
        icon="image",
        fields=(
            "image",
            "title",
            "alt_text",
            "caption",
            "taken_on",
            "location",
            "is_published",
            "show_on_home",
            "order",
        ),
        columns=(
            Column("Photo", "image", "image"),
            Column("Title", "title"),
            Column("Taken", "taken_on", "date"),
            Column("On home", "show_on_home", "bool"),
            Column("Published", "is_published", "bool"),
        ),
        search=("title", "alt_text", "caption", "location"),
        description=(
            "Photos for /photos/ and Google Images. Describe each one in the alt text, "
            "including your name."
        ),
    ),
    Section(
        slug="skill-groups",
        label="Skill groups",
        singular="skill group",
        model=SkillGroup,
        group="Content",
        icon="layers",
        fields=("name", "order"),
        columns=(Column("Name", "name"), Column("Order", "order")),
        search=("name",),
        description="Toolbox headings on the About page (e.g. Backend, AI).",
    ),
    Section(
        slug="skills",
        label="Skills",
        singular="skill",
        model=Skill,
        group="Content",
        icon="spark",
        fields=("group", "name", "order"),
        columns=(Column("Skill", "name"), Column("Group", "group"), Column("Order", "order")),
        search=("name", "group__name"),
        select_related=("group",),
    ),
    Section(
        slug="tags",
        label="Tags",
        singular="tag",
        model=Tag,
        group="Content",
        icon="tag",
        fields=("name", "slug"),
        columns=(Column("Name", "name"), Column("Slug", "slug")),
        search=("name", "slug"),
    ),
    Section(
        slug="social-links",
        label="Social links",
        singular="social link",
        model=SocialLink,
        group="Content",
        icon="link",
        fields=("platform", "url", "rel_me", "order"),
        columns=(
            Column("Platform", "get_platform_display", "badge"),
            Column("URL", "url"),
            Column("rel=me", "rel_me", "bool"),
        ),
        search=("url",),
        description="Tick rel=me on your own profiles: it links them to you for search engines.",
    ),
    # --- Résumé ---
    Section(
        slug="resumes",
        label="Résumés",
        singular="résumé",
        model=Resume,
        group="Résumé",
        icon="file",
        form_class=ResumeForm,
        columns=(
            Column("Label", "label"),
            Column("Active", "is_active", "bool"),
            Column("Downloads", "download_count"),
            Column("Uploaded", "created_at", "datetime"),
        ),
        search=("label",),
        description=(
            "PDF only. The active résumé is what visitors download after entering their "
            "email. Files are private: never reachable by a public URL."
        ),
    ),
    Section(
        slug="resume-requests",
        label="Download requests",
        singular="download request",
        model=ResumeRequest,
        group="Résumé",
        icon="mail",
        columns=(
            Column("Email", "email"),
            Column("Résumé", "resume"),
            Column("Downloaded", "downloaded", "bool"),
            Column("When", "created_at", "datetime"),
        ),
        search=("email",),
        can_add=False,
        can_edit=False,
        select_related=("resume",),
        description="Everyone who entered their email to download your résumé.",
        extra={"export": "dashboard:resume_requests_csv"},
    ),
    # --- Inbox ---
    Section(
        slug="messages",
        label="Messages",
        singular="message",
        model=ContactMessage,
        group="Inbox",
        icon="inbox",
        columns=(
            Column("From", "name"),
            Column("Email", "email"),
            Column("Status", "get_status_display", "badge"),
            Column("Received", "created_at", "datetime"),
        ),
        search=("name", "email", "message"),
        can_add=False,
        can_edit=False,
        detail_url="dashboard:message_detail",
    ),
    # --- AI ---
    Section(
        slug="guardrail-rules",
        label="Guardrail rules",
        singular="guardrail rule",
        model=GuardrailRule,
        group="Ask AI",
        icon="shield",
        fields=(
            "name",
            "stage",
            "match_type",
            "pattern",
            "action",
            "message",
            "priority",
            "is_active",
        ),
        columns=(
            Column("Name", "name"),
            Column("Stage", "get_stage_display", "badge"),
            Column("Pattern", "pattern"),
            Column("Hits", "hit_count"),
            Column("Active", "is_active", "bool"),
        ),
        search=("name", "pattern"),
        description="Extra block/redact rules on top of the built-in guardrails; applied at once.",
    ),
    Section(
        slug="ask-logs",
        label="Ask logs",
        singular="question",
        model=AskLog,
        group="Ask AI",
        icon="chat",
        columns=(
            Column("Question", "question"),
            Column("Refused", "refused", "bool"),
            Column("Guardrail", "guardrail"),
            Column("When", "created_at", "datetime"),
        ),
        search=("question", "guardrail"),
        can_add=False,
        can_edit=False,
    ),
)

BY_SLUG = {s.slug: s for s in SECTIONS}


def grouped() -> list[tuple[str, list[Section]]]:
    groups: dict[str, list[Section]] = {}
    for section in SECTIONS:
        groups.setdefault(section.group, []).append(section)
    return list(groups.items())
