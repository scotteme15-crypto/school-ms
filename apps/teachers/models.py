"""Teacher records, linked one-to-one with a User account."""
from django.conf import settings
from django.db import models

from apps.academics.models import DEPARTMENTS

GENDER_CHOICES = [("M", "Male"), ("F", "Female")]
EMPLOYMENT_STATUS = [("Active", "Active"), ("On leave", "On leave"), ("Inactive", "Inactive")]


class Teacher(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="teacher_profile",
    )
    teacher_id = models.CharField(max_length=24, unique=True, help_text="e.g. TCH-01")
    name = models.CharField(max_length=150)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default="M")
    department = models.CharField(max_length=60, choices=[(d, d) for d in DEPARTMENTS])
    qualification = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    employment_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=EMPLOYMENT_STATUS, default="Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def initials(self):
        return "".join(p[0] for p in self.name.split()[:2]).upper()

    @property
    def is_active(self):
        return self.status == "Active"
