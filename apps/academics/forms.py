"""Forms for the school structure: years, semesters, classes, subjects, exams,
grading bands, assessment components, teaching assignments and school settings."""
from datetime import date

from django import forms

from apps.results.models import Exam

from .models import (
    AcademicYear,
    AssessmentComponent,
    GradingBand,
    SchoolClass,
    SchoolSettings,
    Semester,
    Subject,
    TeachingAssignment,
)

DATE_ATTRS = {"type": "date"}
TIME_ATTRS = {"type": "time"}


class AcademicYearForm(forms.ModelForm):
    class Meta:
        model = AcademicYear
        fields = ["name", "start_date", "end_date", "is_current"]
        labels = {"name": "Academic year", "is_current": "Set as the current year"}
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "2025/26"}),
            "start_date": forms.DateInput(attrs=DATE_ATTRS),
            "end_date": forms.DateInput(attrs=DATE_ATTRS),
        }


class SemesterForm(forms.ModelForm):
    class Meta:
        model = Semester
        fields = ["academic_year", "name", "order", "start_date", "end_date", "is_current"]
        labels = {"order": "Order", "is_current": "Set as the current semester"}
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Semester I"}),
            "start_date": forms.DateInput(attrs=DATE_ATTRS),
            "end_date": forms.DateInput(attrs=DATE_ATTRS),
        }


class GradingBandForm(forms.ModelForm):
    class Meta:
        model = GradingBand
        fields = ["letter", "min_score", "point", "remark", "order"]
        labels = {"min_score": "Minimum score", "point": "Grade point"}
        widgets = {
            "letter": forms.TextInput(attrs={"placeholder": "A+"}),
            "remark": forms.TextInput(attrs={"placeholder": "Excellent"}),
        }


class AssessmentComponentForm(forms.ModelForm):
    class Meta:
        model = AssessmentComponent
        fields = ["key", "label", "max_score", "weight_percent", "order"]
        labels = {"max_score": "Maximum score", "weight_percent": "Weight (%)"}
        widgets = {
            "key": forms.TextInput(attrs={"placeholder": "midterm"}),
            "label": forms.TextInput(attrs={"placeholder": "Midterm exam"}),
        }


class SchoolSettingsForm(forms.ModelForm):
    class Meta:
        model = SchoolSettings
        fields = [
            "school_name",
            "motto",
            "address",
            "phone",
            "email",
            "website",
            "pass_mark",
            "show_school_rank",
            "rank_tie_policy",
            "current_academic_year",
            "current_semester",
        ]
        labels = {
            "pass_mark": "Pass mark",
            "show_school_rank": "Let students see their school-wide rank",
            "rank_tie_policy": "Rank tie policy",
        }
        widgets = {
            "school_name": forms.TextInput(attrs={"placeholder": "Bariso Dukale Secondary School"}),
            "motto": forms.TextInput(attrs={"placeholder": "Knowledge · Integrity · Service"}),
            "address": forms.TextInput(attrs={"placeholder": "P.O. Box 123, Addis Ababa"}),
            "website": forms.TextInput(attrs={"placeholder": "https://example.edu"}),
        }


class SchoolClassForm(forms.ModelForm):
    class Meta:
        model = SchoolClass
        fields = ["grade", "section", "room", "capacity", "academic_year", "homeroom_teacher"]
        labels = {"room": "Room", "homeroom_teacher": "Homeroom teacher"}
        widgets = {"room": forms.TextInput(attrs={"placeholder": "Block A · R12"})}


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ["code", "name", "grade", "credit", "department", "teacher", "is_active"]
        labels = {"code": "Subject code", "credit": "Credits", "is_active": "Active"}
        widgets = {
            "code": forms.TextInput(attrs={"placeholder": "MAT"}),
            "name": forms.TextInput(attrs={"placeholder": "Mathematics"}),
        }


class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = [
            "name",
            "exam_type",
            "grade",
            "subject",
            "date",
            "start_time",
            "end_time",
            "room",
            "instructions",
            "academic_year",
            "semester",
        ]
        labels = {"exam_type": "Exam type", "start_time": "Start time", "end_time": "End time"}
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "End of term examination"}),
            "date": forms.DateInput(attrs=DATE_ATTRS),
            "start_time": forms.TimeInput(attrs=TIME_ATTRS),
            "end_time": forms.TimeInput(attrs=TIME_ATTRS),
            "room": forms.TextInput(attrs={"placeholder": "Main hall"}),
            "instructions": forms.Textarea(attrs={"rows": 3, "placeholder": "Seating, materials, conduct…"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["date"].initial = self.fields["date"].initial or date.today()


class TeachingAssignmentForm(forms.ModelForm):
    class Meta:
        model = TeachingAssignment
        fields = ["teacher", "subject", "school_class", "academic_year"]
        labels = {"school_class": "Class"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["subject"].queryset = Subject.objects.filter(is_active=True)
        self.fields["school_class"].queryset = SchoolClass.objects.all()
