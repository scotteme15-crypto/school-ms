"""URL routes for result sheets, marks approval and student reports."""
from django.urls import path

from . import views

app_name = "results"

urlpatterns = [
    path("results/", views.sheet_list, name="list"),
    path("results/entry/", views.marks_entry, name="entry"),
    path("results/approvals/", views.approvals, name="approvals"),
    path("results/mine/", views.my_results, name="my_results"),
    path("results/<int:pk>/", views.sheet_detail, name="sheet_detail"),
    path("results/<int:pk>/submit/", views.submit, name="submit"),
    path("results/<int:pk>/approve/", views.approve, name="approve"),
    path("results/<int:pk>/return/", views.return_sheet, name="return_sheet"),
    path("results/<int:pk>/report-card/", views.report_card, name="report_card"),
    path("results/<int:pk>/delete/", views.delete, name="delete"),
]
