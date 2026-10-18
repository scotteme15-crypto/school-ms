"""Forms for taking a class register: pick a class + date, then mark each student."""
from django import forms

from apps.academics.models import SchoolClass

from .models import ATTENDANCE_STATUS


def status_field_name(student_id):
    return f"status_{student_id}"


class AttendanceFilterForm(forms.Form):
    """Class and date selector (also used to validate the POST payload)."""

    school_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.all(),
        required=False,
        widget=forms.Select(attrs={"data-autosubmit": "", "aria-label": "Class"}),
    )
    date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "data-autosubmit": "", "aria-label": "Date"}),
    )


class AttendanceRecordForm(forms.Form):
    """One status select per active student in the chosen class."""

    def __init__(self, *args, students, **kwargs):
        super().__init__(*args, **kwargs)
        self.students = list(students)
        for student in self.students:
            self.fields[status_field_name(student.pk)] = forms.ChoiceField(
                choices=ATTENDANCE_STATUS,
                required=False,
                widget=forms.Select(attrs={"data-attendance-status": ""}),
            )

    def rows(self):
        return [{"student": student, "field": self[status_field_name(student.pk)]} for student in self.students]

    def status_values(self):
        """Yield ``(student, status)``; an unset choice defaults to present."""
        for student in self.students:
            yield student, (self.cleaned_data.get(status_field_name(student.pk)) or "present")
