from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django_ratelimit.decorators import ratelimit

from apps.portfolio.selectors import get_profile

from .forms import AskForm
from .guardrails import ask_rate, get_policy
from .services import ask

PAGE_DESCRIPTION = (
    "Ask a question about this site's published work -- answered only from "
    "the site's own content, with citations, or an honest 'I don't know'."
)


@ratelimit(key="ip", rate=ask_rate, method="POST", block=False)
def ask_view(request: HttpRequest) -> HttpResponse:
    result = None
    limited = getattr(request, "limited", False)
    policy = get_policy()
    status = 200

    if request.method == "POST" and not limited and policy.enabled:
        form = AskForm(request.POST)
        if form.is_valid():
            result = ask(form.cleaned_data["question"])
    else:
        form = AskForm()
        if limited:
            status = 429

    context = {
        "form": form,
        "result": result,
        "limited": limited,
        "policy": policy,
        "page_title": f"Ask | {get_profile(request).full_name}",
        "page_description": PAGE_DESCRIPTION,
    }
    return render(request, "pages/ask.html", context, status=status)
