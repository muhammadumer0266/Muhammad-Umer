"""Email-gated resume download.

1. Visitor submits their email on /resume/ (honeypot + time-trap + per-IP
   rate limit, like the contact form).
2. A ResumeRequest is stored and the visitor gets a signed download link
   that expires after DOWNLOAD_TOKEN_MAX_AGE seconds.
3. /resume/download/<token>/ streams the file from private storage.

The file itself is never at a public URL, so the only way to it is through
the email step.
"""

from django import forms
from django.core import signing
from django.db.models import F
from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.text import slugify
from django_ratelimit.decorators import ratelimit

from apps.contact.forms import ContactForm
from apps.core.net import client_ip
from apps.core.privacy import salted_hash

from .models import Resume, ResumeRequest
from .selectors import get_profile

DOWNLOAD_TOKEN_MAX_AGE = 15 * 60
_SIGNING_SALT = "apps.portfolio.resume.download"


class ResumeRequestForm(forms.Form):
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(
            attrs={"autocomplete": "email", "aria-describedby": "email-help email-error"}
        ),
    )
    # Same spam traps as the contact form: a hidden honeypot and a signed
    # render timestamp (too-fast or stale submissions are rejected).
    website = ContactForm.base_fields["website"]
    rendered_at = ContactForm.base_fields["rendered_at"]
    clean_website = ContactForm.clean_website
    clean_rendered_at = ContactForm.clean_rendered_at


def make_download_token(resume_request: ResumeRequest) -> str:
    return signing.dumps({"r": resume_request.pk}, salt=_SIGNING_SALT)


def resolve_download_token(token: str) -> ResumeRequest | None:
    try:
        data = signing.loads(token, salt=_SIGNING_SALT, max_age=DOWNLOAD_TOKEN_MAX_AGE)
    except signing.BadSignature:
        return None
    return ResumeRequest.objects.select_related("resume").filter(pk=data.get("r")).first()


@ratelimit(key="ip", rate="5/h", method="POST", block=False)
def resume_request_view(request: HttpRequest) -> HttpResponse:
    profile = get_profile(request)
    resume = Resume.active()
    context = {
        "resume_available": resume is not None,
        "page_title": f"Résumé | {profile.full_name}",
        "page_description": (
            f"Download {profile.full_name}'s résumé: enter your email and the PDF "
            "downloads right away."
        ),
    }
    if resume is None:
        return render(request, "pages/resume.html", context)

    if request.method != "POST":
        context["form"] = ResumeRequestForm()
        return render(request, "pages/resume.html", context)

    form = ResumeRequestForm(request.POST)
    if getattr(request, "limited", False):
        form.add_error(None, "Too many requests from your network. Please try again later.")
        context["form"] = form
        return render(request, "pages/resume.html", context, status=429)
    if not form.is_valid():
        context["form"] = form
        return render(request, "pages/resume.html", context)

    resume_request = ResumeRequest.objects.create(
        email=form.cleaned_data["email"],
        resume=resume,
        ip_hash=salted_hash(client_ip(request)),
        user_agent_hash=salted_hash(request.META.get("HTTP_USER_AGENT", "")),
    )
    context["download_url"] = reverse(
        "portfolio:resume_download", args=[make_download_token(resume_request)]
    )
    return render(request, "pages/resume_thanks.html", context)


def resume_download_view(request: HttpRequest, token: str) -> FileResponse:
    resume_request = resolve_download_token(token)
    if resume_request is None:
        raise Http404("This download link has expired. Please request the résumé again.")
    resume = resume_request.resume or Resume.active()
    if resume is None or not resume.file:
        raise Http404

    ResumeRequest.objects.filter(pk=resume_request.pk).update(downloaded=True)
    Resume.objects.filter(pk=resume.pk).update(download_count=F("download_count") + 1)

    filename = f"{slugify(get_profile(request).full_name) or 'resume'}-resume.pdf"
    response = FileResponse(
        resume.file.open("rb"),
        as_attachment=True,
        filename=filename,
        content_type="application/pdf",
    )
    response["Cache-Control"] = "no-store, private"
    response["X-Robots-Tag"] = "noindex, nofollow"
    return response
