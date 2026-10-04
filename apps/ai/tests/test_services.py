from datetime import date

import pytest

from apps.ai.models import AskLog, DailyBudget
from apps.ai.providers.fake import FakeProvider
from apps.ai.services import BUDGET_RESTING_MESSAGE, ask
from apps.ai.tests.factories import RagChunkFactory


@pytest.mark.django_db
def test_ask_answers_when_relevant_chunk_exists():
    provider = FakeProvider()
    (embedding,) = provider.embed(["xl-diff is a Rust-backed Excel comparison engine."])
    RagChunkFactory(text="xl-diff is a Rust-backed Excel comparison engine.", embedding=embedding)

    result = ask("What is xl-diff written in?")

    assert result.refused is False
    assert result.citations


@pytest.mark.django_db
def test_ask_refuses_when_nothing_relevant_is_indexed():
    result = ask("What is the meaning of life?")

    assert result.refused is True
    assert result.citations == []


@pytest.mark.django_db
def test_ask_logs_every_call():
    ask("Anything at all")

    assert AskLog.objects.count() == 1
    log = AskLog.objects.get()
    assert log.question == "Anything at all"
    assert log.refused is True


@pytest.mark.django_db
def test_ask_truncates_overlong_questions_before_logging():
    long_question = "a" * 1000

    ask(long_question)

    log = AskLog.objects.get()
    assert len(log.question) == 300


@pytest.mark.django_db
def test_ask_respects_daily_budget_cap(settings):
    settings.AI_DAILY_BUDGET_USD = 0.01
    DailyBudget.objects.create(date=date.today(), spent_usd=0.02)

    result = ask("What is xl-diff?")

    assert result.refused is True
    assert result.answer == BUDGET_RESTING_MESSAGE


@pytest.mark.django_db
def test_ask_ignores_budget_when_cap_is_zero(settings):
    settings.AI_DAILY_BUDGET_USD = 0
    DailyBudget.objects.create(date=date.today(), spent_usd=999)

    result = ask("What is the meaning of life?")

    # Refused for lack of relevant content, not for budget reasons.
    assert result.answer != BUDGET_RESTING_MESSAGE
