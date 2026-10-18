"""Attendance registers: taking a class register, admin overview and the
student's own attendance history.

Re-saving a register upserts the records (unique per session + student), so a
register is never duplicated for the same date and class.
"""
import json

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.academics.models import AcademicYear, SchoolClass, SchoolSettings
from apps.audit.services import log_action
from apps.results.services import ATTENDANCE_WEIGHTS, attendance_summary

from .forms import AttendanceFilterForm, AttendanceRecordForm, status_field_name
from .models import ATTENDANCE_STATUS, AttendanceRecord, AttendanceSession

STATUS_COLOURS = {
    "present": "var(--ok)",
    "absent": "var(--bad)",
    "late": "var(--warn)",
    "excused": "var(--info)",
}


def _is_admin(user):
    return user.is_admin_role or user.is_superuser


def _current_year():
    conf = SchoolSettings.load()
    return conf.current_academic_year or AcademicYear.objects.filter(is_current=True).first() or AcademicYear.objects.first()


def _class_students(klass):
    return list(klass.students.filter(status="Active").order_by("first_name", "last_name"))


def _entry_url(klass, date):
    return f"{reverse('attendance:entry')}?school_class={klass.pk}&date={date.isoformat()}"


# ---------------------------------------------------------------------------
# Taking a register
# ---------------------------------------------------------------------------
def entry(request):
    """Pick a class + date and mark every student present/absent/late/excused."""
    user = request.user
    if not (user.is_authenticated and (user.is_admin_role or user.is_teacher_role or user.is_superuser)):
        raise PermissionDenied("Your account does not have access to this area.")
    teacher = getattr(user, "teacher_profile", None)

    if request.method == "POST":
        return _save_register(request, teacher)

    filter_form = AttendanceFilterForm(request.GET or None, initial={"date": timezone.localdate()})
    klass = None
    date = timezone.localdate()
    if request.GET and filter_form.is_valid():
        klass = filter_form.cleaned_data.get("school_class")
        date = filter_form.cleaned_data.get("date") or date

    rows = []
    session = None
    counts = None
    form = None
    if klass is not None:
        session = AttendanceSession.objects.filter(date=date, school_class=klass).first()
        students = _class_students(klass)
        existing = {}
        if session is not None:
            existing = {record.student_id: record.status for record in session.records.all()}
        form = AttendanceRecordForm(
            students=students, initial={status_field_name(sid): st for sid, st in existing.items()}
        )
        rows = form.rows()
        counts = session.counts if session is not None else None

    context = {
        "page_title": "Take attendance",
        "filter_form": filter_form,
        "school_class": klass,
        "date": date,
        "rows": rows,
        "form": form,
        "session": session,
        "counts": counts,
        "status_choices": ATTENDANCE_STATUS,
    }
    return render(request, "attendance/entry.html", context)


def _save_register(request, teacher):
    data = request.POST
    klass = None
    date = timezone.localdate()
    filter_form = AttendanceFilterForm(data)
    if filter_form.is_valid():
        klass = filter_form.cleaned_data.get("school_class")
        date = filter_form.cleaned_data.get("date") or date
    if klass is None:
        messages.error(request, "Choose a class before saving the register.")
        return redirect("attendance:entry")

    students = _class_students(klass)
    record_form = AttendanceRecordForm(data, students=students)
    if not record_form.is_valid():
        messages.error(request, "Some attendance selections were invalid. Please try again.")
        return redirect(_entry_url(klass, date))

    with transaction.atomic():
        session, _created = AttendanceSession.objects.get_or_create(
            date=date,
            school_class=klass,
            defaults={"teacher": teacher, "academic_year": _current_year()},
        )
        if session.teacher is None and teacher is not None:
            session.teacher = teacher
        if session.academic_year is None:
            session.academic_year = _current_year()
        for student, status in record_form.status_values():
            AttendanceRecord.objects.update_or_create(
                session=session, student=student, defaults={"status": status}
            )
        session.save()

    log_action(
        request,
        "Saved attendance",
        "Attendance",
        f"Register for {klass.name} on {date} — {session.records.count()} records.",
    )
    messages.success(request, f"Register saved for {klass.name} on {date:%d %b %Y}.")
    return redirect(_entry_url(klass, date))


