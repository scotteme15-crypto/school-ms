"""Root URL configuration for the Bariso School Management System."""
from django.contrib import admin
from django.urls import include, path

from apps.accounts import views as accounts_views

urlpatterns = [
    path("django-admin/", admin.site.urls),
    # Role dashboard: flat name ``dashboard`` used by LOGIN_REDIRECT_URL and nav.
    path("", accounts_views.dashboard, name="dashboard"),
    # Auth, profile, password flows and global search
    path("", include("apps.accounts.urls")),
    # School structure: years, classes, subjects, settings
    path("", include("apps.academics.urls")),
    path("", include("apps.students.urls")),
    path("", include("apps.teachers.urls")),
    path("", include("apps.attendance.urls")),
    path("", include("apps.results.urls")),
    path("", include("apps.timetable.urls")),
    path("", include("apps.assignments.urls")),
    path("", include("apps.announcements.urls")),
    path("", include("apps.notifications.urls")),
    path("", include("apps.reports.urls")),
    path("", include("apps.audit.urls")),
]

# Friendly error handlers (templates live in /templates).
handler403 = "apps.accounts.views.error_403"
handler404 = "apps.accounts.views.error_404"
handler500 = "apps.accounts.views.error_500"
