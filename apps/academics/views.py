"""Server-rendered views for school structure, exams, grading and settings.

Authorisation is enforced here on the server. Read-only listings are open to
staff where it makes sense; every create / edit / delete action is admin-only.
"""
import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, ProtectedError, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.permissions import admin_required, staff_required
from apps.audit.services import log_action
from apps.results.models import EXAM_TYPE_CHOICES, Exam

from .forms import (
    AcademicYearForm,
    AssessmentComponentForm,
    ExamForm,
    GradingBandForm,
    SchoolClassForm,
    SchoolSettingsForm,
    SemesterForm,
    SubjectForm,
    TeachingAssignmentForm,
)
from .models import (
    DEPARTMENTS,
    GRADE_CHOICES,
    SECTION_CHOICES,
    AcademicYear,
    AssessmentComponent,
    GradingBand,
    SchoolClass,
    SchoolSettings,
    Semester,
    Subject,
    TeachingAssignment,
    weights_are_consistent,
)

PER_PAGE = 20


def _paginate(request, queryset, per_page=PER_PAGE):
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get("page"))


# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------
@staff_required
def class_list(request):
    qs = (
        SchoolClass.objects.select_related("academic_year", "homeroom_teacher")
        .annotate(active_count=Count("students", filter=Q(students__status="Active")))
        .order_by("grade", "section")
    )
    q = request.GET.get("q", "").strip()
    grade = request.GET.get("grade", "").strip()
    section = request.GET.get("section", "").strip()
    if q:
        qs = qs.filter(Q(room__icontains=q) | Q(homeroom_teacher__name__icontains=q))
    if grade:
        qs = qs.filter(grade=grade)
    if section:
        qs = qs.filter(section=section)

    context = {
        "page_title": "Classes",
        "page_obj": _paginate(request, qs),
        "q": q,
        "grade": grade,
        "section": section,
        "grade_choices": GRADE_CHOICES,
        "section_choices": SECTION_CHOICES,
    }
    return render(request, "academics/class_list.html", context)


@admin_required
def class_create(request):
    form = SchoolClassForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        log_action(request, "Created class", "Academics", f"Class {obj.name} created.")
        messages.success(request, f"Class {obj.name} has been created.")
        return redirect("academics:class_list")
    return render(
        request,
        "academics/class_form.html",
        {"page_title": "New class", "form": form, "is_edit": False},
    )


@admin_required
def class_edit(request, pk):
    obj = get_object_or_404(SchoolClass, pk=pk)
    form = SchoolClassForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        log_action(request, "Updated class", "Academics", f"Class {obj.name} updated.")
        messages.success(request, f"Class {obj.name} has been updated.")
        return redirect("academics:class_list")
    return render(
        request,
        "academics/class_form.html",
        {"page_title": f"Edit {obj.name}", "form": form, "object": obj, "is_edit": True},
    )


@admin_required
def class_delete(request, pk):
    obj = get_object_or_404(SchoolClass, pk=pk)
    if request.method == "POST":
        label = obj.name
        obj.delete()
        log_action(request, "Deleted class", "Academics", f"Class {label} deleted.")
        messages.success(request, f"Class {label} has been deleted.")
        return redirect("academics:class_list")
    return render(
        request,
        "academics/class_confirm_delete.html",
        {"page_title": "Delete class", "object": obj},
    )


# ---------------------------------------------------------------------------
# Subjects
# ---------------------------------------------------------------------------
@staff_required
def subject_list(request):
    qs = Subject.objects.select_related("teacher").order_by("grade", "name")
    q = request.GET.get("q", "").strip()
    grade = request.GET.get("grade", "").strip()
    department = request.GET.get("department", "").strip()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(code__icontains=q))
    if grade:
        qs = qs.filter(grade=grade)
    if department:
        qs = qs.filter(department=department)

    context = {
        "page_title": "Subjects",
        "page_obj": _paginate(request, qs),
        "q": q,
        "grade": grade,
        "department": department,
        "grade_choices": GRADE_CHOICES,
        "departments": DEPARTMENTS,
    }
    return render(request, "academics/subject_list.html", context)


