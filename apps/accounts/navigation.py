"""Role-specific navigation definition, mirroring the original single-file app."""
from django.urls import reverse

# Each item: (url_name, label, icon_key, badge_key|None)
NAV = {
    "admin": [
        (
            "Overview",
            [
                ("dashboard", "Dashboard", "dash", None),
                ("reports:analytics", "Analytics", "trend", None),
                ("reports:index", "Reports", "file", None),
            ],
        ),
        (
            "People",
            [
                ("students:list", "Students", "users", None),
                ("teachers:list", "Teachers", "cap", None),
                ("academics:class_list", "Classes", "school", None),
                ("academics:subject_list", "Subjects", "book", None),
            ],
        ),
        (
            "Academics",
            [
                ("results:approvals", "Result approval", "checkc", "pending"),
                ("results:list", "Results", "clip", None),
                ("attendance:overview", "Attendance", "check", None),
                ("timetable:index", "Timetable", "grid", None),
                ("academics:exam_list", "Exams", "scroll", None),
                ("assignments:list", "Assignments", "pencil", None),
            ],
        ),
        (
            "School",
            [
                ("announcements:list", "Announcements", "mega", None),
                ("announcements:event_list", "Events", "cal", None),
                ("audit:list", "Audit log", "act", None),
                ("academics:settings", "Settings", "gear", None),
            ],
        ),
    ],
    "teacher": [
        (
            "Teaching",
            [
                ("dashboard", "Dashboard", "dash", None),
                ("teachers:my_classes", "My classes", "school", None),
                ("teachers:students", "Students", "users", None),
            ],
        ),
        (
            "Academics",
            [
                ("results:list", "Results", "clip", "todo"),
                ("attendance:entry", "Attendance", "check", None),
                ("assignments:list", "Assignments", "pencil", None),
                ("timetable:index", "Timetable", "grid", None),
                ("academics:exam_list", "Exams", "scroll", None),
            ],
        ),
        (
            "School",
            [
                ("announcements:list", "Announcements", "mega", None),
                ("announcements:event_list", "Events", "cal", None),
                ("notifications:list", "Notifications", "bell", None),
                ("accounts:profile", "My profile", "user", None),
            ],
        ),
    ],
    "student": [
        (
            "My school",
            [
                ("dashboard", "Dashboard", "dash", None),
                ("results:my_results", "My results", "award", None),
                ("attendance:my_attendance", "Attendance", "check", None),
                ("timetable:index", "Timetable", "grid", None),
            ],
        ),
        (
            "Work",
            [
                ("assignments:list", "Assignments", "pencil", None),
                ("academics:exam_list", "Exams", "scroll", None),
            ],
        ),
        (
            "School",
            [
                ("announcements:list", "Announcements", "mega", None),
                ("announcements:event_list", "Events", "cal", None),
                ("notifications:list", "Notifications", "bell", None),
                ("accounts:profile", "My profile", "user", None),
            ],
        ),
    ],
}

# Which URL names each role may reach (defence in depth on top of per-view checks)
ROLE_ROUTES = {
    "admin": {
        "dashboard", "students:list", "teachers:list", "academics:class_list", "academics:subject_list",
        "results:approvals", "results:list", "attendance:overview", "timetable:index", "academics:exam_list",
        "assignments:list", "announcements:list", "announcements:event_list", "audit:list", "academics:settings",
        "reports:analytics", "reports:index", "notifications:list", "accounts:profile",
    },
    "teacher": {
        "dashboard", "teachers:my_classes", "teachers:students", "results:list", "attendance:entry",
        "assignments:list", "timetable:index", "academics:exam_list", "announcements:list",
        "announcements:event_list", "notifications:list", "accounts:profile",
    },
    "student": {
        "dashboard", "results:my_results", "attendance:my_attendance", "timetable:index",
        "assignments:list", "academics:exam_list", "announcements:list", "announcements:event_list",
        "notifications:list", "accounts:profile",
    },
}


def navigation_for(user):
    """Return the sidebar structure for a user with resolved URLs and badges."""
    from apps.results.models import ResultSheet
    from apps.teachers.models import Teacher

    groups = []
    for group_name, items in NAV.get(user.role, []):
        rendered = []
        for url_name, label, icon, badge_key in items:
            try:
                url = reverse(url_name)
            except Exception:  # pragma: no cover - defensive
                continue
            badge = None
            if badge_key == "pending" and user.is_admin_role:
                badge = ResultSheet.objects.filter(status=ResultSheet.Status.PENDING).count()
            elif badge_key == "todo" and user.is_teacher_role:
                teacher = Teacher.objects.filter(user=user).first()
                if teacher:
                    badge = ResultSheet.objects.filter(
                        teacher=teacher,
                        status__in=[
                            ResultSheet.Status.DRAFT,
                            ResultSheet.Status.RETURNED,
                            ResultSheet.Status.REJECTED,
                        ],
                    ).count()
            rendered.append({"url": url, "label": label, "icon": icon, "badge": badge or None})
        groups.append({"group": group_name, "items": rendered})
    return groups
