from .models import Entry


def publish_entries(entries: list[Entry]) -> int:
    return Entry.objects.filter(pk__in=[e.pk for e in entries]).update(is_published=True)


def unpublish_entries(entries: list[Entry]) -> int:
    return Entry.objects.filter(pk__in=[e.pk for e in entries]).update(is_published=False)


def feature_entries(entries: list[Entry]) -> int:
    return Entry.objects.filter(pk__in=[e.pk for e in entries]).update(featured=True)


def unfeature_entries(entries: list[Entry]) -> int:
    return Entry.objects.filter(pk__in=[e.pk for e in entries]).update(featured=False)
