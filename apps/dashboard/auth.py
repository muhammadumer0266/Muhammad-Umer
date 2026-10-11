"""Dashboard authentication: password + (optionally required) TOTP.

Zero trust on every request, not just at login:
- staff_required re-checks active + staff + (when ADMIN_REQUIRE_OTP) an
  OTP-verified session on *every* dashboard view;
- login goes through django.contrib.auth.authenticate(request=...), so
  django-axes counts failures and locks out exactly as it did for the old
  admin;
- `next` redirects are only honoured if they stay inside the dashboard.
"""

from collections.abc import Callable
from functools import wraps
from urllib.parse import urlencode

from django import forms
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_POST
from django_otp import login as otp_login
from django_otp import match_token


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"autocomplete": "username", "autofocus": True}),
    )
    password = forms.CharField(
        strip=False, widget=forms.PasswordInput(attrs={"autocomplete": "current-password"})
    )
    otp_token = forms.CharField(
        required=False,
        max_length=16,
        label="Authenticator code",
        widget=forms.TextInput(
            attrs={"autocomplete": "one-time-code", "inputmode": "numeric", "spellcheck": "false"}
        ),
    )


def _otp_required() -> bool:
    return bool(getattr(settings, "ADMIN_REQUIRE_OTP", False))


def _is_trusted(user) -> bool:
    if not (user.is_authenticated and user.is_active and user.is_staff):
        return False
    return not _otp_required() or user.is_verified()


def staff_required(view: Callable[..., HttpResponse]) -> Callable[..., HttpResponse]:
    @wraps(view)
    @never_cache
    def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not _is_trusted(request.user):
            if request.user.is_authenticated:
                auth_logout(request)  # e.g. staff flag removed mid-session
            login_url = reverse("dashboard:login")
            return redirect(f"{login_url}?{urlencode({'next': request.get_full_path()})}")
        return view(request, *args, **kwargs)

    return wrapper


def _safe_next(request: HttpRequest) -> str:
    target = request.POST.get("next") or request.GET.get("next") or ""
    dashboard_root = reverse("dashboard:overview")
    if target.startswith(dashboard_root) and url_has_allowed_host_and_scheme(
        target, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return target
    return dashboard_root


@sensitive_post_parameters("password", "otp_token")
@csrf_protect
@never_cache
def login_view(request: HttpRequest) -> HttpResponse:
    if _is_trusted(request.user):
        return HttpResponseRedirect(_safe_next(request))

    form = LoginForm(request.POST or None)
    error = ""
    if request.method == "POST" and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password"],
        )
        if getattr(request, "axes_locked_out", False):
            return render(request, "dashboard/locked.html", status=429)
        if user is None or not user.is_staff:
            error = "Those details don't match a dashboard account."
        elif _otp_required():
            device = match_token(user, form.cleaned_data["otp_token"].strip())
            if device is None:
                error = "Enter the current code from your authenticator app."
            else:
                auth_login(request, user)
                otp_login(request, device)
                return HttpResponseRedirect(_safe_next(request))
        else:
            auth_login(request, user)
            return HttpResponseRedirect(_safe_next(request))

    return render(
        request,
        "dashboard/login.html",
        {
            "form": form,
            "error": error,
            "otp_required": _otp_required(),
            "next": _safe_next(request),
        },
        status=400 if error else 200,
    )


@require_POST
@csrf_protect
def logout_view(request: HttpRequest) -> HttpResponse:
    auth_logout(request)
    return redirect("dashboard:login")
