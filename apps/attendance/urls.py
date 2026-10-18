"""URL routes for attendance registers."""
from django.urls import path

from . import views

app_name = "attendance"

urlpatterns = [
    path("attendance/", views.overview, name="overview"),
    path("attendance/entry/", views.entry, name="entry"),
    path("attendance/mine/", views.my_attendance, name="my_attendance"),
    path("attendance/<int:pk>/delete/", views.session_delete, name="session_delete"),
]
