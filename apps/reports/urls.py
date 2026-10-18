"""Reporting routes: hub, analytics dashboard and CSV exports."""
from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("reports/", views.index, name="index"),
    path("reports/analytics/", views.analytics, name="analytics"),
    path("reports/export/", views.export, name="export"),
]
