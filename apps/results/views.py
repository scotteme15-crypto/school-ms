"""Views for result sheets, the marks-approval workflow and student reports.

Security: teachers only ever touch their own sheets, students only ever read
their own published results. Every student-facing read goes through
``apps.results.services`` which filters on ``status=approved``.
"""
import json
from decimal import Decimal

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.academics.models import (
    AcademicYear,
    GradingBand,
    SchoolClass,
    SchoolSettings,
    Semester,
    Subject,
    grade_letter,
    grade_point,
    grade_remark,
)
from apps.audit.services import log_action
from apps.notifications.models import Notification
from apps.notifications.services import notify_role, notify_user
from apps.students.models import Student

from .forms import (
    MarksEntryForm,
    ResultSheetForm,
    bands_payload,
    build_marks_initial,
    components_payload,
    default_components,
    ensure_subject_marks,
)
from .models import EXAM_TYPE_CHOICES, ResultSheet
from .services import (
    attendance_summary,
    published_marks,
    semester_average,
    student_rank,
)

STATUS = ResultSheet.Status
EDITABLE = (STATUS.DRAFT, STATUS.RETURNED, STATUS.REJECTED)
PAGE_SIZE = 20


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _current_period():
    conf = SchoolSettings.load()
    year = conf.current_academic_year or AcademicYear.objects.filter(is_current=True).first() or AcademicYear.objects.first()
    semester = conf.current_semester
    if semester is None and year is not None:
        semester = (
            Semester.objects.filter(academic_year=year, is_current=True).first()
            or Semester.objects.filter(academic_year=year).first()
        )
    return year, semester


def _teacher_of(user):
    return getattr(user, "teacher_profile", None)


def _is_admin(user):
    return user.is_admin_role or user.is_superuser


def _owned_sheet(user, pk, qs=None):
    """Fetch a sheet, enforcing teacher ownership; 404 on a foreign pk."""
    qs = qs or ResultSheet.objects.all()
    qs = qs.select_related("subject", "school_class", "semester", "academic_year", "teacher")
    if _is_admin(user):
        return get_object_or_404(qs, pk=pk)
    teacher = _teacher_of(user)
    if teacher is None:
        raise Http404("No teacher profile.")
    return get_object_or_404(qs, pk=pk, teacher=teacher)


def _sheet_rows(sheet):
    components = default_components()
    rows = []
    for mark in sheet.marks.select_related("student").prefetch_related("entries"):
        breakdown = {entry.component_id: entry.score for entry in mark.entries.all()}
        rows.append(
            {
                "student": mark.student,
                "breakdown": breakdown,
                "total": mark.total,
                "percentage": mark.percentage,
                "grade": mark.grade,
                "remark": mark.remark,
            }
        )
    return components, rows


# ---------------------------------------------------------------------------
# Result sheets
# ---------------------------------------------------------------------------
def sheet_list(request):
    """Teacher: their own sheets. Admin: every sheet, with filters."""
    user = request.user
    if not (user.is_authenticated and (user.is_admin_role or user.is_teacher_role or user.is_superuser)):
        raise PermissionDenied("Your account does not have access to this area.")

    is_admin = _is_admin(user)
    teacher = _teacher_of(user)
    qs = ResultSheet.objects.select_related(
        "subject", "school_class", "semester", "academic_year", "teacher"
    )

    if not is_admin:
        qs = qs.filter(teacher=teacher) if teacher else qs.none()

    # Create a new draft sheet.
    if request.method == "POST":
        if not is_admin and teacher is None:
            messages.error(request, "Your login is not linked to a teacher profile.")
            return redirect("results:list")
        form = ResultSheetForm(request.POST, lock_teacher=None if is_admin else teacher)
        if form.is_valid():
            sheet = form.save(commit=False)
            if not is_admin:
                sheet.teacher = teacher
            sheet.status = STATUS.DRAFT
            sheet.save()
            log_action(request, "Created result sheet", "Results", f"Created {sheet.context_label()}.")
            messages.success(request, "Result sheet created. You can now enter marks.")
            return redirect(f"{reverse('results:entry')}?sheet={sheet.pk}")
        messages.error(request, "Please correct the errors in the new sheet form.")
    else:
        form = ResultSheetForm(lock_teacher=None if is_admin else teacher)

    status = request.GET.get("status", "").strip()
    class_id = request.GET.get("class", "").strip()
    subject_id = request.GET.get("subject", "").strip()
    if status:
        qs = qs.filter(status=status)
    if class_id.isdigit():
        qs = qs.filter(school_class_id=class_id)
    if subject_id.isdigit():
        qs = qs.filter(subject_id=subject_id)

    page_obj = Paginator(qs, PAGE_SIZE).get_page(request.GET.get("page"))

    counts = {
        "total": ResultSheet.objects.count(),
        "pending": ResultSheet.objects.filter(status=STATUS.PENDING).count(),
        "approved": ResultSheet.objects.filter(status=STATUS.APPROVED).count(),
        "back": ResultSheet.objects.filter(status__in=[STATUS.RETURNED, STATUS.REJECTED]).count(),
    }
    context = {
        "page_title": "Results",
        "page_obj": page_obj,
        "sheets": page_obj.object_list,
        "form": form,
        "is_admin": is_admin,
        "teacher": teacher,
        "statuses": STATUS.choices,
        "exam_types": EXAM_TYPE_CHOICES,
        "classes": SchoolClass.objects.all(),
        "subjects": Subject.objects.all(),
        "filters": {"status": status, "class_id": class_id, "subject_id": subject_id},
        "counts": counts,
    }
    return render(request, "results/list.html", context)


