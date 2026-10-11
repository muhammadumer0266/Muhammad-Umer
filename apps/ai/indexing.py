"""Builds the RAG index from published site content.

Sources: the profile bio, published non-sample case studies, and published
certifications. Unchanged documents are skipped by content hash, so a
reindex only pays for embeddings on what actually changed.

Anything no longer published is *removed* from the index -- otherwise an
unpublished entry (or a deleted certification) would stay answerable in Ask.

Runs automatically after content changes (apps/ai/signals.py), and on
demand via `manage.py reindex_rag`.
"""

import hashlib
from dataclasses import dataclass

from django.db import transaction
from django.urls import reverse

from apps.portfolio.models import Certification, Entry, Profile

from .chunking import chunk_markdown
from .models import RagChunk, RagDocument
from .providers import get_provider

Source = tuple[str, str, str, str, str]  # (source_type, source_id, title, url, text)


@dataclass
class IndexStats:
    indexed: int = 0
    skipped: int = 0
    removed: int = 0
    chunks: int = 0


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _certification_text(cert: Certification) -> str:
    lines = [
        f"# {cert.title}",
        f"Certification issued by {cert.issuer} in {cert.issue_date:%B %Y}.",
    ]
    if cert.expiry_date:
        lines.append(f"Valid until {cert.expiry_date:%B %Y}.")
    if cert.description:
        lines.append(cert.description)
    tags = [t.name for t in cert.tags.all()]
    if tags:
        lines.append(f"Skills covered: {', '.join(tags)}.")
    if cert.credential_url:
        lines.append(f"Verifiable at the issuer's site: {cert.credential_url}")
    return "\n\n".join(lines)


def collect_sources() -> list[Source]:
    sources: list[Source] = []

    profile = Profile.get_solo()
    if profile.bio_md:
        sources.append(
            (
                RagDocument.SourceType.PROFILE,
                str(profile.pk),
                profile.full_name,
                reverse("portfolio:about"),
                profile.bio_md,
            )
        )

    entries = Entry.objects.filter(is_published=True, is_sample=False).exclude(body_md="")
    for entry in entries:
        sources.append(
            (
                RagDocument.SourceType.ENTRY,
                str(entry.pk),
                entry.title,
                reverse("portfolio:entry_detail", args=[entry.slug]),
                entry.body_md,
            )
        )

    certifications = Certification.objects.filter(is_published=True).prefetch_related("tags")
    for cert in certifications:
        sources.append(
            (
                RagDocument.SourceType.CERTIFICATION,
                str(cert.pk),
                f"{cert.title} ({cert.issuer})",
                reverse("portfolio:certifications"),
                _certification_text(cert),
            )
        )
    return sources


def reindex() -> IndexStats:
    provider = get_provider()
    sources = collect_sources()
    stats = IndexStats()

    live_keys = {(source_type, source_id) for source_type, source_id, *_ in sources}
    stale = [
        doc.pk
        for doc in RagDocument.objects.only("pk", "source_type", "source_id")
        if (doc.source_type, doc.source_id) not in live_keys
    ]
    if stale:
        RagDocument.objects.filter(pk__in=stale).delete()
        stats.removed = len(stale)

    for source_type, source_id, title, url, text in sources:
        content_hash = _content_hash(text)
        existing = RagDocument.objects.filter(source_type=source_type, source_id=source_id).first()
        if existing and existing.content_hash == content_hash:
            if existing.title != title or existing.url != url:
                existing.title, existing.url = title, url
                existing.save(update_fields=["title", "url", "updated_at"])
            stats.skipped += 1
            continue

        chunk_texts = chunk_markdown(text)
        embeddings = provider.embed(chunk_texts) if chunk_texts else []
        with transaction.atomic():
            document, _ = RagDocument.objects.update_or_create(
                source_type=source_type,
                source_id=source_id,
                defaults={"title": title, "url": url, "content_hash": content_hash},
            )
            document.chunks.all().delete()
            RagChunk.objects.bulk_create(
                RagChunk(
                    document=document,
                    text=chunk_text,
                    token_count=len(chunk_text.split()),
                    embedding=embedding,
                )
                for chunk_text, embedding in zip(chunk_texts, embeddings, strict=True)
            )
        stats.chunks += len(chunk_texts)
        stats.indexed += 1
    return stats
