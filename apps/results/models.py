"""Exams, result sheets, per-student marks and the assessment components."""
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.academics.models import (
    AssessmentComponent,
    AcademicYear,
    GRADE_CHOICES,
    Semester,
    grade_letter,
    grade_point,
)

EXAM_TYPE_CHOICES = [
    ("Quiz", "Quiz"),
    ("Midterm", "Midterm"),
    ("Final", "Final"),
    ("Mock Exam", "Mock Exam"),
    ("National Exam", "National Exam"),
]


class Exam(models.Model):
    name = models.CharField(max_length=150)
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPE_CHOICES, default="Final")
    grade = models.PositiveSmallIntegerField(choices=GRADE_CHOICES)
    subject = models.ForeignKey("academics.Subject", null=True, blank=True, on_delete=models.SET_NULL, related_name="exams")
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    room = models.CharField(max_length=40, blank=True)
    instructions = models.TextField(blank=True)
    academic_year = models.ForeignKey(AcademicYear, null=True, blank=True, on_delete=models.SET_NULL, related_name="exams")
    semester = models.ForeignKey(Semester, null=True, blank=True, on_delete=models.SET_NULL, related_name="exams")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "start_time"]

    def __str__(self):
        return f"{self.name} — {self.date}"


class ResultSheet(models.Model):
    """One teacher's marks for a class + subject + exam type in a semester."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING = "pending", "Pending review"
        RETURNED = "returned", "Returned for correction"
        REJECTED = "rejected", "Rejected"
        APPROVED = "approved", "Approved & published"

    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name="result_sheets")
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name="result_sheets")
    school_class = models.ForeignKey("academics.SchoolClass", on_delete=models.CASCADE, related_name="result_sheets")
    subject = models.ForeignKey("academics.Subject", on_delete=models.CASCADE, related_name="result_sheets")
    teacher = models.ForeignKey("teachers.Teacher", on_delete=models.CASCADE, related_name="result_sheets")
    exam = models.ForeignKey(Exam, null=True, blank=True, on_delete=models.SET_NULL, related_name="result_sheets")
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPE_CHOICES, default="Final")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT, db_index=True)
    reason = models.TextField(blank=True, help_text="Set by the registrar when returning or rejecting.")
    submitted_at = models.DateTimeField(null=True, blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="decided_sheets"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        unique_together = [("academic_year", "semester", "school_class", "subject", "exam_type")]

    def __str__(self):
        return f"{self.subject} · {self.school_class} · {self.exam_type}"

    @property
    def is_editable(self):
        return self.status in {self.Status.DRAFT, self.Status.RETURNED, self.Status.REJECTED}

    @property
    def is_published(self):
        return self.status == self.Status.APPROVED

    def context_label(self):
        return f"{self.subject.name} · {self.school_class.name} · {self.exam_type}"


class SubjectMark(models.Model):
    """A single student's marks within a result sheet."""

    result_sheet = models.ForeignKey(ResultSheet, on_delete=models.CASCADE, related_name="marks")
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="subject_marks")
    remark = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["student__first_name"]
        unique_together = [("result_sheet", "student")]

    def __str__(self):
        return f"{self.student.full_name} — {self.result_sheet}"

    # ------------------------------------------------------------------ maths
    def entries_total(self, entries=None):
        entries = list(entries) if entries is not None else list(self.entries.all())
        return sum((e.score for e in entries), Decimal("0"))

    @property
    def total(self):
        return self.entries_total()

    @property
    def percentage(self):
        max_total = AssessmentComponent.total_max_score() or Decimal("100")
        if not max_total:
            return Decimal("0")
        return (self.total / max_total * Decimal("100")).quantize(Decimal("0.1"))

    @property
    def grade(self):
        return grade_letter(self.percentage)

    @property
    def grade_point(self):
        return grade_point(self.percentage)


class MarkEntry(models.Model):
    """The score for one assessment component of a subject mark."""

    subject_mark = models.ForeignKey(SubjectMark, on_delete=models.CASCADE, related_name="entries")
    component = models.ForeignKey(AssessmentComponent, on_delete=models.PROTECT, related_name="entries")
    score = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("0"))

    class Meta:
        unique_together = [("subject_mark", "component")]

    def __str__(self):
        return f"{self.component.label}: {self.score}"

    def clean(self):
        if self.component_id and self.score is not None:
            if self.score < 0:
                raise ValidationError("A mark cannot be negative.")
            if self.score > self.component.max_score:
                raise ValidationError(
                    f"{self.component.label} cannot exceed {self.component.max_score}."
                )
