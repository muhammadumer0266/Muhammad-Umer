import datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.portfolio.models import Profile, Skill
from apps.portfolio.tests.factories import EntryFactory, SkillGroupFactory


@pytest.mark.django_db
def test_profile_is_a_pinned_singleton():
    first = Profile.get_solo()
    second = Profile.get_solo()

    assert first.pk == second.pk == 1


@pytest.mark.django_db
def test_profile_cannot_be_deleted():
    profile = Profile.get_solo()

    with pytest.raises(ValidationError):
        profile.delete()


@pytest.mark.django_db
def test_entry_clean_normalizes_date_to_first_of_month():
    entry = EntryFactory.build(date=datetime.date(2026, 9, 15))

    entry.clean()

    assert entry.date == datetime.date(2026, 9, 1)


@pytest.mark.django_db
def test_entry_has_case_study_requires_project_kind_and_body():
    project_with_body = EntryFactory(kind="project", body_md="# Case study")
    project_without_body = EntryFactory(kind="project", body_md="")
    milestone_with_body = EntryFactory(kind="milestone", body_md="# Notes")

    assert project_with_body.has_case_study is True
    assert project_without_body.has_case_study is False
    assert milestone_with_body.has_case_study is False


@pytest.mark.django_db
def test_skill_unique_per_group():
    group = SkillGroupFactory()
    Skill.objects.create(group=group, name="Django")

    with pytest.raises(IntegrityError):
        Skill.objects.create(group=group, name="Django")
