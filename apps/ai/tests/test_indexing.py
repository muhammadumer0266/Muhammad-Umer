from datetime import date

import pytest

from apps.ai.indexing import reindex
from apps.ai.models import RagDocument
from apps.ai.services import ask
from apps.portfolio.models import Certification
from apps.portfolio.tests.factories import EntryFactory


@pytest.mark.django_db
def test_published_certification_is_indexed_and_answerable():
    Certification.objects.create(
        title="Certified Kubernetes Administrator",
        issuer="CNCF",
        issue_date=date(2025, 6, 1),
    )

    reindex()
    result = ask("Which Kubernetes certification does he hold?")

    assert RagDocument.objects.filter(source_type="certification").count() == 1
    assert result.refused is False
    assert "Kubernetes" in result.answer


@pytest.mark.django_db
def test_unpublished_content_is_removed_from_index():
    entry = EntryFactory(is_sample=False, body_md="Hidden project about llamas.")
    reindex()
    assert RagDocument.objects.filter(source_id=str(entry.pk)).exists()

    entry.is_published = False
    entry.save()
    stats = reindex()

    assert stats.removed == 1
    assert not RagDocument.objects.filter(source_id=str(entry.pk)).exists()
    assert ask("Tell me about the llamas project").refused is True


@pytest.mark.django_db
def test_content_save_schedules_reindex_after_commit(django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        Certification.objects.create(title="Auto Cert", issuer="Org", issue_date=date(2025, 1, 1))

    assert RagDocument.objects.filter(title__contains="Auto Cert").exists()


@pytest.mark.django_db
def test_auto_reindex_can_be_disabled(settings, django_capture_on_commit_callbacks):
    settings.AI_AUTO_REINDEX = False

    with django_capture_on_commit_callbacks(execute=True) as callbacks:
        Certification.objects.create(title="Quiet", issuer="Org", issue_date=date(2025, 1, 1))

    assert callbacks == []
