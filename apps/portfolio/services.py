from .models import Entry
from .signals import content_changed


def publish_entries(entries: list[Entry]) -> int:
    count = Entry.objects.filter(pk__in=[e.pk for e in entries]).update(is_published=True)
    content_changed.send(sender=Entry)
    return count


def unpublish_entries(entries: list[Entry]) -> int:
    count = Entry.objects.filter(pk__in=[e.pk for e in entries]).update(is_published=False)
    content_changed.send(sender=Entry)
    return count


def feature_entries(entries: list[Entry]) -> int:
    return Entry.objects.filter(pk__in=[e.pk for e in entries]).update(featured=True)


def unfeature_entries(entries: list[Entry]) -> int:
    return Entry.objects.filter(pk__in=[e.pk for e in entries]).update(featured=False)
