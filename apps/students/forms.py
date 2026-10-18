"""Forms for managing student records."""
from django import forms

from .models import Student


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            "student_id",
            "first_name",
            "middle_name",
            "last_name",
            "gender",
            "date_of_birth",
            "grade",
            "section",
            "school_class",
            "parent_name",
            "parent_phone",
            "email",
            "address",
            "admission_date",
            "status",
        ]
        labels = {
            "student_id": "Student ID",
            "date_of_birth": "Date of birth",
            "school_class": "Class",
            "parent_name": "Guardian name",
            "parent_phone": "Guardian phone",
            "admission_date": "Admission date",
        }
        widgets = {
            "student_id": forms.TextInput(attrs={"placeholder": "UNS-10A-01"}),
            "first_name": forms.TextInput(attrs={"placeholder": "First name"}),
            "middle_name": forms.TextInput(attrs={"placeholder": "Middle name"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Last name"}),
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "admission_date": forms.DateInput(attrs={"type": "date"}),
            "parent_name": forms.TextInput(attrs={"placeholder": "Guardian full name"}),
            "parent_phone": forms.TextInput(attrs={"placeholder": "+251 …"}),
            "email": forms.EmailInput(attrs={"placeholder": "student@example.com"}),
            "address": forms.TextInput(attrs={"placeholder": "Town, kebele…"}),
        }