def marks_entry(request):
    """Enter or edit the marks for one of the teacher's editable sheets."""
    user = request.user
    if not (user.is_authenticated and (user.is_admin_role or user.is_teacher_role or user.is_superuser)):
        raise PermissionDenied("Your account does not have access to this area.")
    if _is_admin(user):
        return redirect("results:list")

    teacher = _teacher_of(user)
    if teacher is None:
        messages.error(request, "Your login is not linked to a teacher profile.")
        return redirect("results:list")

    sheet_id = (request.POST.get("sheet") or request.GET.get("sheet") or "").strip()
    if not sheet_id.isdigit():
        messages.info(request, "Choose one of your result sheets to enter marks.")
        return redirect("results:list")

    sheet = get_object_or_404(
        ResultSheet.objects.select_related("subject", "school_class", "semester", "academic_year", "teacher"),
        pk=sheet_id,
        teacher=teacher,
    )
    if not sheet.is_editable:
        messages.warning(request, "This sheet has been submitted and can no longer be edited.")
        return redirect("results:sheet_detail", pk=sheet.pk)

    ensure_subject_marks(sheet)
    subject_marks = list(
        sheet.marks.select_related("student").prefetch_related("entries").order_by(
            "student__first_name", "student__last_name"
        )
    )
    components = default_components()

    action = request.POST.get("action", "save")

    if request.method == "POST":
        form = MarksEntryForm(request.POST, sheet=sheet, subject_marks=subject_marks, components=components)
        if form.is_valid():
            with transaction.atomic():
                form.save()
                if action == "submit":
                    sheet.status = STATUS.PENDING
                    sheet.submitted_at = timezone.now()
                    sheet.reason = ""
                    sheet.save(update_fields=["status", "submitted_at", "reason", "updated_at"])
            if action == "submit":
                notify_role(
                    "admin",
                    f"Result sheet submitted — {sheet.context_label()}",
                    f"{teacher.name} submitted marks for approval.",
                    kind=Notification.Kind.RESULT,
                    url=reverse("results:approvals"),
                )
                log_action(
                    request, "Submitted result sheet", "Results",
                    f"{sheet.context_label()} submitted for approval.",
                )
                messages.success(request, "Marks saved and the sheet was submitted for approval.")
                return redirect("results:sheet_detail", pk=sheet.pk)
            log_action(request, "Saved marks", "Results", f"Updated marks on {sheet.context_label()}.")
            messages.success(request, "Marks saved as draft.")
            return redirect(f"{reverse('results:entry')}?sheet={sheet.pk}")
        messages.error(request, "Some marks could not be saved. Please check the highlighted fields.")
    else:
        form = MarksEntryForm(
            sheet=sheet,
            subject_marks=subject_marks,
            components=components,
            initial=build_marks_initial(subject_marks),
        )

    rows = form.rows()
    context = {
        "page_title": f"Marks entry — {sheet.subject.name}",
        "sheet": sheet,
        "components": components,
        "rows": rows,
        "form": form,
        "max_total": sum((c.max_score for c in components), Decimal("0")),
        "components_json": json.dumps(components_payload(components)),
        "bands_json": json.dumps(bands_payload(GradingBand.objects.all())),
    }
    return render(request, "results/entry.html", context)


def sheet_detail(request, pk):
    """Read a sheet, with the workflow actions the viewer is allowed to take."""
    sheet = _owned_sheet(request.user, pk)
    components, rows = _sheet_rows(sheet)
    context = {
        "page_title": f"Result sheet — {sheet.subject.name}",
        "sheet": sheet,
        "components": components,
        "rows": rows,
        "is_admin": _is_admin(request.user),
        "can_edit": sheet.is_editable and not _is_admin(request.user),
        "can_decide": _is_admin(request.user) and sheet.status == STATUS.PENDING,
    }
    return render(request, "results/sheet_detail.html", context)


