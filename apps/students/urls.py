"""URL routes for the students app."""
from django.urls import path

from . import views

app_name = "students"

urlpatterns = [
    path("students/", views.student_list, name="list"),
    path("students/export/", views.student_export, name="export"),
    path("students/new/", views.student_create, name="create"),
    path("students/<int:pk>/", views.student_detail, name="detail"),
    path("students/<int:pk>/edit/", views.student_edit, name="edit"),
    path("students/<int:pk>/delete/", views.student_delete, name="delete"),
]
