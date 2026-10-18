"""Business logic for marks, grades, averages, rankings and publication.

Every student-facing read path filters on ``status=approved`` here so that
unpublished marks can never leak through templates or queries.
"""
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Sum

from apps.academics.models import AssessmentComponent, SchoolSettings
from apps.attendance.models import AttendanceRecord

from .models import ResultSheet, SubjectMark

PUBLISHED = ResultSheet.Status.APPROVED

# Attendance weighting used across the school (matches the original design).
ATTENDANCE_WEIGHTS = {"present": Decimal("1"), "late": Decimal("0.5"), "excused": Decimal("1"), "absent": Decimal("0")}


def _pct(value):
    return Decimal(value).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def published_marks(*, student=None, year=None, semester=None, school_class=None):
    """SubjectMark queryset restricted to approved & published sheets only."""
    qs = SubjectMark.objects.filter(result_sheet__status=PUBLISHED)
    if student is not None:
        qs = qs.filter(student=student)
    if year is not None:
        qs = qs.filter(result_sheet__academic_year=year)
    if semester is not None:
        qs = qs.filter(result_sheet__semester=semester)
    if school_class is not None:
        qs = qs.filter(student__school_class=school_class)
    return qs.select_related("student", "result_sheet__subject", "result_sheet__school_class")


def semester_average(student, year=None, semester=None):
    """Mean subject percentage across a student's published sheets."""
    marks = list(published_marks(student=student, year=year, semester=semester))
    if not marks:
        return None
    total = sum((m.percentage for m in marks), Decimal("0"))
    return _pct(total / len(marks))


# ---------------------------------------------------------------------------
# Rankings
# ---------------------------------------------------------------------------
def _rank(values_desc):
    """Assign ranks with the configured tie policy (dense or competition)."""
    policy = SchoolSettings.load().rank_tie_policy
    ranks = {}
    previous = None
    rank = 0
    dense_rank = 0
    for index, value in enumerate(values_desc, start=1):
        if value != previous:
            dense_rank += 1
            rank = dense_rank if policy == "dense" else index
            previous = value
        ranks[index] = rank
    return ranks


def ranked_students(year, semester, *, school_class=None):
    """Return ``[{student, average, rank}]`` sorted by descending average."""
    qs = published_marks(year=year, semester=semester, school_class=school_class)
    qs = qs.annotate(entry_total=Sum("entries__score"))
    max_total = AssessmentComponent.total_max_score() or Decimal("100")

    by_student = {}
    for mark in qs:
        bucket = by_student.setdefault(mark.student_id, {"student": mark.student, "sum": Decimal("0"), "count": 0})
        bucket["sum"] += (mark.entry_total or Decimal("0")) / max_total * Decimal("100")
        bucket["count"] += 1

    rows = []
    for bucket in by_student.values():
        if bucket["count"]:
            rows.append({"student": bucket["student"], "average": _pct(bucket["sum"] / bucket["count"])})

    rows.sort(key=lambda r: (-r["average"], r["student"].full_name))
    ranks = _rank([r["average"] for r in rows])
    for index, row in enumerate(rows, start=1):
        row["rank"] = ranks[index]
    return rows


def student_rank(student, year, semester, *, scope="class"):
    """Rank of a single student within their class or the whole school."""
    school_class = student.school_class if scope == "class" else None
    for row in ranked_students(year, semester, school_class=school_class):
        if row["student"].pk == student.pk:
            return {"rank": row["rank"], "of": len(ranked_students(year, semester, school_class=school_class))}
    return None


def class_average(school_class, year=None, semester=None):
    marks = list(published_marks(year=year, semester=semester, school_class=school_class))
    if not marks:
        return None
    return _pct(sum((m.percentage for m in marks), Decimal("0")) / len(marks))


def subject_performance(year=None, semester=None):
    """Average and pass-rate per subject across published marks."""
    from apps.academics.models import Subject

    pass_mark = SchoolSettings.load().pass_mark or Decimal("50")
    rows = []
    for subject in Subject.objects.all():
        marks = published_marks(year=year, semester=semester).filter(result_sheet__subject=subject)
        values = [m.percentage for m in marks]
        if not values:
            continue
        passing = sum(1 for v in values if v >= pass_mark)
        rows.append(
            {
                "subject": subject,
                "average": _pct(sum(values) / len(values)),
                "count": len(values),
                "pass_rate": _pct(Decimal(passing) / Decimal(len(values)) * 100),
            }
        )
    rows.sort(key=lambda r: r["average"], reverse=True)
    return rows


def pass_rate(year=None, semester=None):
    pass_mark = SchoolSettings.load().pass_mark or Decimal("50")
    values = [m.percentage for m in published_marks(year=year, semester=semester)]
    if not values:
        return {"pass": 0, "fail": 0, "rate": Decimal("0")}
    passing = sum(1 for v in values if v >= pass_mark)
    return {
        "pass": passing,
        "fail": len(values) - passing,
        "rate": _pct(Decimal(passing) / Decimal(len(values)) * 100),
    }


# ---------------------------------------------------------------------------
# Attendance
# ---------------------------------------------------------------------------
def attendance_summary(student, *, date_from=None, date_to=None):
    records = AttendanceRecord.objects.filter(student=student)
    if date_from:
        records = records.filter(session__date__gte=date_from)
    if date_to:
        records = records.filter(session__date__lte=date_to)
    tally = {"present": 0, "absent": 0, "late": 0, "excused": 0}
    weighted = Decimal("0")
    for record in records:
        tally[record.status] = tally.get(record.status, 0) + 1
        weighted += ATTENDANCE_WEIGHTS.get(record.status, Decimal("0"))
    total = sum(tally.values())
    tally["total"] = total
    tally["percentage"] = _pct(weighted / total * 100) if total else Decimal("0")
    return tally