def approvals(request):
    """Admin approval queue: pending sheets plus recently decided ones."""
    user = request.user
    if not (user.is_authenticated and _is_admin(user)):
        raise PermissionDenied("Your account does not have access to this area.")

    pending = list(
        ResultSheet.objects.filter(status=STATUS.PENDING)
        .select_related("subject", "school_class", "semester", "teacher")
        .order_by("submitted_at", "id")
    )
    decided = list(
        ResultSheet.objects.filter(status__in=[STATUS.APPROVED, STATUS.RETURNED, STATUS.REJECTED])
        .select_related("subject", "school_class", "teacher", "decided_by")
        .order_by("-decided_at")[:15]
    )
    context = {
        "page_title": "Result approvals",
        "pending": pending,
        "decided": decided,
        "pending_count": len(pending),
    }
    return render(request, "results/approvals.html", context)


@require_POST
def submit(request, pk):
    sheet = _owned_sheet(request.user, pk)
    if _is_admin(request.user):
        raise PermissionDenied("Only the owning teacher may submit a sheet.")
    if not sheet.is_editable:
        messages.error(request, "This sheet is not editable and cannot be submitted.")
        return redirect("results:sheet_detail", pk=sheet.pk)

    with transaction.atomic():
        sheet.status = STATUS.PENDING
        sheet.submitted_at = timezone.now()
        sheet.reason = ""
        sheet.save(update_fields=["status", "submitted_at", "reason", "updated_at"])

    notify_role(
        "admin",
        f"Result sheet submitted — {sheet.context_label()}",
        "A result sheet is waiting for approval.",
        kind=Notification.Kind.RESULT,
        url=reverse("results:approvals"),
    )
    log_action(request, "Submitted result sheet", "Results", f"{sheet.context_label()} submitted for approval.")
    messages.success(request, "Sheet submitted for approval.")
    return redirect("results:sheet_detail", pk=sheet.pk)


@require_POST
def approve(request, pk):
    user = request.user
    if not (user.is_authenticated and _is_admin(user)):
        raise PermissionDenied("Your account does not have access to this area.")
    sheet = get_object_or_404(ResultSheet.objects.select_related("teacher"), pk=pk)
    if sheet.status != STATUS.PENDING:
        messages.error(request, "Only a submitted sheet can be approved.")
        return redirect("results:sheet_detail", pk=sheet.pk)

    with transaction.atomic():
        sheet.status = STATUS.APPROVED
        sheet.reason = ""
        sheet.decided_at = timezone.now()
        sheet.decided_by = user
        sheet.save(update_fields=["status", "reason", "decided_at", "decided_by", "updated_at"])

    if sheet.teacher and sheet.teacher.user:
        notify_user(
            sheet.teacher.user,
            f"Results approved — {sheet.context_label()}",
            "Your result sheet has been approved and published to students.",
            kind=Notification.Kind.RESULT,
            url=reverse("results:sheet_detail", args=[sheet.pk]),
        )
    log_action(request, "Approved result sheet", "Results", f"{sheet.context_label()} approved and published.")
    messages.success(request, "Sheet approved and published to students.")
    return redirect("results:approvals")


@require_POST
def return_sheet(request, pk):
    """Return a pending sheet for correction, or reject it outright."""
    user = request.user
    if not (user.is_authenticated and _is_admin(user)):
        raise PermissionDenied("Your account does not have access to this area.")
    sheet = get_object_or_404(ResultSheet.objects.select_related("teacher"), pk=pk)

    decision = request.POST.get("decision", STATUS.RETURNED)
    if decision not in (STATUS.RETURNED, STATUS.REJECTED):
        decision = STATUS.RETURNED
    reason = request.POST.get("reason", "").strip()
    if not reason:
        messages.error(request, "Please give a reason so the teacher knows what to correct.")
        return redirect("results:sheet_detail", pk=sheet.pk)
    if sheet.status != STATUS.PENDING:
        messages.error(request, "Only a submitted sheet can be returned or rejected.")
        return redirect("results:sheet_detail", pk=sheet.pk)

    with transaction.atomic():
        sheet.status = decision
        sheet.reason = reason
        sheet.decided_at = timezone.now()
        sheet.decided_by = user
        sheet.save(update_fields=["status", "reason", "decided_at", "decided_by", "updated_at"])

    if sheet.teacher and sheet.teacher.user:
        notify_user(
            sheet.teacher.user,
            f"Result sheet {sheet.get_status_display().lower()} — {sheet.context_label()}",
            reason,
            kind=Notification.Kind.RESULT,
            url=reverse("results:sheet_detail", args=[sheet.pk]),
        )
    log_action(request, "Returned result sheet", "Results", f"{sheet.context_label()} — {sheet.get_status_display()}.")
    messages.success(request, f"Sheet marked as {sheet.get_status_display().lower()}.")
    return redirect("results:approvals")


