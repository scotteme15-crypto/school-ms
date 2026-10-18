"""URL routes for the teachers app."""
from django.urls import path

from . import views

app_name = "teachers"

urlpatterns = [
    path("teachers/", views.teacher_list, name="list"),
    path("teachers/my-classes/", views.my_classes, name="my_classes"),
    path("teachers/students/", views.teacher_students, name="students"),
    path("teachers/new/", views.teacher_create, name="create"),
    path("teachers/<int:pk>/", views.teacher_detail, name="detail"),
    path("teachers/<int:pk>/edit/", views.teacher_edit, name="edit"),
    path("teachers/<int:pk>/delete/", views.teacher_delete, name="delete"),
]
