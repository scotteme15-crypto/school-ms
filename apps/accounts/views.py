"""Authentication, role dashboards, profile, password flows and global search.

Authorisation is enforced here on the server; the templates only decide what to
show. Nothing in this module trusts client input for identity or role.
"""
import json
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.audit.services import log_action

from .forms import LoginForm, ProfileForm, StyledPasswordChangeForm


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def _current_period():
    """Return the configured (academic year, semester) pair, with fallbacks."""
    from apps.academics.models import AcademicYear, SchoolSettings, Semester

    conf = SchoolSettings.load()
    year = conf.current_academic_year or AcademicYear.objects.filter(is_current=True).first() or AcademicYear.objects.first()
    semester = conf.current_semester
    if semester is None and year is not None:
        semester = (
            Semester.objects.filter(academic_year=year, is_current=True).first()
            or Semester.objects.filter(academic_year=year).first()
        )
    return year, semester


def _greeting():
    hour = timezone.localtime().hour
    if hour < 12:
        return "Good morning"
    if hour < 17:
        return "Good afternoon"
    return "Good evening"


def _round(value, places=0):
    if value is None:
        return 0
    return round(float(value), places)


def _throttle_key(request, username):
    ip = request.META.get("REMOTE_ADDR", "unknown")
    return f"login-fail:{ip}:{(username or '').lower()}"


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = LoginForm(request.POST or None)

    if request.method == "POST":
        key = _throttle_key(request, request.POST.get("username", ""))
        attempts = cache.get(key, 0)
        if attempts >= settings.LOGIN_MAX_ATTEMPTS:
            form.add_error(None, "Too many failed attempts. Please wait a few minutes and try again.")
        elif form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )
            if user is None:
                cache.set(key, attempts + 1, settings.LOGIN_LOCKOUT_SECONDS)
                form.add_error(None, "That username and password did not match an active account.")
            elif not user.is_active:
                form.add_error(None, "This account has been deactivated. Contact the registrar.")
            else:
                cache.delete(key)
                login(request, user)
                user.touch_last_seen()
                log_action(request, "Signed in", "Accounts", f"{user.display_name} signed in.")
                if not form.cleaned_data.get("remember"):
                    request.session.set_expiry(0)
                nxt = request.POST.get("next") or request.GET.get("next")
                return redirect(nxt or "dashboard")

    stats = _login_stats()
    return render(
        request,
        "registration/login.html",
        {"form": form, "next": request.GET.get("next", ""), "stats": stats},
    )


def _login_stats():
    from apps.academics.models import SchoolClass
    from apps.students.models import Student
    from apps.teachers.models import Teacher

    return {
        "students": Student.objects.filter(status="Active").count(),
        "teachers": Teacher.objects.count(),
        "classes": SchoolClass.objects.count(),
    }


@require_POST
def logout_view(request):
    if request.user.is_authenticated:
        log_action(request, "Signed out", "Accounts", f"{request.user.display_name} signed out.")
    logout(request)
    messages.success(request, "You have been signed out.")
    return redirect("accounts:login")


# ---------------------------------------------------------------------------
# Dashboard (role dispatch)
# ---------------------------------------------------------------------------
@login_required
def dashboard(request):
    user = request.user
    if user.is_admin_role or user.is_superuser:
        return _render_admin_dashboard(request)
    if user.is_teacher_role:
        return _render_teacher_dashboard(request)
    return _render_student_dashboard(request)


