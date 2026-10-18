"""URL routes for the assignments app."""
from django.urls import path

from . import views

app_name = "assignments"

urlpatterns = [
    path("assignments/", views.list_view, name="list"),
    path("assignments/create/", views.create, name="create"),
    path("assignments/<int:pk>/edit/", views.edit, name="edit"),
    path("assignments/<int:pk>/delete/", views.delete, name="delete"),
]
