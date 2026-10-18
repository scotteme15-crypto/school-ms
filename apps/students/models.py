"""Student records, linked to a User account and a school class."""
from django.conf import settings
from django.db import models

from apps.academics.models import GRADE_CHOICES, SECTION_CHOICES

GENDER_CHOICES = [("M", "Male"), ("F", "Female")]
STUDENT_STATUS = [("Active", "Active"), ("Inactive", "Inactive"), ("Suspended", "Suspended")]


class Student(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="student_profile",
    )
    student_id = models.CharField(max_length=24, unique=True, help_text="e.g. UNS-10A-01")
    first_name = models.CharField(max_length=60)
    middle_name = models.CharField(max_length=60, blank=True)
    last_name = models.CharField(max_length=60, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default="M")
    date_of_birth = models.DateField(null=True, blank=True)
    grade = models.PositiveSmallIntegerField(choices=GRADE_CHOICES)
    section = models.CharField(max_length=4, choices=SECTION_CHOICES)
    school_class = models.ForeignKey(
        "academics.SchoolClass",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="students",
    )
    parent_name = models.CharField(max_length=150, blank=True)
    parent_phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=200, blank=True)
    admission_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STUDENT_STATUS, default="Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["grade", "section", "first_name"]
        indexes = [models.Index(fields=["grade", "section"]), models.Index(fields=["status"])]

    def __str__(self):
        return f"{self.full_name} ({self.student_id})"

    @property
    def full_name(self):
        return " ".join(p for p in [self.first_name, self.middle_name, self.last_name] if p)

    @property
    def short_name(self):
        return " ".join(p for p in [self.first_name, self.middle_name] if p)

    @property
    def initials(self):
        parts = [self.first_name, self.last_name or self.middle_name]
        return "".join(p[0] for p in parts if p).upper()

    @property
    def is_active(self):
        return self.status == "Active"