@admin_required
def subject_create(request):
    form = SubjectForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        log_action(request, "Created subject", "Academics", f"Subject {obj} created.")
        messages.success(request, f"Subject {obj.name} has been created.")
        return redirect("academics:subject_list")
    return render(
        request,
        "academics/subject_form.html",
        {"page_title": "New subject", "form": form, "is_edit": False},
    )


@admin_required
def subject_edit(request, pk):
    obj = get_object_or_404(Subject, pk=pk)
    form = SubjectForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        log_action(request, "Updated subject", "Academics", f"Subject {obj} updated.")
        messages.success(request, f"Subject {obj.name} has been updated.")
        return redirect("academics:subject_list")
    return render(
        request,
        "academics/subject_form.html",
        {"page_title": f"Edit {obj.name}", "form": form, "object": obj, "is_edit": True},
    )


@admin_required
def subject_delete(request, pk):
    obj = get_object_or_404(Subject, pk=pk)
    if request.method == "POST":
        label = str(obj)
        obj.delete()
        log_action(request, "Deleted subject", "Academics", f"Subject {label} deleted.")
        messages.success(request, f"Subject {obj.name} has been deleted.")
        return redirect("academics:subject_list")
    return render(
        request,
        "academics/subject_confirm_delete.html",
        {"page_title": "Delete subject", "object": obj},
    )


# ---------------------------------------------------------------------------
# Exams (results.Exam)
# ---------------------------------------------------------------------------
@login_required
def exam_list(request):
    user = request.user
    qs = Exam.objects.select_related("subject", "academic_year", "semester").order_by("date", "start_time")
    if user.is_student_role:
        student = getattr(user, "student_profile", None)
        qs = qs.filter(grade=student.grade) if student else qs.none()
    elif user.is_teacher_role:
        teacher = getattr(user, "teacher_profile", None)
        grades = (
            TeachingAssignment.objects.filter(teacher=teacher).values_list("school_class__grade", flat=True)
            if teacher
            else []
        )
        qs = qs.filter(grade__in=list(grades))

    q = request.GET.get("q", "").strip()
    grade = request.GET.get("grade", "").strip()
    exam_type = request.GET.get("exam_type", "").strip()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(room__icontains=q) | Q(subject__name__icontains=q))
    if grade:
        qs = qs.filter(grade=grade)
    if exam_type:
        qs = qs.filter(exam_type=exam_type)

    context = {
        "page_title": "Exams",
        "page_obj": _paginate(request, qs),
        "q": q,
        "grade": grade,
        "exam_type": exam_type,
        "grade_choices": GRADE_CHOICES,
        "exam_type_choices": EXAM_TYPE_CHOICES,
    }
    return render(request, "academics/exam_list.html", context)


@admin_required
def exam_create(request):
    form = ExamForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        log_action(request, "Scheduled exam", "Academics", f"Exam {obj} scheduled.")
        messages.success(request, f"Exam “{obj.name}” has been scheduled.")
        return redirect("academics:exam_list")
    return render(
        request,
        "academics/exam_form.html",
        {"page_title": "Schedule exam", "form": form, "is_edit": False},
    )


@admin_required
def exam_edit(request, pk):
    obj = get_object_or_404(Exam, pk=pk)
    form = ExamForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        log_action(request, "Updated exam", "Academics", f"Exam {obj} updated.")
        messages.success(request, f"Exam “{obj.name}” has been updated.")
        return redirect("academics:exam_list")
    return render(
        request,
        "academics/exam_form.html",
        {"page_title": f"Edit {obj.name}", "form": form, "object": obj, "is_edit": True},
    )


@admin_required
def exam_delete(request, pk):
    obj = get_object_or_404(Exam, pk=pk)
    if request.method == "POST":
        label = str(obj)
        obj.delete()
        log_action(request, "Deleted exam", "Academics", f"Exam {label} deleted.")
        messages.success(request, "The exam has been deleted.")
        return redirect("academics:exam_list")
    return render(
        request,
        "academics/exam_confirm_delete.html",
        {"page_title": "Delete exam", "object": obj},
    )


