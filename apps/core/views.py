from django.db import connections
from django.db.utils import OperationalError
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string


def handler404(request: HttpRequest, exception: Exception | None = None) -> HttpResponse:
    response = render(request, "404.html", status=404)
    response["X-Robots-Tag"] = "noindex"
    return response


def handler500(request: HttpRequest) -> HttpResponse:
    # Deliberately not django.shortcuts.render: it always builds a
    # RequestContext and runs every context processor (including the one
    # that queries Profile), which would re-trigger a DB failure while
    # rendering the page meant to survive one. render_to_string with no
    # context/request needs neither the database nor base.html.
    html = render_to_string("500.html")
    response = HttpResponse(html, status=500)
    response["X-Robots-Tag"] = "noindex"
    return response


def privacy(request: HttpRequest) -> HttpResponse:
    context = {
        "page_title": "Privacy | Muhammad Umer",
        "page_description": (
            "What this site collects through the contact form, and why -- "
            "no tracking cookies, no third-party analytics."
        ),
    }
    return render(request, "pages/privacy.html", context)


def healthz(request):
    """Liveness and readiness probe. No auth, no secrets in the response."""
    db_ok = True
    try:
        connections["default"].cursor()
    except OperationalError:
        db_ok = False

    status = 200 if db_ok else 503
    return JsonResponse({"status": "ok" if db_ok else "error", "database": db_ok}, status=status)
