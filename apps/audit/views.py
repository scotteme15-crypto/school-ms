"""Read-only audit log viewer (administrators and staff)."""
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render

from apps.accounts.permissions import staff_required

from .models import AuditLog

PAGE_SIZE = 40


@staff_required
def log_list(request):
    """Paginated, filterable list of audit entries. Never mutates data."""
    logs = AuditLog.objects.select_related("user")

    q = request.GET.get("q", "").strip()
    module = request.GET.get("module", "").strip()
    role = request.GET.get("role", "").strip()

    if q:
        logs = logs.filter(
            Q(action__icontains=q)
            | Q(description__icontains=q)
            | Q(user_name__icontains=q)
            | Q(module__icontains=q)
        )
    if module:
        logs = logs.filter(module=module)
    if role:
        logs = logs.filter(role=role)

    modules = list(
        AuditLog.objects.exclude(module="").values_list("module", flat=True).distinct().order_by("module")
    )
    roles = list(
        AuditLog.objects.exclude(role="").values_list("role", flat=True).distinct().order_by("role")
    )

    page_obj = Paginator(logs, PAGE_SIZE).get_page(request.GET.get("page"))

    context = {
        "page_title": "Audit log",
        "page_obj": page_obj,
        "logs": page_obj.object_list,
        "modules": modules,
        "roles": roles,
        "filters": {"q": q, "module": module, "role": role},
        "total": page_obj.paginator.count,
    }
    return render(request, "audit/list.html", context)