# ---------------------------------------------------------------------------
# Academic years & semesters
# ---------------------------------------------------------------------------
@admin_required
def year_list(request):
    qs = AcademicYear.objects.annotate(semester_count=Count("semesters")).order_by("-name")
    return render(
        request,
        "academics/year_list.html",
        {"page_title": "Academic years", "page_obj": _paginate(request, qs)},
    )


@admin_required
def year_create(request):
    form = AcademicYearForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        log_action(request, "Created academic year", "Academics", f"Academic year {obj.name} created.")
        messages.success(request, f"Academic year {obj.name} has been created.")
        return redirect("academics:year_list")
    return render(
        request,
        "academics/year_form.html",
        {"page_title": "New academic year", "form": form, "is_edit": False},
    )


@admin_required
def year_edit(request, pk):
    obj = get_object_or_404(AcademicYear, pk=pk)
    form = AcademicYearForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        log_action(request, "Updated academic year", "Academics", f"Academic year {obj.name} updated.")
        messages.success(request, f"Academic year {obj.name} has been updated.")
        return redirect("academics:year_list")
    return render(
        request,
        "academics/year_form.html",
        {"page_title": f"Edit {obj.name}", "form": form, "object": obj, "is_edit": True},
    )


@admin_required
def semester_list(request):
    qs = Semester.objects.select_related("academic_year").order_by("-academic_year__name", "order")
    return render(
        request,
        "academics/semester_list.html",
        {"page_title": "Semesters", "page_obj": _paginate(request, qs)},
    )


@admin_required
def semester_create(request):
    form = SemesterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        log_action(request, "Created semester", "Academics", f"Semester {obj} created.")
        messages.success(request, f"Semester “{obj}” has been created.")
        return redirect("academics:semester_list")
    return render(
        request,
        "academics/semester_form.html",
        {"page_title": "New semester", "form": form, "is_edit": False},
    )


# ---------------------------------------------------------------------------
# Grading bands & assessment components
# ---------------------------------------------------------------------------
@admin_required
def grading(request):
    edit_obj = None
    if request.method == "POST":
        action = request.POST.get("action", "save")
        band_id = request.POST.get("band_id") or None
        instance = GradingBand.objects.filter(pk=band_id).first() if band_id else None
        if action == "delete" and instance:
            label = str(instance)
            instance.delete()
            log_action(request, "Deleted grading band", "Academics", f"Grading band {label} deleted.")
            messages.success(request, f"Grading band {label} has been deleted.")
            return redirect("academics:grading")
        form = GradingBandForm(request.POST, instance=instance, prefix="band")
        if form.is_valid():
            obj = form.save()
            verb = "Updated" if instance else "Added"
            log_action(request, f"{verb} grading band", "Academics", f"Grading band {obj.letter} ≥ {obj.min_score}.")
            messages.success(request, f"Grading band {obj.letter} has been saved.")
            if request.POST.get("next") == "settings":
                return redirect("academics:settings")
            return redirect("academics:grading")
        messages.error(request, "Please correct the highlighted fields.")
        edit_obj = instance
        add_form = form
    else:
        edit_id = request.GET.get("edit")
        if edit_id:
            edit_obj = GradingBand.objects.filter(pk=edit_id).first()
        add_form = GradingBandForm(instance=edit_obj, prefix="band")

    context = {
        "page_title": "Grading scale",
        "bands": GradingBand.objects.all(),
        "form": add_form,
        "edit_obj": edit_obj,
    }
    return render(request, "academics/grading.html", context)


