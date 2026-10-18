"""Reporting & analytics screens plus CSV exports (administrators only).

All figures are derived from the shared ``results.services`` readers so a
report can never expose unpublished (non-approved) marks.
"""
import csv
import json
from decimal import Decimal

from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from apps.academics.models import AssessmentComponent, GRADE_CHOICES
from apps.accounts.permissions import admin_required
from apps.attendance.models import AttendanceRecord, AttendanceSession
from apps.audit.services import log_action
from apps.results.models import SubjectMark
from apps.results.services import PUBLISHED, attendance_summary, pass_rate, published_marks
from apps.results.services import ranked_students, subject_performance
from apps.students.models import Student

# The reports that can be exported as CSV (surfaced on the reports hub).
REPORT_CATALOG = [
    {
        "key": "student_marks",
        "name": "Student marks",
        "description": "Every published subject mark with totals, percentages and grades.",
        "icon": "clip",
    },
    {
        "key": "attendance",
        "name": "Attendance register",
        "description": "Per-student attendance totals with a weighted attendance percentage.",
        "icon": "check",
    },
    {
        "key": "class_rankings",
        "name": "Class rankings",
        "description": "Students ranked by average score for the current period.",
        "icon": "award",
    },
]
REPORT_KEYS = {r["key"] for r in REPORT_CATALOG}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _current_period():
    """Configured (academic year, semester) pair with graceful fallbacks."""
    from apps.academics.models import AcademicYear, SchoolSettings, Semester

    conf = SchoolSettings.load()
    year = (
        conf.current_academic_year
        or AcademicYear.objects.filter(is_current=True).first()
        or AcademicYear.objects.first()
    )
    semester = conf.current_semester
    if semester is None and year is not None:
        semester = (
            Semester.objects.filter(academic_year=year, is_current=True).first()
            or Semester.objects.filter(academic_year=year).first()
        )
    return year, semester


def _selected_class(request):
    """Resolve the optional ``?class=<id>`` filter to a SchoolClass or None."""
    from apps.academics.models import SchoolClass

    raw = request.GET.get("class", "").strip()
    if raw.isdigit():
        return SchoolClass.objects.filter(pk=int(raw)).first()
    return None


def _pct(part, whole):
    return round(part / whole * 100) if whole else 0


def _average_by_grade(year, semester):
    max_total = AssessmentComponent.total_max_score() or Decimal("100")
    rows = []
    for grade, _ in GRADE_CHOICES:
        marks = published_marks(year=year, semester=semester).filter(student__grade=grade)
        totals = marks.annotate(entry_total=Sum("entries__score"))
        values = [float((m.entry_total or 0) / max_total * 100) for m in totals]
        rows.append({"label": f"G{grade}", "value": round(sum(values) / len(values)) if values else 0})
    return rows


def _attendance_trend(limit=10):
    dates = list(
        AttendanceSession.objects.values_list("date", flat=True).distinct().order_by("-date")[:limit]
    )
    dates.reverse()
    series = []
    for day in dates:
        records = AttendanceRecord.objects.filter(session__date=day)
        total = records.count()
        present = records.filter(status__in=["present", "late"]).count()
        series.append({"label": day.strftime("%d %b"), "value": _pct(present, total)})
    return series


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------
@admin_required
def index(request):
    """Reports hub: what can be viewed or exported."""
    from apps.academics.models import SchoolClass

    year, semester = _current_period()
    context = {
        "page_title": "Reports",
        "reports": REPORT_CATALOG,
        "year": year,
        "semester": semester,
        "classes": SchoolClass.objects.select_related("academic_year").order_by("grade", "section"),
        "stats": {
            "students": Student.objects.filter(status="Active").count(),
            "classes": SchoolClass.objects.count(),
            "published_marks": SubjectMark.objects.filter(result_sheet__status=PUBLISHED).count(),
            "attendance_days": AttendanceSession.objects.values("date").distinct().count(),
        },
    }
    return render(request, "reports/index.html", context)


@admin_required
def analytics(request):
    """Charts: enrolment, averages, subject performance, pass rate, attendance."""
    year, semester = _current_period()

    active = Student.objects.filter(status="Active")
    enrolment = [{"label": f"G{g}", "value": active.filter(grade=g).count()} for g, _ in GRADE_CHOICES]

    perf = _average_by_grade(year, semester)

    subjects = subject_performance(year, semester)
    subject_rows = [
        {"label": row["subject"].name, "value": float(row["average"]), "display": f"{row['average']:.1f}%"}
        for row in subjects
    ]

    rate = pass_rate(year, semester)
    pass_segments = [
        {"label": "Pass", "value": rate["pass"], "color": "var(--ok)"},
        {"label": "Fail", "value": rate["fail"], "color": "var(--bad)"},
    ]

    trend = _attendance_trend()

    context = {
        "page_title": "Analytics",
        "year": year,
        "semester": semester,
        "totals": {
            "students": active.count(),
            "marks": SubjectMark.objects.filter(result_sheet__status=PUBLISHED).count(),
            "pass": rate["pass"],
            "fail": rate["fail"],
            "pass_rate": rate["rate"],
        },
        "enrol_json": json.dumps(enrolment),
        "perf_json": json.dumps(perf),
        "subject_json": json.dumps(subject_rows),
        "pass_json": json.dumps(pass_segments),
        "pass_segments": pass_segments,
        "trend_json": json.dumps(trend),
        "subjects": subjects,
    }
    return render(request, "reports/analytics.html", context)


@admin_required
def export(request):
    """Stream a CSV export for one of the catalogued reports."""
    name = request.GET.get("report", "student_marks").strip()
    if name not in REPORT_KEYS:
        name = "student_marks"

    year, semester = _current_period()
    school_class = _selected_class(request)
    label = next((r["name"] for r in REPORT_CATALOG if r["key"] == name), name)

    response = HttpResponse(content_type="text/csv")
    filename = f"{name}-{timezone.localdate():%Y%m%d}.csv"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)

    if name == "student_marks":
        writer.writerow(["Student ID", "Student", "Class", "Subject", "Total", "Percentage", "Grade"])
        marks = published_marks(year=year, semester=semester, school_class=school_class).select_related(
            "student", "result_sheet__subject"
        )
        for mark in marks:
            writer.writerow(
                [
                    mark.student.student_id,
                    mark.student.full_name,
                    mark.result_sheet.school_class.name,
                    mark.result_sheet.subject.name,
                    mark.total,
                    mark.percentage,
                    mark.grade,
                ]
            )

    elif name == "attendance":
        writer.writerow(
            ["Student ID", "Student", "Class", "Present", "Absent", "Late", "Excused", "Total", "Attendance %"]
        )
        students = Student.objects.filter(status="Active")
        if school_class is not None:
            students = students.filter(school_class=school_class)
        for student in students.select_related("school_class"):
            summary = attendance_summary(student)
            writer.writerow(
                [
                    student.student_id,
                    student.full_name,
                    student.school_class.name if student.school_class else f"Grade {student.grade} {student.section}",
                    summary["present"],
                    summary["absent"],
                    summary["late"],
                    summary["excused"],
                    summary["total"],
                    summary["percentage"],
                ]
            )

    else:  # class_rankings
        writer.writerow(["Rank", "Student ID", "Student", "Class", "Average"])
        for row in ranked_students(year, semester, school_class=school_class):
            writer.writerow(
                [
                    row["rank"],
                    row["student"].student_id,
                    row["student"].full_name,
                    row["student"].school_class.name if row["student"].school_class else "",
                    row["average"],
                ]
            )

    log_action(request, "Exported report", "Reports", f"Downloaded the {label} report as CSV.")
    return response
