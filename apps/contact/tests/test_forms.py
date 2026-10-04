import time

from django.core import signing

from apps.contact.forms import MAX_SECONDS_TO_SUBMIT, MIN_SECONDS_TO_SUBMIT, ContactForm

_SALT = "apps.contact.forms.ContactForm.rendered_at"


def _rendered_at(seconds_ago: float) -> str:
    return signing.dumps(time.time() - seconds_ago, salt=_SALT)


def _valid_data(**overrides) -> dict:
    data = {
        "name": "Jane",
        "email": "jane@example.com",
        "message": "Hello",
        "rendered_at": _rendered_at(MIN_SECONDS_TO_SUBMIT + 1),
    }
    data.update(overrides)
    return data


def test_valid_data_passes():
    form = ContactForm(data=_valid_data())

    assert form.is_valid(), form.errors


def test_honeypot_field_filled_is_rejected():
    form = ContactForm(data=_valid_data(website="http://spam.example"))

    assert not form.is_valid()
    assert "website" in form.errors


def test_missing_required_fields_rejected():
    form = ContactForm(data={})

    assert not form.is_valid()
    assert set(form.errors) == {"name", "email", "message", "rendered_at"}


def test_submitting_too_fast_is_rejected_as_spam():
    form = ContactForm(data=_valid_data(rendered_at=_rendered_at(0)))

    assert not form.is_valid()
    assert "rendered_at" in form.errors


def test_tampered_rendered_at_is_rejected():
    form = ContactForm(data=_valid_data(rendered_at="not-a-valid-signature"))

    assert not form.is_valid()
    assert "rendered_at" in form.errors


def test_stale_rendered_at_beyond_max_age_is_rejected():
    form = ContactForm(data=_valid_data(rendered_at=_rendered_at(MAX_SECONDS_TO_SUBMIT + 1)))

    assert not form.is_valid()
    assert "rendered_at" in form.errors
