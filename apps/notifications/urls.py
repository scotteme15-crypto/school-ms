"""URL routes for the notifications app."""
from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path("notifications/", views.list_view, name="list"),
    path("notifications/read-all/", views.mark_all_read, name="mark_all_read"),
    path("notifications/<int:pk>/read/", views.mark_read, name="mark_read"),
    path("notifications/<int:pk>/delete/", views.delete, name="delete"),
]