# ---------------------------------------------------------------------------
# Admin overview
# ---------------------------------------------------------------------------
def overview(request):
    """Whole-school attendance summary with per-class counts and a trend."""
    user = request.user
    if not (user.is_authenticated and _is_admin(user)):
        raise PermissionDenied("Your account does not have access to this area.")

    records = AttendanceRecord.objects.all()
    total = records.count()
    present = records.filter(status__in=["present", "late"]).count()
    overall_pct = round(present / total * 100) if total else 0

    tally = {key: records.filter(status=key).count() for key, _ in ATTENDANCE_STATUS}

    per_class = []
    for klass in SchoolClass.objects.all():
        klass_records = records.filter(session__school_class=klass)
        klass_total = klass_records.count()
        klass_present = klass_records.filter(status__in=["present", "late"]).count()
        per_class.append(
            {
                "name": klass.name,
                "students": klass.students.filter(status="Active").count(),
                "sessions": AttendanceSession.objects.filter(school_class=klass).count(),
                "total": klass_total,
                "present": klass_present,
                "pct": round(klass_present / klass_total * 100) if klass_total else 0,
            }
        )

    dates = list(
        AttendanceSession.objects.values_list("date", flat=True).distinct().order_by("-date")[:10]
    )
    dates.reverse()
    trend = []
    for day in dates:
        day_records = records.filter(session__date=day)
        day_total = day_records.count()
        day_present = day_records.filter(status__in=["present", "late"]).count()
        trend.append({"label": day.strftime("%d %b"), "value": round(day_present / day_total * 100) if day_total else 0})

    donut = [
        {"label": label, "value": tally.get(key, 0), "color": STATUS_COLOURS.get(key)}
        for key, label in ATTENDANCE_STATUS
    ]

    context = {
        "page_title": "Attendance",
        "kpis": {
            "total_records": total,
            "present": present,
            "absent": tally.get("absent", 0),
            "sessions": AttendanceSession.objects.count(),
            "overall_pct": overall_pct,
        },
        "tally": tally,
        "per_class": per_class,
        "recent": AttendanceSession.objects.select_related("school_class", "teacher")[:12],
        "trend_json": json.dumps(trend),
        "donut_json": json.dumps(donut),
        "segments": donut,
    }
    return render(request, "attendance/overview.html", context)


# ---------------------------------------------------------------------------
# Student's own attendance
# ---------------------------------------------------------------------------
def my_attendance(request):
    user = request.user
    if not (user.is_authenticated and (user.is_student_role or user.is_superuser)):
        raise PermissionDenied("Your account does not have access to this area.")

    student = getattr(user, "student_profile", None)
    if student is None:
        return render(
            request,
            "attendance/my_attendance.html",
            {"page_title": "My attendance", "student": None, "summary": None, "records": [], "trend": []},
        )

    summary = attendance_summary(student)
    records = list(
        AttendanceRecord.objects.filter(student=student)
        .select_related("session", "session__school_class")
        .order_by("-session__date", "-id")[:60]
    )

    # Per-day trend for the student (last 10 marked days).
    dates = list(
        AttendanceRecord.objects.filter(student=student)
        .values_list("session__date", flat=True)
        .distinct()
        .order_by("-session__date")[:10]
    )
    dates.reverse()
    trend = []
    for day in dates:
        day_records = AttendanceRecord.objects.filter(student=student, session__date=day)
        weighted = sum(ATTENDANCE_WEIGHTS.get(r.status, 0) for r in day_records)
        pct = round(weighted / len(day_records) * 100) if day_records else 0
        trend.append({"label": day.strftime("%d %b"), "value": pct})

    context = {
        "page_title": "My attendance",
        "student": student,
        "summary": summary,
        "records": records,
        "trend_json": json.dumps(trend),
    }
    return render(request, "attendance/my_attendance.html", context)


@require_POST
def session_delete(request, pk):
    user = request.user
    if not (user.is_authenticated and _is_admin(user)):
        raise PermissionDenied("Your account does not have access to this area.")
    session = get_object_or_404(AttendanceSession.objects.select_related("school_class"), pk=pk)
    label = str(session)
    session.delete()
    log_action(request, "Deleted attendance session", "Attendance", f"Deleted register {label}.")
    messages.success(request, "Attendance session deleted.")
    return redirect("attendance:overview")
