import time

from django import forms
from django.core import signing

# Below this, a submission is almost certainly a bot filling the form
# instantly rather than a human reading and typing.
MIN_SECONDS_TO_SUBMIT = 2
# Above this, treat the form as stale rather than trust a very old signature.
MAX_SECONDS_TO_SUBMIT = 60 * 60
_SIGNING_SALT = "apps.contact.forms.ContactForm.rendered_at"


class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={"aria-describedby": "name-error"}),
    )
    email = forms.EmailField(widget=forms.EmailInput(attrs={"aria-describedby": "email-error"}))
    message = forms.CharField(
        widget=forms.Textarea(attrs={"aria-describedby": "message-error", "rows": 6}),
        max_length=5000,
    )
    # Honeypot: real visitors never see or fill this field (hidden via CSS,
    # not display:none/hidden so basic bots that skip invisible fields still
    # get caught). Any value here means the submission is discarded as spam.
    website = forms.CharField(required=False, widget=forms.TextInput())
    # Time-trap: a signed render timestamp. Submitting faster than a human
    # could plausibly read and fill the form is treated as spam.
    rendered_at = forms.CharField(
        required=True,
        widget=forms.HiddenInput,
        initial=lambda: signing.dumps(time.time(), salt=_SIGNING_SALT),
    )

    def clean_website(self) -> str:
        value = self.cleaned_data.get("website", "")
        if value:
            raise forms.ValidationError("Spam detected.")
        return value

    def clean_rendered_at(self) -> str:
        raw = self.cleaned_data.get("rendered_at", "")
        try:
            rendered_at = signing.loads(raw, salt=_SIGNING_SALT)
        except signing.BadSignature as exc:
            raise forms.ValidationError("Spam detected.") from exc
        # Bounds are checked against the payload value itself, not
        # TimestampSigner's own max_age (which tracks real signing
        # wall-clock time, not the value we embedded in it).
        elapsed = time.time() - rendered_at
        if elapsed < MIN_SECONDS_TO_SUBMIT or elapsed > MAX_SECONDS_TO_SUBMIT:
            raise forms.ValidationError("Spam detected.")
        return raw
