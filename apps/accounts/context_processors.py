"""Template context shared by every page: navigation, school settings, badges.

Everything here is plain data (dicts/lists) so it can be handed straight to
``json_script`` for the client-side UI.
"""
from pathlib import Path

from django.conf import settings
from django.contrib.messages import get_messages
from django.urls import reverse

from .navigation import navigation_for


def _asset_version() -> str:
    """Newest mtime across static assets, used to bust browser caches in dev."""
    static_dir = Path(settings.BASE_DIR) / "static"
    latest = 0
    for path in static_dir.rglob("*"):
        if path.is_file():
            try:
                latest = max(latest, int(path.stat().st_mtime))
            except OSError:
                continue
    return str(latest)


def school_context(request):
    from apps.academics.models import SchoolSettings
    from apps.notifications.models import Notification

    user = getattr(request, "user", None)
    settings_obj = SchoolSettings.load()

    ctx = {
        "school": settings_obj,
        "asset_version": _asset_version(),
        "current_year": settings_obj.current_academic_year,
        "current_semester": settings_obj.current_semester,
        "nav_groups": [],
        "unread_notification_count": 0,
        "pending_approval_count": 0,
        "recent_notifications": [],
        "notifications_url": reverse("notifications:list"),
        "django_messages": [
            {"level": m.level_tag, "text": str(m)} for m in get_messages(request)
        ],
    }

    if user is not None and user.is_authenticated:
        ctx["nav_groups"] = navigation_for(user)
        notifications = Notification.objects.filter(user=user).order_by("-created_at")[:8]
        ctx["recent_notifications"] = [
            {
                "title": n.title,
                "body": n.body,
                "kind": n.kind,
                "read": n.read,
                "url": n.url or reverse("notifications:list"),
            }
            for n in notifications
        ]
        ctx["unread_notification_count"] = Notification.objects.filter(user=user, read=False).count()

        if user.is_admin_role:
            from apps.results.models import ResultSheet

            ctx["pending_approval_count"] = ResultSheet.objects.filter(
                status=ResultSheet.Status.PENDING
            ).count()
        elif user.is_teacher_role:
            from apps.results.models import ResultSheet
            from apps.teachers.models import Teacher

            teacher = Teacher.objects.filter(user=user).first()
            if teacher:
                ctx["pending_approval_count"] = ResultSheet.objects.filter(
                    teacher=teacher,
                    status__in=[
                        ResultSheet.Status.DRAFT,
                        ResultSheet.Status.RETURNED,
                        ResultSheet.Status.REJECTED,
                    ],
                ).count()
    return ctx