@require_POST
def delete(request, pk):
    user = request.user
    if not (user.is_authenticated and (user.is_admin_role or user.is_teacher_role or user.is_superuser)):
        raise PermissionDenied("Your account does not have access to this area.")
    sheet = _owned_sheet(user, pk)
    if not _is_admin(user) and not sheet.is_editable:
        messages.error(request, "A submitted sheet cannot be deleted.")
        return redirect("results:sheet_detail", pk=sheet.pk)
    label = sheet.context_label()
    sheet.delete()
    log_action(request, "Deleted result sheet", "Results", f"Deleted {label}.")
    messages.success(request, "Result sheet deleted.")
    return redirect("results:list")


# ---------------------------------------------------------------------------
# Student-facing views (published marks only)
# ---------------------------------------------------------------------------
def my_results(request):
    """A student's own published marks (never a draft or pending sheet)."""
    user = request.user
    if not (user.is_authenticated and (user.is_student_role or user.is_superuser)):
        raise PermissionDenied("Your account does not have access to this area.")

    student = getattr(user, "student_profile", None)
    if student is None:
        return render(
            request,
            "results/my_results.html",
            {"page_title": "My results", "student": None, "subjects": [], "average": None, "rank": None},
        )

    year, semester = _current_period()
    subjects = []
    for mark in published_marks(student=student, year=year, semester=semester).select_related(
        "result_sheet__subject"
    ):
        subjects.append(
            {
                "subject": mark.result_sheet.subject.name,
                "exam_type": mark.result_sheet.exam_type,
                "total": mark.total,
                "percentage": mark.percentage,
                "grade": mark.grade,
                "grade_point": mark.grade_point,
                "remark": mark.remark,
            }
        )
    subjects.sort(key=lambda s: s["subject"])
    average = semester_average(student, year=year, semester=semester)
    rank = student_rank(student, year, semester, scope="class") if year and semester else None
    context = {
        "page_title": "My results",
        "student": student,
        "period": {"year": year.name if year else "—", "semester": semester.name if semester else "—"},
        "subjects": subjects,
        "average": average,
        "rank": rank,
        "show_school_rank": SchoolSettings.load().show_school_rank,
    }
    return render(request, "results/my_results.html", context)


def report_card(request, pk):
    """Printable report card. Students may only open their own."""
    user = request.user
    if not user.is_authenticated:
        raise PermissionDenied("Sign in first.")
    student = get_object_or_404(Student, pk=pk)
    if user.is_student_role:
        own = getattr(user, "student_profile", None)
        if own is None or own.pk != student.pk:
            raise Http404("Not your report card.")
    elif not (user.is_admin_role or user.is_teacher_role or user.is_superuser):
        raise PermissionDenied("Your account does not have access to this area.")

    year, semester = _current_period()
    subjects = []
    total_points = 0
    for mark in published_marks(student=student, year=year, semester=semester).select_related(
        "result_sheet__subject"
    ):
        point = mark.grade_point
        total_points += point or 0
        subjects.append(
            {
                "subject": mark.result_sheet.subject.name,
                "exam_type": mark.result_sheet.exam_type,
                "total": mark.total,
                "percentage": mark.percentage,
                "grade": mark.grade,
                "grade_point": point,
                "remark": grade_remark(mark.percentage),
            }
        )
    subjects.sort(key=lambda s: s["subject"])

    average = semester_average(student, year=year, semester=semester)
    rank = student_rank(student, year, semester, scope="class") if year and semester else None
    context = {
        "page_title": f"Report card — {student.full_name}",
        "student": student,
        "period": {"year": year.name if year else "—", "semester": semester.name if semester else "—"},
        "subjects": subjects,
        "average": average,
        "rank": rank,
        "total_points": total_points,
        "overall_grade": grade_letter(average) if average is not None else "—",
        "overall_remark": grade_remark(average) if average is not None else "",
        "attendance": attendance_summary(student),
        "settings": SchoolSettings.load(),
        "points": grade_point(average) if average is not None else None,
    }
    return render(request, "results/report_card.html", context)
