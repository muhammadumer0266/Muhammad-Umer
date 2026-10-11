import csv
from datetime import timedelta
from functools import reduce
from operator import or_

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.forms import modelform_factory
from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.ai.indexing import reindex
from apps.ai.models import AskLog, GuardrailPolicy, RagDocument
from apps.contact.models import ContactMessage
from apps.portfolio.models import Certification, Entry, Photo, Profile, Resume, ResumeRequest

from .auth import staff_required
from .forms import DashboardModelForm, GuardrailPolicyForm, ProfileForm
from .sections import BY_SLUG, Section, grouped

PAGE_SIZE = 25


def _ctx(request: HttpRequest, **extra) -> dict:
    """Shared context: sidebar groups and the unread badge."""
    return {
        "nav_groups": grouped(),
        "unread_messages": ContactMessage.objects.filter(status=ContactMessage.Status.NEW).count(),
        "active_section": extra.pop("active_section", ""),
        **extra,
    }


def _section(slug: str) -> Section:
    section = BY_SLUG.get(slug)
    if section is None:
        raise Http404
    return section


def _form_class(section: Section) -> type[DashboardModelForm]:
    if section.form_class:
        return section.form_class
    return modelform_factory(section.model, form=DashboardModelForm, fields=list(section.fields))


def _cell(obj, column) -> dict:
    value = obj
    for part in column.attr.split("__"):
        value = getattr(value, part, "")
    if callable(value):
        value = value()
    return {"kind": column.kind, "value": value}


# --- overview ----------------------------------------------------------------


@staff_required
def overview(request: HttpRequest) -> HttpResponse:
    week_ago = timezone.now() - timedelta(days=7)
    asks = AskLog.objects.filter(created_at__gte=week_ago)
    asked = asks.count()
    stats = [
        ("Published work", Entry.objects.filter(is_published=True).count(), "work"),
        (
            "Certifications",
            Certification.objects.filter(is_published=True).count(),
            "certifications",
        ),
        ("Photos", Photo.objects.filter(is_published=True).count(), "photos"),
        (
            "Résumé requests · 7d",
            ResumeRequest.objects.filter(created_at__gte=week_ago).count(),
            "resume-requests",
        ),
        ("Ask questions · 7d", asked, "ask-logs"),
        (
            "Refused · 7d",
            f"{round(100 * asks.filter(refused=True).count() / asked) if asked else 0}%",
            "ask-logs",
        ),
    ]
    profile = Profile.get_solo()
    checklist = [
        ("Headline set", bool(profile.headline), reverse("dashboard:profile")),
        ("Summary written", bool(profile.bio_short), reverse("dashboard:profile")),
        ("Profile photo uploaded", bool(profile.photo), reverse("dashboard:profile")),
        (
            "Active résumé uploaded",
            Resume.objects.filter(is_active=True).exists(),
            reverse("dashboard:create", args=["resumes"]),
        ),
        (
            "At least one published project",
            Entry.objects.filter(is_published=True, is_sample=False).exists(),
            reverse("dashboard:create", args=["work"]),
        ),
    ]
    return render(
        request,
        "dashboard/overview.html",
        _ctx(
            request,
            stats=stats,
            checklist=checklist,
            recent_messages=ContactMessage.objects.all()[:5],
            recent_requests=ResumeRequest.objects.select_related("resume")[:5],
            indexed_documents=RagDocument.objects.count(),
            profile=profile,
        ),
    )


# --- generic sections ----------------------------------------------------------


@staff_required
def section_list(request: HttpRequest, section: str) -> HttpResponse:
    sec = _section(section)
    qs = sec.model.objects.all()
    if sec.select_related:
        qs = qs.select_related(*sec.select_related)
    query = request.GET.get("q", "").strip()[:100]
    if query and sec.search:
        qs = qs.filter(reduce(or_, (Q(**{f"{f}__icontains": query}) for f in sec.search)))
    page = Paginator(qs, PAGE_SIZE).get_page(request.GET.get("page"))
    rows = [
        {
            "obj": obj,
            "cells": [_cell(obj, c) for c in sec.columns],
            "url": (
                reverse(sec.detail_url, args=[obj.pk])
                if sec.detail_url
                else reverse("dashboard:edit", args=[sec.slug, obj.pk])
                if sec.can_edit
                else ""
            ),
        }
        for obj in page.object_list
    ]
    return render(
        request,
        "dashboard/list.html",
        _ctx(
            request,
            section=sec,
            active_section=sec.slug,
            rows=rows,
            page=page,
            query=query,
        ),
    )