def _render_admin_dashboard(request):
    from apps.academics.models import AssessmentComponent, GRADE_CHOICES, SchoolClass, Subject
    from apps.announcements.models import SchoolEvent
    from apps.attendance.models import AttendanceRecord, AttendanceSession
    from apps.audit.models import AuditLog
    from apps.results.models import Exam, ResultSheet, SubjectMark
    from apps.results.services import PUBLISHED
    from apps.students.models import Student
    from apps.teachers.models import Teacher

    today = timezone.localdate()
    year, semester = _current_period()

    students = Student.objects.all()
    active = students.filter(status="Active")
    teachers = Teacher.objects.all()

    enrol = [{"label": f"G{g}", "value": active.filter(grade=g).count()} for g, _ in GRADE_CHOICES]
    male = active.filter(gender="M").count()
    female = active.filter(gender="F").count()

    latest = AttendanceSession.objects.order_by("-date").values_list("date", flat=True).first()
    if latest:
        recs = AttendanceRecord.objects.filter(session__date=latest)
        att = {
            "date": latest,
            "present": recs.filter(status="present").count(),
            "absent": recs.filter(status="absent").count(),
            "late": recs.filter(status="late").count(),
            "excused": recs.filter(status="excused").count(),
            "total": recs.count(),
        }
    else:
        att = {"date": None, "present": 0, "absent": 0, "late": 0, "excused": 0, "total": 0}

    dates = list(AttendanceSession.objects.values_list("date", flat=True).distinct().order_by("-date")[:10])
    dates.reverse()
    att_series = []
    for day in dates:
        recs = AttendanceRecord.objects.filter(session__date=day)
        total = recs.count()
        present = recs.filter(status__in=["present", "late"]).count()
        att_series.append({"label": day.strftime("%d %b"), "value": round(present / total * 100) if total else 0})

    max_total = AssessmentComponent.total_max_score() or Decimal("100")
    perf = []
    for g, _ in GRADE_CHOICES:
        rows = SubjectMark.objects.filter(result_sheet__status=PUBLISHED, student__grade=g).annotate(
            s=Sum("entries__score")
        )
        values = [float((row.s or 0) / max_total * 100) for row in rows]
        perf.append({"label": f"G{g}", "value": round(sum(values) / len(values)) if values else 0})

    pending = ResultSheet.objects.filter(status=ResultSheet.Status.PENDING).count()
    approved = ResultSheet.objects.filter(status=ResultSheet.Status.APPROVED).count()
    returned = ResultSheet.objects.filter(
        status__in=[ResultSheet.Status.RETURNED, ResultSheet.Status.REJECTED]
    ).count()

    upcoming = Exam.objects.filter(date__gte=today).order_by("date")

    context = {
        "page_title": "Dashboard",
        "greeting": _greeting(),
        "period": {"year": year.name if year else "—", "semester": semester.name if semester else "—"},
        "kpis": {
            "students_active": active.count(),
            "students_total": students.count(),
            "teachers_active": teachers.filter(status="Active").count(),
            "teachers_total": teachers.count(),
            "classes": SchoolClass.objects.count(),
            "subjects": Subject.objects.count(),
            "present_today": att["present"],
            "absent_today": att["absent"],
            "late_today": att["late"],
            "excused_today": att["excused"],
            "att_total": att["total"],
            "att_pct": round(att["present"] / att["total"] * 100) if att["total"] else 0,
            "pending": pending,
            "approved": approved,
            "sheets_total": ResultSheet.objects.count(),
            "exams_upcoming": upcoming.count(),
            "next_exam": upcoming.first(),
        },
        "enrol_json": json.dumps(enrol),
        "gender_json": json.dumps(
            [
                {"label": "Male", "value": male, "color": "var(--brand)"},
                {"label": "Female", "value": female, "color": "var(--brass)"},
            ]
        ),
        "gender_segments": [
            {"label": "Male", "value": male, "color": "var(--brand)"},
            {"label": "Female", "value": female, "color": "var(--brass)"},
        ],
        "att_series_json": json.dumps(att_series),
        "perf_json": json.dumps(perf),
        "sheet_json": json.dumps(
            [
                {"label": "Approved", "value": approved, "color": "var(--ok)"},
                {"label": "Pending", "value": pending, "color": "var(--warn)"},
                {"label": "Sent back", "value": returned, "color": "var(--bad)"},
            ]
        ),
        "sheet_segments": [
            {"label": "Approved", "value": approved, "color": "var(--ok)"},
            {"label": "Pending", "value": pending, "color": "var(--warn)"},
            {"label": "Sent back", "value": returned, "color": "var(--bad)"},
        ],
        "activity": AuditLog.objects.select_related("user")[:7],
        "events": SchoolEvent.objects.filter(date__gte=today)[:6],
    }
    return render(request, "dashboard/admin_dashboard.html", context)


