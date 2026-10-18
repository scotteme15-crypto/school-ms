"""URL routes for the academics app (school structure, exams, grading, settings)."""
from django.urls import path

from . import views

app_name = "academics"

urlpatterns = [
    # Classes
    path("classes/", views.class_list, name="class_list"),
    path("classes/new/", views.class_create, name="class_create"),
    path("classes/<int:pk>/edit/", views.class_edit, name="class_edit"),
    path("classes/<int:pk>/delete/", views.class_delete, name="class_delete"),
    # Subjects
    path("subjects/", views.subject_list, name="subject_list"),
    path("subjects/new/", views.subject_create, name="subject_create"),
    path("subjects/<int:pk>/edit/", views.subject_edit, name="subject_edit"),
    path("subjects/<int:pk>/delete/", views.subject_delete, name="subject_delete"),
    # Exams
    path("exams/", views.exam_list, name="exam_list"),
    path("exams/new/", views.exam_create, name="exam_create"),
    path("exams/<int:pk>/edit/", views.exam_edit, name="exam_edit"),
    path("exams/<int:pk>/delete/", views.exam_delete, name="exam_delete"),
    # Academic years & semesters
    path("years/", views.year_list, name="year_list"),
    path("years/new/", views.year_create, name="year_create"),
    path("years/<int:pk>/edit/", views.year_edit, name="year_edit"),
    path("semesters/", views.semester_list, name="semester_list"),
    path("semesters/new/", views.semester_create, name="semester_create"),
    # Grading scale & assessment components
    path("grading/", views.grading, name="grading"),
    path("components/", views.components, name="components"),
    # Teaching assignments
    path("teaching-assignments/", views.assignment_list, name="assignment_list"),
    path("teaching-assignments/new/", views.assignment_create, name="assignment_create"),
    path("teaching-assignments/<int:pk>/delete/", views.assignment_delete, name="assignment_delete"),
    # School settings
    path("settings/", views.settings_view, name="settings"),
]
