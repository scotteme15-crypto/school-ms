"""Announcements feed and the school events calendar.

Everyone can read; visibility of announcements is filtered by audience. Only
administrators may publish, edit or remove content.
"""
import calendar
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.permissions import admin_required
from apps.audit.services import log_action

from .forms import AnnouncementForm, SchoolEventForm
from .models import Announcement, SchoolEvent

DOW_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _visible(user):
    """Announcements the signed-in user is allowed to read."""
    qs = Announcement.objects.select_related("author")
    if user.is_admin_role or user.is_superuser:
        return qs
    if user.is_teacher_role:
        return qs.filter(audience__in=["Everyone", "Teachers"])
    student = getattr(user, "student_profile", None)
    if student is not None:
        return qs.filter(audience__in=["Everyone", "Students", f"Grade {student.grade}"])
    return qs.filter(audience="Everyone")


def _month_start(value):
    today = timezone.localdate()
    if value:
        try:
            year, month = (int(part) for part in value.split("-"))
            return date(year, month, 1)
        except (ValueError, TypeError):
            pass
    return today.replace(day=1)


def _month_grid(events, first_of_month, today):
    """Build six weeks (Monday-first) of calendar cells for the given month."""
    last_day = calendar.monthrange(first_of_month.year, first_of_month.month)[1]
    start = first_of_month - timedelta(days=first_of_month.weekday())
    end = date(first_of_month.year, first_of_month.month, last_day)
    end = end + timedelta(days=6 - end.weekday())

    by_day = {}
    for event in events:
        by_day.setdefault(event.date, []).append(event)

    weeks, day = [], start
    while day <= end:
        week = []
        for _ in range(7):
            week.append(
                {
                    "date": day,
                    "in_month": day.month == first_of_month.month,
                    "today": day == today,
                    "events": by_day.get(day, []),
                }
            )
            day += timedelta(days=1)
        weeks.append(week)
    return weeks


# ---------------------------------------------------------------------------
# Announcements
# ---------------------------------------------------------------------------
@login_required
def list_view(request):
    user = request.user
    notices = _visible(user)
    priority = request.GET.get("priority")
    if priority:
        notices = notices.filter(priority=priority)
    page_obj = Paginator(notices, 12).get_page(request.GET.get("page"))
    context = {
        "page_title": "Announcements",
        "page_obj": page_obj,
        "can_manage": user.is_admin_role or user.is_superuser,
        "priority_filter": priority or "",
    }
    return render(request, "announcements/list.html", context)


@admin_required
def create(request):
    form = AnnouncementForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        notice = form.save(commit=False)
        notice.author = request.user
        notice.save()
        log_action(request, "Published announcement", "Announcements", notice.title)
        messages.success(request, "Announcement published.")
        return redirect("announcements:list")
    return render(
        request,
        "announcements/form.html",
        {"form": form, "page_title": "New announcement", "mode": "create"},
    )


@admin_required
def edit(request, pk):
    notice = get_object_or_404(Announcement, pk=pk)
    form = AnnouncementForm(request.POST or None, instance=notice)
    if request.method == "POST" and form.is_valid():
        notice = form.save()
        log_action(request, "Updated announcement", "Announcements", notice.title)
        messages.success(request, "Announcement updated.")
        return redirect("announcements:list")
    return render(
        request,
        "announcements/form.html",
        {"form": form, "page_title": "Edit announcement", "notice": notice, "mode": "edit"},
    )


@admin_required
@require_POST
def delete(request, pk):
    notice = get_object_or_404(Announcement, pk=pk)
    title = notice.title
    notice.delete()
    log_action(request, "Deleted announcement", "Announcements", title)
    messages.success(request, "Announcement deleted.")
    return redirect("announcements:list")


# ---------------------------------------------------------------------------
# School events calendar
# ---------------------------------------------------------------------------
@login_required
def event_list(request):
    today = timezone.localdate()
    first_of_month = _month_start(request.GET.get("month"))
    events = list(SchoolEvent.objects.all())
    context = {
        "page_title": "School events",
        "dow_labels": DOW_LABELS,
        "weeks": _month_grid(events, first_of_month, today),
        "month_label": first_of_month.strftime("%B %Y"),
        "prev_month": (first_of_month - timedelta(days=1)).strftime("%Y-%m"),
        "next_month": (first_of_month + timedelta(days=32)).replace(day=1).strftime("%Y-%m"),
        "upcoming": [e for e in events if e.date >= today][:8],
        "past": sorted([e for e in events if e.date < today], key=lambda e: e.date, reverse=True)[:8],
        "can_manage": request.user.is_admin_role or request.user.is_superuser,
    }
    return render(request, "announcements/event_list.html", context)


@admin_required
def event_create(request):
    form = SchoolEventForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        event = form.save()
        log_action(request, "Created event", "Announcements", event.title)
        messages.success(request, "Event added to the calendar.")
        return redirect("announcements:event_list")
    return render(
        request,
        "announcements/event_form.html",
        {"form": form, "page_title": "New event", "mode": "create"},
    )


@admin_required
def event_edit(request, pk):
    event = get_object_or_404(SchoolEvent, pk=pk)
    form = SchoolEventForm(request.POST or None, instance=event)
    if request.method == "POST" and form.is_valid():
        event = form.save()
        log_action(request, "Updated event", "Announcements", event.title)
        messages.success(request, "Event updated.")
        return redirect("announcements:event_list")
    return render(
        request,
        "announcements/event_form.html",
        {"form": form, "page_title": "Edit event", "event": event, "mode": "edit"},
    )


@admin_required
@require_POST
def event_delete(request, pk):
    event = get_object_or_404(SchoolEvent, pk=pk)
    title = event.title
    event.delete()
    log_action(request, "Deleted event", "Announcements", title)
    messages.success(request, "Event removed from the calendar.")
    return redirect("announcements:event_list")
