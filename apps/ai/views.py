from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django_ratelimit.decorators import ratelimit

from .forms import AskForm
from .services import ask

PAGE_TITLE = "Ask | Muhammad Umer"
PAGE_DESCRIPTION = (
    "Ask a question about Muhammad Umer's work -- answered only from this "
    "site's own content, with citations, or an honest 'I don't know'."
)


@ratelimit(key="ip", rate="20/h", method="POST", block=False)
def ask_view(request: HttpRequest) -> HttpResponse:
    result = None
    limited = getattr(request, "limited", False)

    if request.method == "POST" and not limited:
        form = AskForm(request.POST)
        if form.is_valid():
            result = ask(form.cleaned_data["question"])
    else:
        form = AskForm()

    context = {
        "form": form,
        "result": result,
        "limited": limited,
        "page_title": PAGE_TITLE,
        "page_description": PAGE_DESCRIPTION,
    }
    return render(request, "pages/ask.html", context)
