from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django_ratelimit.decorators import ratelimit

from .forms import ContactForm
from .services import save_contact_message

PAGE_DESCRIPTION = (
    "Get in touch with Muhammad Umer, a Django developer and AI engineer, "
    "using the form below or one of his public profiles."
)


def _render_form(request: HttpRequest, form: ContactForm, *, status: int = 200) -> HttpResponse:
    context = {
        "form": form,
        "page_title": "Contact | Muhammad Umer",
        "page_description": PAGE_DESCRIPTION,
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
