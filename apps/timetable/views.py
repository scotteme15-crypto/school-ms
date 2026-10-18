"""Weekly timetable views, scoped per role.

Admins manage slots for any class; teachers and students get a read-only view
of the periods that concern them.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.academics.models import SchoolClass
from apps.accounts.permissions import admin_required
from apps.audit.services import log_action

from .forms import TimetableSlotForm
from .models import DAY_CHOICES, TimetableSlot


def _grid(slots):
    """Turn a flat list of slots into a day-by-time grid for the ``.tt`` table."""
    days = [day for day, _ in DAY_CHOICES]
    times = sorted({slot.start_time for slot in slots})
    lookup = {(slot.start_time, slot.day): slot for slot in slots}
    rows = [{"time": time, "cells": [lookup.get((time, day)) for day in days]} for time in times]
    return days, rows


@login_required
def index(request):
    user = request.user
    classes = []
    selected_class = None

    if user.is_admin_role or user.is_superuser:
        classes = list(SchoolClass.objects.all())
        selected_class = SchoolClass.objects.filter(pk=request.GET.get("class")).first()
        if selected_class is None and classes:
            selected_class = classes[0]
        slots = (
            list(
                TimetableSlot.objects.filter(school_class=selected_class).select_related(
                    "subject", "teacher"
                )
            )
            if selected_class
            else []
        )
    elif user.is_teacher_role:
        teacher = getattr(user, "teacher_profile", None)
        slots = (
            list(
                TimetableSlot.objects.filter(teacher=teacher).select_related(
                    "subject", "teacher", "school_class"
                )
            )
            if teacher
            else []
        )
    else:
        student = getattr(user, "student_profile", None)
        if student and student.school_class_id:
            selected_class = student.school_class
            slots = list(
                TimetableSlot.objects.filter(school_class=student.school_class).select_related(
                    "subject", "teacher"
                )
            )
        else:
            slots = []

    days, rows = _grid(slots)
    context = {
        "page_title": "Timetable",
        "days": days,
        "rows": rows,
        "has_slots": bool(slots),
        "classes": classes,
        "selected_class": selected_class,
        "can_manage": user.is_admin_role or user.is_superuser,
        "scope": "teacher" if user.is_teacher_role else ("student" if user.is_student_role else "class"),
    }
    return render(request, "timetable/index.html", context)


@admin_required
def slot_create(request):
    initial = {}
    if request.GET.get("class"):
        initial["school_class"] = request.GET.get("class")
    form = TimetableSlotForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        slot = form.save()
        log_action(
            request,
            "Created timetable slot",
            "Timetable",
            f"{slot.school_class.name} · {slot.day} {slot.start_time:%H:%M}",
        )
        messages.success(request, "Timetable slot added.")
        return redirect(f"{reverse('timetable:index')}?class={slot.school_class_id}")
    return render(
        request,
        "timetable/slot_form.html",
        {"form": form, "page_title": "Add timetable slot", "mode": "create"},
    )


@admin_required
def slot_edit(request, pk):
    slot = get_object_or_404(TimetableSlot, pk=pk)
    form = TimetableSlotForm(request.POST or None, instance=slot)
    if request.method == "POST" and form.is_valid():
        slot = form.save()
        log_action(
            request,
            "Updated timetable slot",
            "Timetable",
            f"{slot.school_class.name} · {slot.day} {slot.start_time:%H:%M}",
        )
        messages.success(request, "Timetable slot updated.")
        return redirect(f"{reverse('timetable:index')}?class={slot.school_class_id}")
    return render(
        request,
        "timetable/slot_form.html",
        {"form": form, "page_title": "Edit timetable slot", "slot": slot, "mode": "edit"},
    )


@admin_required
@require_POST
def slot_delete(request, pk):
    slot = get_object_or_404(TimetableSlot, pk=pk)
    class_id = slot.school_class_id
    label = f"{slot.school_class.name} · {slot.day} {slot.start_time:%H:%M}"
    slot.delete()
    log_action(request, "Deleted timetable slot", "Timetable", label)
    messages.success(request, "Timetable slot removed.")
    return redirect(f"{reverse('timetable:index')}?class={class_id}")
