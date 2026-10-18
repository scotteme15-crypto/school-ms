"""Audit log routes (read-only viewer)."""
from django.urls import path

from . import views

app_name = "audit"

urlpatterns = [
    path("audit/", views.log_list, name="list"),
]
