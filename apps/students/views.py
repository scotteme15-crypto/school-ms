"""Server-rendered views for student records.

Listings are readable by staff; creating, editing and deleting a student is
restricted to administrators.
"""
import csv

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.academics.models import GRADE_CHOICES, SECTION_CHOICES, SchoolClass
from apps.accounts.permissions import admin_required, staff_required
from apps.audit.services import log_action

from .forms import StudentForm
from .models import STUDENT_STATUS, Student

PER_PAGE = 25


def _filtered_students(request):
    qs = Student.objects.select_related("school_class").order_by("grade", "section", "first_name")
    q = request.GET.get("q", "").strip()
    grade = request.GET.get("grade", "").strip()
    section = request.GET.get("section", "").strip()
    status = request.GET.get("status", "").strip()
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
    if status:
        qs = qs.filter(status=status)
    if class_id:
        qs = qs.filter(school_class_id=class_id)
    return qs


def _filter_context(request):
    return {
        "q": request.GET.get("q", "").strip(),
        "grade": request.GET.get("grade", "").strip(),
        "section": request.GET.get("section", "").strip(),
        "status": request.GET.get("status", "").strip(),
        "class_id": request.GET.get("class", "").strip(),
        "grade_choices": GRADE_CHOICES,
        "section_choices": SECTION_CHOICES,
        "status_choices": STUDENT_STATUS,
        "classes": SchoolClass.objects.all(),
    }


@staff_required
def student_list(request):
    qs = _filtered_students(request)
    paginator = Paginator(qs, PER_PAGE)
    context = {"page_title": "Students", "page_obj": paginator.get_page(request.GET.get("page"))}
    context.update(_filter_context(request))
    return render(request, "students/list.html", context)


@staff_required
def student_detail(request, pk):
    student = get_object_or_404(Student.objects.select_related("school_class"), pk=pk)
    return render(
        request,
        "students/detail.html",
        {"page_title": student.full_name, "student": student},
    )


@admin_required
def student_create(request):
    form = StudentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        log_action(request, "Created student", "Students", f"{obj.full_name} ({obj.student_id}) enrolled.")
        messages.success(request, f"Student {obj.full_name} has been enrolled.")
        return redirect("students:detail", pk=obj.pk)
    return render(
        request,
        "students/form.html",
        {"page_title": "Enrol student", "form": form, "is_edit": False},
    )


@admin_required
def student_edit(request, pk):
    obj = get_object_or_404(Student, pk=pk)
    form = StudentForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        log_action(request, "Updated student", "Students", f"{obj.full_name} ({obj.student_id}) updated.")
        messages.success(request, f"Student {obj.full_name} has been updated.")
        return redirect("students:detail", pk=obj.pk)
    return render(
        request,
        "students/form.html",
        {"page_title": f"Edit {obj.full_name}", "form": form, "object": obj, "is_edit": True},
    )


@admin_required
def student_delete(request, pk):
    obj = get_object_or_404(Student, pk=pk)
    if request.method == "POST":
        label = f"{obj.full_name} ({obj.student_id})"
        obj.delete()
        log_action(request, "Deleted student", "Students", f"{label} removed.")
        messages.success(request, f"Student {obj.full_name} has been deleted.")
        return redirect("students:list")
    return render(
        request,
        "students/confirm_delete.html",
        {"page_title": "Delete student", "object": obj},
    )


@staff_required
def student_export(request):
    qs = _filtered_students(request)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="students.csv"'
    response.write("\ufeff")  # BOM so Excel opens the file with correct encoding
    writer = csv.writer(response)
    writer.writerow(
        [
            "Student ID",
            "Full name",
            "Gender",
            "Grade",
            "Section",
            "Class",
            "Status",
            "Guardian",
            "Guardian phone",
            "Email",
            "Admission date",
        ]
    )
    for s in qs:
        writer.writerow(
            [
                s.student_id,
                s.full_name,
                s.get_gender_display(),
                s.grade,
                s.section,
                s.school_class.name if s.school_class_id else "",
                s.status,
                s.parent_name,
                s.parent_phone,
                s.email,
                s.admission_date.isoformat() if s.admission_date else "",
            ]
        )
    log_action(request, "Exported students", "Students", f"{qs.count()} student records exported.")
    return response
