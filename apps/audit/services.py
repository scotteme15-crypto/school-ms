"""Helper for writing audit entries without repeating boilerplate."""
from .models import AuditLog


def _client_ip(request):
    if request is None:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_action(request, action, module="", description=""):
    """Record an audit entry for the acting user (or the system)."""
    user = getattr(request, "user", None)
    if user is not None and not user.is_authenticated:
        user = None
    return AuditLog.objects.create(
        user=user,
        user_name=user.display_name if user else "System",
        role=user.role if user else "system",
        action=action,
        module=module,
        description=description,
        ip_address=_client_ip(request),
    )
