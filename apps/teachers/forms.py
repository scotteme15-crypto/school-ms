"""Forms for managing teacher records."""
from django import forms

from .models import Teacher


class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = [
            "teacher_id",
            "name",
            "gender",
            "department",
            "qualification",
            "phone",
            "email",
            "employment_date",
            "status",
        ]
        labels = {
            "teacher_id": "Staff ID",
            "department": "Department",
            "employment_date": "Employment date",
        }
        widgets = {
            "teacher_id": forms.TextInput(attrs={"placeholder": "TCH-01"}),
            "name": forms.TextInput(attrs={"placeholder": "Full name"}),
            "qualification": forms.TextInput(attrs={"placeholder": "B.Ed. Mathematics"}),
            "phone": forms.TextInput(attrs={"placeholder": "+251 …"}),
            "email": forms.EmailInput(attrs={"placeholder": "teacher@example.com"}),
            "employment_date": forms.DateInput(attrs={"type": "date"}),
        }