def _render_teacher_dashboard(request):
    from apps.academics.models import SchoolClass, TeachingAssignment
    from apps.announcements.models import Announcement
    from apps.attendance.models import AttendanceSession
    from apps.results.models import ResultSheet
    from apps.timetable.models import DAY_CHOICES, TimetableSlot

    teacher = getattr(request.user, "teacher_profile", None)
    today_name = timezone.localdate().strftime("%A")

    assignments = []
    class_ids = []
    subjects = []
    if teacher:
        assignments = list(
            TeachingAssignment.objects.filter(teacher=teacher).select_related("subject", "school_class")
        )
        class_ids = sorted({a.school_class_id for a in assignments})
        subjects = sorted({a.subject.name for a in assignments if a.subject_id})

    todo = []
    if teacher:
        todo = list(
            ResultSheet.objects.filter(
                teacher=teacher,
                status__in=[ResultSheet.Status.DRAFT, ResultSheet.Status.RETURNED, ResultSheet.Status.REJECTED],
            ).select_related("subject", "school_class", "semester")
        )

    lessons = []
    if teacher:
        lessons = list(
            TimetableSlot.objects.filter(teacher=teacher, day=today_name)
            .select_related("subject", "school_class")
            .order_by("start_time")
        )

    classes = []
    for class_id in class_ids:
        klass = SchoolClass.objects.get(pk=class_id)
        classes.append(
            {
                "name": klass.name,
                "students": klass.students.filter(status="Active").count(),
                "marked_today": AttendanceSession.objects.filter(
                    school_class=klass, date=timezone.localdate()
                ).exists(),
            }
        )

    notices = Announcement.objects.filter(audience__in=["Everyone", "Teachers"])[:5]

    context = {
        "page_title": "Dashboard",
        "greeting": _greeting(),
        "teacher": teacher,
        "today_name": today_name,
        "class_count": len(class_ids),
        "subject_count": len(subjects),
        "todo": todo,
        "lessons": lessons,
        "classes": classes,
        "notices": notices,
        "kpis": {
            "classes": len(class_ids),
            "subjects": len(subjects),
            "todo": len(todo),
            "marked_today": sum(1 for c in classes if c["marked_today"]),
            "class_total": len(classes),
        },
    }
    return render(request, "dashboard/teacher_dashboard.html", context)


def _render_student_dashboard(request):
    from apps.academics.models import GRADE_CHOICES  # noqa: F401  (keeps choices in sync)

    student = getattr(request.user, "student_profile", None)
    if student is None:
        return render(
            request,
            "dashboard/student_dashboard.html",
            {"page_title": "Dashboard", "student": None},
        )

    from apps.announcements.models import Announcement, SchoolEvent  # noqa: F401
    from apps.assignments.models import Assignment
    from apps.results.models import Exam
    from apps.results.services import semester_average, student_rank
    from apps.timetable.models import TimetableSlot
    from apps.attendance.models import AttendanceRecord, AttendanceSession

    year, semester = _current_period()
    average = semester_average(student, year=year, semester=semester)
    class_rank = student_rank(student, year, semester, scope="class") if year and semester else None
    school_rank = student_rank(student, year, semester, scope="school") if year and semester else None

    records = AttendanceRecord.objects.filter(student=student)
    total = records.count()
    present = records.filter(status__in=["present", "late", "excused"]).count()
    att_pct = round(present / total * 100) if total else 0

    today_name = timezone.localdate().strftime("%A")
    lessons = []
    if student.school_class_id:
        lessons = list(
            TimetableSlot.objects.filter(school_class=student.school_class, day=today_name)
            .select_related("subject", "teacher")
            .order_by("start_time")
        )

    from apps.results.services import published_marks

    subjects = []
    for mark in published_marks(student=student, year=year, semester=semester).select_related("result_sheet__subject"):
        subjects.append(
            {
                "subject": mark.result_sheet.subject.name,
                "total": _round(mark.percentage, 1),
                "grade": mark.grade,
            }
        )

    context = {
        "page_title": "Dashboard",
        "greeting": _greeting(),
        "student": student,
        "period": {"year": year.name if year else "—", "semester": semester.name if semester else "—"},
        "subjects": subjects,
        "average": average,
        "class_rank": class_rank,
        "school_rank": school_rank,
        "attendance": {"total": total, "absent": records.filter(status="absent").count(), "pct": att_pct},
        "lessons": lessons,
        "exams": Exam.objects.filter(grade=student.grade, date__gte=timezone.localdate()).order_by("date")[:4],
        "assignments": Assignment.objects.filter(
            school_class=student.school_class, due_date__gte=timezone.localdate()
        ).order_by("due_date")[:4]
        if student.school_class_id
        else [],
        "notices": Announcement.objects.filter(
            audience__in=["Everyone", "Students", f"Grade {student.grade}"]
        )[:4],
    }
    return render(request, "dashboard/student_dashboard.html", context)


