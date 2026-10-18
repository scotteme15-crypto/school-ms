"""URL routes for the timetable app."""
from django.urls import path

from . import views

app_name = "timetable"

urlpatterns = [
    path("timetable/", views.index, name="index"),
    path("timetable/create/", views.slot_create, name="slot_create"),
    path("timetable/<int:pk>/edit/", views.slot_edit, name="slot_edit"),
    path("timetable/<int:pk>/delete/", views.slot_delete, name="slot_delete"),
]
