"""Server-rendered views for teaching staff.

The staff directory is readable by staff; managing records is admin-only.
``my_classes`` and ``students`` are the teacher's own scoped teaching pages.
"""
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.academics.models import (
    DEPARTMENTS,
    GRADE_CHOICES,
    SECTION_CHOICES,
    SchoolClass,
    TeachingAssignment,
)
from apps.accounts.permissions import admin_required, staff_required, teacher_required
from apps.audit.services import log_action
from apps.students.models import Student

from .forms import TeacherForm
from .models import EMPLOYMENT_STATUS, Teacher

PER_PAGE = 25


def _teacher_class_ids(teacher):
    if not teacher:
        return []
    return list(
        TeachingAssignment.objects.filter(teacher=teacher)
        .values_list("school_class_id", flat=True)
        .distinct()
    )


# ---------------------------------------------------------------------------
# Staff directory (admin / staff)
# ---------------------------------------------------------------------------
@staff_required
def teacher_list(request):
    qs = Teacher.objects.all()
    q = request.GET.get("q", "").strip()
    department = request.GET.get("department", "").strip()
    status = request.GET.get("status", "").strip()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(teacher_id__icontains=q) | Q(email__icontains=q))
    if department:
        qs = qs.filter(department=department)
    if status:
        qs = qs.filter(status=status)

    paginator = Paginator(qs, PER_PAGE)
    context = {
        "page_title": "Teachers",
        "page_obj": paginator.get_page(request.GET.get("page")),
        "q": q,
        "department": department,
        "status": status,
        "departments": DEPARTMENTS,
        "status_choices": EMPLOYMENT_STATUS,
    }
    return render(request, "teachers/list.html", context)


@staff_required
def teacher_detail(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    assignments = (
        TeachingAssignment.objects.filter(teacher=teacher)
        .select_related("subject", "school_class", "academic_year")
    )
    context = {
        "page_title": teacher.name,
        "teacher": teacher,
        "assignments": assignments,
        "homeroom_classes": teacher.homeroom_classes.all(),
        "subjects": teacher.subjects.all(),
    }
    return render(request, "teachers/detail.html", context)


@admin_required
def teacher_create(request):
    form = TeacherForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        log_action(request, "Created teacher", "Teachers", f"{obj.name} ({obj.teacher_id}) added.")
        messages.success(request, f"Teacher {obj.name} has been added.")
        return redirect("teachers:detail", pk=obj.pk)
    return render(
        request,
        "teachers/form.html",
        {"page_title": "Add teacher", "form": form, "is_edit": False},
    )


@admin_required
def teacher_edit(request, pk):
    obj = get_object_or_404(Teacher, pk=pk)
    form = TeacherForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        log_action(request, "Updated teacher", "Teachers", f"{obj.name} ({obj.teacher_id}) updated.")
        messages.success(request, f"Teacher {obj.name} has been updated.")
        return redirect("teachers:detail", pk=obj.pk)
    return render(
        request,
        "teachers/form.html",
        {"page_title": f"Edit {obj.name}", "form": form, "object": obj, "is_edit": True},
    )


@admin_required
def teacher_delete(request, pk):
    obj = get_object_or_404(Teacher, pk=pk)
    if request.method == "POST":
        label = f"{obj.name} ({obj.teacher_id})"
        obj.delete()
        log_action(request, "Deleted teacher", "Teachers", f"{label} removed.")
        messages.success(request, f"Teacher {obj.name} has been deleted.")
        return redirect("teachers:list")
    return render(
        request,
        "teachers/confirm_delete.html",
        {"page_title": "Delete teacher", "object": obj},
    )


# ---------------------------------------------------------------------------
# Teacher-scoped pages
# ---------------------------------------------------------------------------
@teacher_required
def my_classes(request):
    teacher = getattr(request.user, "teacher_profile", None)
    assignments = (
        TeachingAssignment.objects.filter(teacher=teacher)
        .select_related("subject", "school_class", "academic_year")
        if teacher
        else TeachingAssignment.objects.none()
    )

    classes = []
    index = {}
    for assignment in assignments:
        entry = index.get(assignment.school_class_id)
        if entry is None:
            entry = {
                "klass": assignment.school_class,
                "subjects": [],
                "students": assignment.school_class.student_count,
            }
            index[assignment.school_class_id] = entry
            classes.append(entry)
        entry["subjects"].append(assignment.subject.name)

    return render(
        request,
        "teachers/my_classes.html",
        {"page_title": "My classes", "teacher": teacher, "classes": classes},
    )


@teacher_required
def teacher_students(request):
    teacher = getattr(request.user, "teacher_profile", None)
    class_ids = _teacher_class_ids(teacher)
    qs = (
        Student.objects.filter(school_class_id__in=class_ids)
        .select_related("school_class")
        .order_by("grade", "section", "first_name")
    )
    q = request.GET.get("q", "").strip()
    grade = request.GET.get("grade", "").strip()
    section = request.GET.get("section", "").strip()
    class_id = request.GET.get("class", "").strip()
    if q:
        qs = qs.filter(
            Q(first_name__icontains=q)
            | Q(middle_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(student_id__icontains=q)
        )
    if grade:
        qs = qs.filter(grade=grade)
    if section:
        qs = qs.filter(section=section)
    if class_id:
        qs = qs.filter(school_class_id=class_id)

    paginator = Paginator(qs, PER_PAGE)
    # The class filter only lists the classes this teacher actually teaches.
    context = {
        "page_title": "My students",
        "page_obj": paginator.get_page(request.GET.get("page")),
        "q": q,
        "grade": grade,
        "section": section,
        "class_id": class_id,
        "grade_choices": GRADE_CHOICES,
        "section_choices": SECTION_CHOICES,
        "classes": SchoolClass.objects.filter(pk__in=class_ids),
    }
    return render(request, "teachers/students.html", context)