# ---------------------------------------------------------------------------
# Profile & password
# ---------------------------------------------------------------------------
@login_required
def profile(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        log_action(request, "Updated profile", "Accounts", "Profile details changed.")
        messages.success(request, "Your profile has been updated.")
        return redirect("accounts:profile")
    return render(
        request,
        "accounts/profile.html",
        {"form": form, "page_title": "My profile"},
    )


@login_required
def password_change(request):
    form = StyledPasswordChangeForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        log_action(request, "Changed password", "Accounts", "Account password updated.")
        messages.success(request, "Your password has been updated.")
        return redirect("accounts:profile")
    return render(
        request,
        "registration/password_change_form.html",
        {"form": form, "page_title": "Change password"},
    )


# ---------------------------------------------------------------------------
# Global search (command palette)
# ---------------------------------------------------------------------------
@login_required
def search(request):
    term = request.GET.get("q", "").strip()
    results = []
    if len(term) >= 2:
        user = request.user
        from apps.academics.models import SchoolClass, Subject
        from apps.announcements.models import Announcement

        if user.is_admin_role or user.is_superuser:
            from apps.students.models import Student
            from apps.teachers.models import Teacher

            for student in Student.objects.filter(
                Q(first_name__icontains=term) | Q(last_name__icontains=term) | Q(student_id__icontains=term)
            )[:5]:
                results.append(
                    {
                        "label": student.full_name,
                        "sub": f"{student.student_id} · Grade {student.grade} {student.section}",
                        "kind": "Student",
                        "icon": "user",
                        "url": reverse("students:list") + f"?q={term}",
                    }
                )
            for teacher in Teacher.objects.filter(
                Q(name__icontains=term) | Q(teacher_id__icontains=term)
            )[:5]:
                results.append(
                    {
                        "label": teacher.name,
                        "sub": f"{teacher.teacher_id} · {teacher.department}",
                        "kind": "Teacher",
                        "icon": "cap",
                        "url": reverse("teachers:list") + f"?q={term}",
                    }
                )
            for klass in SchoolClass.objects.filter(
                Q(section__icontains=term) | Q(room__icontains=term)
            )[:5]:
                results.append(
                    {
                        "label": klass.name,
                        "sub": f"{klass.student_count} students",
                        "kind": "Class",
                        "icon": "school",
                        "url": reverse("academics:class_list"),
                    }
                )
        elif user.is_teacher_role:
            from apps.students.models import Student

            for student in Student.objects.filter(
                Q(first_name__icontains=term) | Q(last_name__icontains=term) | Q(student_id__icontains=term)
            )[:5]:
                results.append(
                    {
                        "label": student.full_name,
                        "sub": f"{student.student_id} · Grade {student.grade} {student.section}",
                        "kind": "Student",
                        "icon": "user",
                        "url": reverse("teachers:students") + f"?q={term}",
                    }
                )

        for subject in Subject.objects.filter(Q(name__icontains=term) | Q(code__icontains=term))[:5]:
            results.append(
                {
                    "label": subject.name,
                    "sub": f"{subject.full_code} · {subject.department}",
                    "kind": "Subject",
                    "icon": "book",
                    "url": reverse("academics:subject_list"),
                }
            )
        for notice in Announcement.objects.filter(title__icontains=term)[:4]:
            results.append(
                {
                    "label": notice.title,
                    "sub": f"{notice.audience} · {notice.date:%d %b %Y}",
                    "kind": "Notice",
                    "icon": "mega",
                    "url": reverse("announcements:list"),
                }
            )

    return JsonResponse({"results": results[:20]})


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------
def _error(request, status, title, message, exception=None):
    return render(
        request,
        f"errors/{status}.html",
        {"page_title": title, "status_code": status, "title": title, "message": message},
        status=status,
    )


def error_403(request, exception=None):
    return _error(request, 403, "Access denied", "Your account does not have access to this area.")


def error_404(request, exception=None):
    return _error(request, 404, "Page not found", "The link may be out of date. Pick a section from the sidebar.")


def error_500(request):
    return _error(request, 500, "Something went wrong", "An unexpected error occurred. Please try again.")
