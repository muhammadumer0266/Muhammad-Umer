from django.conf import settings
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django_ratelimit.decorators import ratelimit

from apps.portfolio.selectors import get_profile

from .forms import ContactForm
from .services import save_contact_message


def _render_form(request: HttpRequest, form: ContactForm, *, status: int = 200) -> HttpResponse:
    profile = get_profile(request)
    context = {
        "form": form,
        # Only ever exposed when the owner opts in from the admin.
        "public_email": settings.CONTACT_EMAIL if profile.public_email_visible else "",
        "page_title": f"Contact | {profile.full_name}",
        "page_description": (
            f"Get in touch with {profile.full_name}, a Django developer and AI engineer, "
            "using the form below or one of his public profiles."
        ),
    }
    return render(request, "pages/contact.html", context, status=status)


@ratelimit(key="ip", rate="5/h", method="POST", block=False)
def contact(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        return _render_form(request, ContactForm())

    if getattr(request, "limited", False):
        form = ContactForm(request.POST)
        form.add_error(None, "Too many messages sent recently. Please try again later.")
        return _render_form(request, form, status=429)

    form = ContactForm(request.POST)
    if form.is_valid():
        save_contact_message(
            request,
            name=form.cleaned_data["name"],
            email=form.cleaned_data["email"],
            message=form.cleaned_data["message"],
        )
        messages.success(request, "Thanks — your message has been sent.")
        return redirect("contact:contact")

    return _render_form(request, form)
