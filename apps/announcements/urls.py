"""URL routes for the announcements app."""
from django.urls import path

from . import views

app_name = "announcements"

urlpatterns = [
    path("announcements/", views.list_view, name="list"),
    path("announcements/create/", views.create, name="create"),
    path("announcements/<int:pk>/edit/", views.edit, name="edit"),
    path("announcements/<int:pk>/delete/", views.delete, name="delete"),
    path("events/", views.event_list, name="event_list"),
    path("events/create/", views.event_create, name="event_create"),
    path("events/<int:pk>/edit/", views.event_edit, name="event_edit"),
    path("events/<int:pk>/delete/", views.event_delete, name="event_delete"),
]
