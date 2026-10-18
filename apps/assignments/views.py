"""Assignment list and management, scoped by role.

Admins see every assignment, teachers see the classes they teach and students
see only their own class. Creating, editing and deleting is limited to admins
and the teacher who owns the assignment.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.permissions import staff_required
from apps.academics.models import TeachingAssignment
from apps.audit.services import log_action

from .forms import AssignmentForm
from .models import Assignment


def _teacher(user):
    return getattr(user, "teacher_profile", None)


def _can_manage(user, assignment):
    if user.is_admin_role or user.is_superuser:
        return True
    teacher = _teacher(user)
    return bool(teacher and assignment.teacher_id == teacher.id)


def _visible(user):
    qs = Assignment.objects.select_related("subject", "school_class", "teacher")
    if user.is_admin_role or user.is_superuser:
        return qs
    if user.is_teacher_role:
        teacher = _teacher(user)
        if teacher is None:
            return qs.none()
        class_ids = TeachingAssignment.objects.filter(teacher=teacher).values_list(
            "school_class_id", flat=True
        )
        return qs.filter(school_class_id__in=class_ids)
    student = getattr(user, "student_profile", None)
    if student and student.school_class_id:
        return qs.filter(school_class_id=student.school_class_id)
    return qs.none()


@login_required
def list_view(request):
    user = request.user
    page_obj = Paginator(_visible(user), 15).get_page(request.GET.get("page"))
    for assignment in page_obj:
        assignment.can_edit = _can_manage(user, assignment)
    context = {
        "page_title": "Assignments",
        "page_obj": page_obj,
        "can_manage": user.is_admin_role or user.is_teacher_role or user.is_superuser,
    }
    return render(request, "assignments/list.html", context)


@staff_required
def create(request):
    form = AssignmentForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        assignment = form.save(commit=False)
        if request.user.is_teacher_role:
            assignment.teacher = _teacher(request.user)
        assignment.save()
        log_action(
            request,
            "Created assignment",
            "Assignments",
            f"{assignment.title} · {assignment.school_class.name}",
        )
        messages.success(request, "Assignment created.")
        return redirect("assignments:list")
    return render(
        request,
        "assignments/form.html",
        {"form": form, "page_title": "New assignment", "mode": "create"},
    )


@staff_required
def edit(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    if not _can_manage(request.user, assignment):
        raise PermissionDenied("You can only edit assignments you created.")
    form = AssignmentForm(request.POST or None, instance=assignment, user=request.user)
    if request.method == "POST" and form.is_valid():
        assignment = form.save(commit=False)
        if request.user.is_teacher_role:
            assignment.teacher = _teacher(request.user)
        assignment.save()
        log_action(
            request,
            "Updated assignment",
            "Assignments",
            f"{assignment.title} · {assignment.school_class.name}",
        )
        messages.success(request, "Assignment updated.")
        return redirect("assignments:list")
    return render(
        request,
        "assignments/form.html",
        {"form": form, "page_title": "Edit assignment", "assignment": assignment, "mode": "edit"},
    )


@staff_required
@require_POST
def delete(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    if not _can_manage(request.user, assignment):
        raise PermissionDenied("You can only delete assignments you created.")
    label = f"{assignment.title} · {assignment.school_class.name}"
    assignment.delete()
    log_action(request, "Deleted assignment", "Assignments", label)
    messages.success(request, "Assignment deleted.")
    return redirect("assignments:list")
