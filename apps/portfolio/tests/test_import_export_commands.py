import json

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.portfolio.models import Entry


@pytest.fixture
def sample_rows():
    return [
        {
            "slug": "xl-diff",
            "title": "xl-diff",
            "kind": "project",
            "status": "shipped",
            "date": "2026-03-15",
            "summary": "A Rust-backed Excel comparison engine for Python.",
            "tags": ["Rust", "Python"],
            "metrics": ["Sample metric — TODO(owner): real numbers"],
            "live_url": "",
            "repo_url": "https://github.com/muhammadumer0266/xl-diff",
            "writeup_url": "",
            "featured": True,
            "is_sample": True,
        }
    ]


def _write(tmp_path, rows):
    path = tmp_path / "entries.json"
    path.write_text(json.dumps(rows), encoding="utf-8")
    return path


@pytest.mark.django_db
def test_import_entries_creates_rows_and_tags(tmp_path, sample_rows):
    path = _write(tmp_path, sample_rows)

    call_command("import_entries", str(path))

    entry = Entry.objects.get(slug="xl-diff")
    assert entry.date.isoformat() == "2026-03-01"  # normalized to first of month
    assert set(entry.tags.values_list("name", flat=True)) == {"Rust", "Python"}
    assert entry.is_sample is True


@pytest.mark.django_db
def test_import_entries_is_idempotent_and_upserts_by_slug(tmp_path, sample_rows):
    path = _write(tmp_path, sample_rows)
    call_command("import_entries", str(path))

    sample_rows[0]["title"] = "xl-diff (updated)"
    path = _write(tmp_path, sample_rows)
    call_command("import_entries", str(path))

    assert Entry.objects.count() == 1
    assert Entry.objects.get(slug="xl-diff").title == "xl-diff (updated)"


@pytest.mark.django_db
def test_import_entries_rejects_invalid_url(tmp_path, sample_rows):
    sample_rows[0]["repo_url"] = "not-a-url"
    path = _write(tmp_path, sample_rows)

    with pytest.raises(CommandError):
        call_command("import_entries", str(path))


@pytest.mark.django_db
def test_import_entries_rejects_missing_required_field(tmp_path, sample_rows):
    del sample_rows[0]["summary"]
    path = _write(tmp_path, sample_rows)

    with pytest.raises(CommandError):
        call_command("import_entries", str(path))


@pytest.mark.django_db
def test_export_then_import_round_trips(tmp_path, sample_rows):
    import_path = _write(tmp_path, sample_rows)
    call_command("import_entries", str(import_path))

    export_path = tmp_path / "exported.json"
    call_command("export_entries", str(export_path))
    exported = json.loads(export_path.read_text(encoding="utf-8"))

    assert len(exported) == 1
    assert exported[0]["slug"] == "xl-diff"

    Entry.objects.all().delete()
    call_command("import_entries", str(export_path))

    assert Entry.objects.get(slug="xl-diff").title == "xl-diff"
