import factory
from factory.django import DjangoModelFactory

from apps.portfolio.models import Entry, SkillGroup, SocialLink, Tag


class TagFactory(DjangoModelFactory):
    class Meta:
        model = Tag
        django_get_or_create = ("slug",)

    name = factory.Sequence(lambda n: f"Tag {n}")
    slug = factory.Sequence(lambda n: f"tag-{n}")


class EntryFactory(DjangoModelFactory):
    class Meta:
        model = Entry
        skip_postgeneration_save = True

    slug = factory.Sequence(lambda n: f"entry-{n}")
    title = factory.Sequence(lambda n: f"Sample entry {n}")
    kind = Entry.Kind.PROJECT
    status = Entry.Status.SHIPPED
    date = factory.Faker("date_object")
    summary = factory.Faker("sentence")
    is_published = True
    is_sample = True

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.tags.set(extracted)


class SocialLinkFactory(DjangoModelFactory):
    class Meta:
        model = SocialLink

    platform = SocialLink.Platform.GITHUB
    url = "https://github.com/muhammadumer0266"


class SkillGroupFactory(DjangoModelFactory):
    class Meta:
        model = SkillGroup
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Group {n}")
