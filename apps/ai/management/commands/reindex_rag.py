import hashlib
from typing import Any

from django.core.management.base import BaseCommand
from django.urls import reverse

from apps.ai.chunking import chunk_markdown
from apps.ai.models import RagChunk, RagDocument
from apps.ai.providers import get_provider
from apps.portfolio.models import Entry, Profile


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


class Command(BaseCommand):
    help = "Rebuild the RAG index from published entries and the profile bio."

    def handle(self, *args: Any, **options: Any) -> None:
        provider = get_provider()
        sources = self._collect_sources()

        created_docs = 0
        skipped_docs = 0
        total_chunks = 0

        for source_type, source_id, title, url, text in sources:
            content_hash = _content_hash(text)
            document, created = RagDocument.objects.get_or_create(
                source_type=source_type,
                source_id=source_id,
                defaults={"title": title, "url": url, "content_hash": content_hash},
            )
            if not created and document.content_hash == content_hash:
                skipped_docs += 1
                continue

            document.title = title
            document.url = url
            document.content_hash = content_hash
            document.save()
            document.chunks.all().delete()

            chunk_texts = chunk_markdown(text)
            if chunk_texts:
                embeddings = provider.embed(chunk_texts)
                RagChunk.objects.bulk_create(
                    RagChunk(
                        document=document,
                        text=chunk_text,
                        token_count=len(chunk_text.split()),
                        embedding=embedding,
                    )
                    for chunk_text, embedding in zip(chunk_texts, embeddings, strict=True)
                )
            total_chunks += len(chunk_texts)
            created_docs += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Indexed {created_docs} document(s) ({total_chunks} chunks), "
                f"skipped {skipped_docs} unchanged."
            )
        )

    def _collect_sources(self) -> list[tuple[str, str, str, str, str]]:
        sources: list[tuple[str, str, str, str, str]] = []

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
        return sources