@admin_required
def components(request):
    edit_obj = None
    if request.method == "POST":
        action = request.POST.get("action", "save")
        comp_id = request.POST.get("component_id") or None
        instance = AssessmentComponent.objects.filter(pk=comp_id).first() if comp_id else None
        if action == "delete" and instance:
            label = instance.label
            try:
                instance.delete()
            except ProtectedError:
                messages.error(request, f"“{label}” is in use by recorded marks and cannot be deleted.")
                return redirect("academics:components")
            log_action(request, "Deleted assessment component", "Academics", f"Component {label} deleted.")
            messages.success(request, f"Component “{label}” has been deleted.")
            return redirect("academics:components")
        form = AssessmentComponentForm(request.POST, instance=instance, prefix="comp")
        if form.is_valid():
            obj = form.save()
            verb = "Updated" if instance else "Added"
            log_action(request, f"{verb} assessment component", "Academics", f"Component {obj.label} ({obj.weight_percent}%).")
            messages.success(request, f"Component “{obj.label}” has been saved.")
            if request.POST.get("next") == "settings":
                return redirect("academics:settings")
            return redirect("academics:components")
        messages.error(request, "Please correct the highlighted fields.")
        edit_obj = instance
        add_form = form
    else:
        edit_id = request.GET.get("edit")
        if edit_id:
            edit_obj = AssessmentComponent.objects.filter(pk=edit_id).first()
        add_form = AssessmentComponentForm(instance=edit_obj, prefix="comp")

    context = {
        "page_title": "Assessment components",
        "components": AssessmentComponent.objects.all(),
        "form": add_form,
        "edit_obj": edit_obj,
        "weights_total": AssessmentComponent.weights_total(),
        "weights_ok": weights_are_consistent(),
    }
    return render(request, "academics/components.html", context)


# ---------------------------------------------------------------------------
# Teaching assignments
# ---------------------------------------------------------------------------
@staff_required
def assignment_list(request):
    qs = TeachingAssignment.objects.select_related("teacher", "subject", "school_class", "academic_year")
    q = request.GET.get("q", "").strip()
    class_id = request.GET.get("class", "").strip()
    if q:
        qs = qs.filter(
            Q(teacher__name__icontains=q) | Q(subject__name__icontains=q) | Q(subject__code__icontains=q)
        )
    if class_id:
        qs = qs.filter(school_class_id=class_id)
    context = {
        "page_title": "Teaching assignments",
        "page_obj": _paginate(request, qs),
        "q": q,
        "class_id": class_id,
        "classes": SchoolClass.objects.all(),
    }
    return render(request, "academics/assignment_list.html", context)


@admin_required
def assignment_create(request):
    form = TeachingAssignmentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        log_action(request, "Created teaching assignment", "Academics", str(obj))
        messages.success(request, "The teaching assignment has been created.")
        return redirect("academics:assignment_list")
    return render(
        request,
        "academics/assignment_form.html",
        {"page_title": "New teaching assignment", "form": form},
    )


@admin_required
def assignment_delete(request, pk):
    obj = get_object_or_404(TeachingAssignment, pk=pk)
    if request.method == "POST":
        label = str(obj)
        obj.delete()
        log_action(request, "Deleted teaching assignment", "Academics", label)
        messages.success(request, "The teaching assignment has been deleted.")
        return redirect("academics:assignment_list")
    return render(
        request,
        "academics/assignment_confirm_delete.html",
        {"page_title": "Delete teaching assignment", "object": obj},
    )


# ---------------------------------------------------------------------------
# School settings (singleton) + inline grading / component management
# ---------------------------------------------------------------------------
@admin_required
def settings_view(request):
    conf = SchoolSettings.load()
    form = SchoolSettingsForm(request.POST or None, instance=conf)
    if request.method == "POST" and form.is_valid():
        form.save()
        log_action(request, "Updated school settings", "Academics", "School settings changed.")
        messages.success(request, "School settings have been saved.")
        return redirect("academics:settings")

    context = {
        "page_title": "School settings",
        "form": form,
        "band_form": GradingBandForm(prefix="band"),
        "comp_form": AssessmentComponentForm(prefix="comp"),
        "bands": GradingBand.objects.all(),
        "components": AssessmentComponent.objects.all(),
        "weights_total": AssessmentComponent.weights_total(),
        "weights_ok": weights_are_consistent(),
    }
    return render(request, "academics/settings.html", context)
