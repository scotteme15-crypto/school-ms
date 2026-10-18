"""Assignments issued to classes."""
from decimal import Decimal

from django.db import models


class Assignment(models.Model):
    title = models.CharField(max_length=180)
    subject = models.ForeignKey("academics.Subject", on_delete=models.CASCADE, related_name="assignments")
    school_class = models.ForeignKey("academics.SchoolClass", on_delete=models.CASCADE, related_name="assignments")
    teacher = models.ForeignKey("teachers.Teacher", null=True, blank=True, on_delete=models.SET_NULL, related_name="assignments")
    max_mark = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("15"))
    due_date = models.DateField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-due_date"]

    def __str__(self):
        return f"{self.title} ({self.school_class.name})"

    @property
    def is_overdue(self):
        from django.utils import timezone

        return self.due_date < timezone.localdate()
