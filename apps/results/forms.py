"""Forms for creating result sheets and entering marks.

Marks are validated on the server: every score is bound by its assessment
component's ``max_score`` through the form field, and again by
``MarkEntry.clean()`` when the row is saved.
"""
from decimal import Decimal

from django import forms

from apps.academics.models import AssessmentComponent

from .models import MarkEntry, ResultSheet


def score_field_name(subject_mark_id, component_id):
    return f"score_{subject_mark_id}_{component_id}"


def remark_field_name(subject_mark_id):
    return f"remark_{subject_mark_id}"


class ResultSheetForm(forms.ModelForm):
    """Create or edit a result sheet (one class + subject + exam type)."""

    class Meta:
        model = ResultSheet
        fields = ["academic_year", "semester", "school_class", "subject", "teacher", "exam_type", "exam"]

    def __init__(self, *args, lock_teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        if lock_teacher is not None:
            # A teacher may only ever create sheets for themselves.
            self.fields["teacher"].queryset = self.fields["teacher"].queryset.filter(pk=lock_teacher.pk)
            self.fields["teacher"].initial = lock_teacher.pk

    def clean(self):
        cleaned = super().clean()
        school_class = cleaned.get("school_class")
        subject = cleaned.get("subject")
        if school_class and subject and subject.grade != school_class.grade:
            self.add_error("subject", "Choose a subject that matches the class grade.")
        return cleaned


class MarksEntryForm(forms.Form):
    """One decimal input per student per assessment component."""

    def __init__(self, *args, sheet, subject_marks, components, **kwargs):
        super().__init__(*args, **kwargs)
        self.sheet = sheet
        self.subject_marks = list(subject_marks)
        self.components = list(components)
        for mark in self.subject_marks:
            for component in self.components:
                self.fields[score_field_name(mark.pk, component.pk)] = forms.DecimalField(
                    required=False,
                    min_value=Decimal("0"),
                    max_value=component.max_score,
                    max_digits=6,
                    decimal_places=2,
                    error_messages={
                        "min_value": f"{component.label} cannot be negative.",
                        "max_value": f"{component.label} cannot exceed {component.max_score}.",
                        "invalid": f"Enter a valid mark for {component.label}.",
                    },
                    widget=forms.NumberInput(
                        attrs={
                            "class": "mark-input",
                            "step": "0.01",
                            "min": "0",
                            "max": str(component.max_score),
                            "inputmode": "decimal",
                            "data-score": "",
                            "data-max": str(component.max_score),
                        }
                    ),
                )
            self.fields[remark_field_name(mark.pk)] = forms.CharField(
                required=False,
                max_length=200,
                widget=forms.TextInput(attrs={"placeholder": "Optional remark"}),
            )

    def rows(self):
        """Bound rows ready to render: student + one BoundField per component."""
        rows = []
        for mark in self.subject_marks:
            cells = [
                {"component": component, "field": self[score_field_name(mark.pk, component.pk)]}
                for component in self.components
            ]
            rows.append(
                {
                    "mark": mark,
                    "student": mark.student,
                    "cells": cells,
                    "remark": self[remark_field_name(mark.pk)],
                    "total": mark.total,
                    "percentage": mark.percentage,
                    "grade": mark.grade,
                }
            )
        return rows

    def score_values(self):
        """Yield ``(subject_mark, component, value)`` for every provided mark."""
        for mark in self.subject_marks:
            for component in self.components:
                value = self.cleaned_data.get(score_field_name(mark.pk, component.pk))
                if value is not None:
                    yield mark, component, value

    def remark_values(self):
        for mark in self.subject_marks:
            remark = self.cleaned_data.get(remark_field_name(mark.pk), "")
            yield mark, (remark or "")

    def save(self):
        """Persist validated scores and remarks onto existing SubjectMark rows."""
        for mark, component, value in self.score_values():
            entry, _ = MarkEntry.objects.get_or_create(subject_mark=mark, component=component)
            entry.score = value
            entry.full_clean(exclude=["subject_mark", "component"])
            entry.save()
        for mark, remark in self.remark_values():
            if remark != mark.remark:
                mark.remark = remark
                mark.save(update_fields=["remark"])


def build_marks_initial(subject_marks):
    """Initial values for MarksEntryForm from existing entries and remarks."""
    initial = {}
    for mark in subject_marks:
        for entry in mark.entries.all():
            initial[score_field_name(mark.pk, entry.component_id)] = entry.score
        if mark.remark:
            initial[remark_field_name(mark.pk)] = mark.remark
    return initial


def components_payload(components):
    return [{"key": c.key, "label": c.label, "max": float(c.max_score)} for c in components]


def bands_payload(bands):
    return [{"letter": b.letter, "min": float(b.min_score)} for b in bands]


def ensure_subject_marks(sheet):
    """Create the SubjectMark rows for every active student in the class."""
    from .models import SubjectMark

    for student in sheet.school_class.students.filter(status="Active"):
        SubjectMark.objects.get_or_create(result_sheet=sheet, student=student)


def default_components():
    return list(AssessmentComponent.objects.all())