def _save_form(request: HttpRequest, sec: Section, instance=None) -> HttpResponse:
    form_class = _form_class(sec)
    form = form_class(request.POST or None, request.FILES or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        messages.success(request, f"Saved {sec.singular} “{obj}”.")
        if "save_add" in request.POST and sec.can_add:
            return redirect("dashboard:create", sec.slug)
        return redirect("dashboard:list", sec.slug)
    return render(
        request,
        "dashboard/form.html",
        _ctx(
            request,
            section=sec,
            active_section=sec.slug,
            form=form,
            object=instance,
        ),
        status=400 if form.errors else 200,
    )


@staff_required
def section_create(request: HttpRequest, section: str) -> HttpResponse:
    sec = _section(section)
    if not sec.can_add:
        raise Http404
    return _save_form(request, sec)


@staff_required
def section_edit(request: HttpRequest, section: str, pk: int) -> HttpResponse:
    sec = _section(section)
    if not sec.can_edit:
        raise Http404
    return _save_form(request, sec, get_object_or_404(sec.model, pk=pk))


@staff_required
def section_delete(request: HttpRequest, section: str, pk: int) -> HttpResponse:
    sec = _section(section)
    if not sec.can_delete:
        raise Http404
    obj = get_object_or_404(sec.model, pk=pk)
    if request.method == "POST":
        label = str(obj)
        obj.delete()
        messages.success(request, f"Deleted {sec.singular} “{label}”.")
        return redirect("dashboard:list", sec.slug)
    return render(
        request,
        "dashboard/confirm_delete.html",
        _ctx(request, section=sec, active_section=sec.slug, object=obj),
    )


# --- singletons ------------------------------------------------------------


@staff_required
def profile_edit(request: HttpRequest) -> HttpResponse:
    profile = Profile.get_solo()
    form = ProfileForm(request.POST or None, request.FILES or None, instance=profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile saved. It's live on the site now.")
        return redirect("dashboard:profile")
    return render(
        request,
        "dashboard/profile.html",
        _ctx(request, active_section="profile", form=form, profile=profile),
        status=400 if form.errors else 200,
    )


@staff_required
def policy_edit(request: HttpRequest) -> HttpResponse:
    policy = GuardrailPolicy.get_solo()
    form = GuardrailPolicyForm(request.POST or None, instance=policy)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Guardrail policy saved. It applies to the next question.")
        return redirect("dashboard:policy")
    return render(
        request,
        "dashboard/policy.html",
        _ctx(
            request,
            active_section="policy",
            form=form,
            indexed_documents=RagDocument.objects.count(),
        ),
        status=400 if form.errors else 200,
    )


@staff_required
@require_POST
def reindex_now(request: HttpRequest) -> HttpResponse:
    stats = reindex()
    messages.success(
        request,
        f"Ask index rebuilt: {stats.indexed} updated, {stats.skipped} unchanged, "
        f"{stats.removed} removed.",
    )
    return redirect("dashboard:policy")


# --- inbox -------------------------------------------------------------------


@staff_required
def message_detail(request: HttpRequest, pk: int) -> HttpResponse:
    message = get_object_or_404(ContactMessage, pk=pk)
    if request.method == "POST":
        status = request.POST.get("status")
        if status in ContactMessage.Status.values:
            message.status = status
            message.save(update_fields=["status", "updated_at"])
            messages.success(request, f"Marked as {message.get_status_display().lower()}.")
        return redirect("dashboard:list", "messages")
    if message.status == ContactMessage.Status.NEW:
        message.status = ContactMessage.Status.READ
        message.save(update_fields=["status", "updated_at"])
    return render(
        request,
        "dashboard/message_detail.html",
        _ctx(
            request,
            section=BY_SLUG["messages"],
            active_section="messages",
            message=message,
            statuses=ContactMessage.Status.choices,
        ),
    )


# --- résumés -------------------------------------------------------------


@staff_required
def resume_file(request: HttpRequest, pk: int) -> FileResponse:
    """Owner-only preview of a private résumé file (not counted as a download)."""
    resume = get_object_or_404(Resume, pk=pk)
    response = FileResponse(resume.file.open("rb"), content_type="application/pdf")
    response["Cache-Control"] = "no-store, private"
    return response


@staff_required
def resume_requests_csv(request: HttpRequest) -> HttpResponse:
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="resume-requests.csv"'
    response["Cache-Control"] = "no-store, private"
    writer = csv.writer(response)
    writer.writerow(["email", "resume", "downloaded", "requested_at"])
    for item in ResumeRequest.objects.select_related("resume").iterator():
        # Neutralise spreadsheet formula injection from user-supplied emails.
        email = f"'{item.email}" if item.email[:1] in "=+-@" else item.email
        writer.writerow([email, item.resume or "", item.downloaded, item.created_at.isoformat()])
    return response
