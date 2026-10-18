"""Role-based access helpers shared across every app.

Permission is always enforced on the server: templates only hide UI, they never
grant access.
"""
from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse


def is_admin(user) -> bool:
    return bool(user.is_authenticated and user.role == "admin")


def is_teacher(user) -> bool:
    return bool(user.is_authenticated and user.role == "teacher")


def is_student(user) -> bool:
    return bool(user.is_authenticated and user.role == "student")


def role_required(*roles):
    """Decorator: allow only the given roles (all authenticated otherwise)."""

    def decorator(view):
        @wraps(view)
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                return redirect_to_login(request.get_full_path(), reverse("accounts:login"))
            if user.role not in roles and not user.is_superuser:
                raise PermissionDenied("Your account does not have access to this area.")
            return view(request, *args, **kwargs)

        return _wrapped

    return decorator


admin_required = role_required("admin")
teacher_required = role_required("teacher")
student_required = role_required("student")
staff_required = role_required("admin", "teacher")


class RoleRequiredMixin:
    """Class-based view mixin enforcing a set of allowed roles."""

    allowed_roles: tuple[str, ...] = ()

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return redirect_to_login(request.get_full_path(), reverse("accounts:login"))
        if self.allowed_roles and user.role not in self.allowed_roles and not user.is_superuser:
            raise PermissionDenied("Your account does not have access to this area.")
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = ("admin",)


class TeacherRequiredMixin(RoleRequiredMixin):
    allowed_roles = ("teacher",)


class StudentRequiredMixin(RoleRequiredMixin):
    allowed_roles = ("student",)


class StaffRequiredMixin(RoleRequiredMixin):
    allowed_roles = ("admin", "teacher")
