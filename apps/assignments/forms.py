"""Form for creating and editing class assignments."""
from django import forms

from apps.academics.models import SchoolClass, Subject, TeachingAssignment

from .models import Assignment


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ["title", "school_class", "subject", "teacher", "max_mark", "due_date", "description"]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user is not None and getattr(user, "is_teacher_role", False):
            # A teacher may only issue work to the classes and subjects they teach;
            # the owning teacher is set from their profile in the view.
            self.fields.pop("teacher", None)
            teacher = getattr(user, "teacher_profile", None)
            if teacher is not None:
                assignments = TeachingAssignment.objects.filter(teacher=teacher)
                self.fields["school_class"].queryset = SchoolClass.objects.filter(
                    pk__in=assignments.values_list("school_class_id", flat=True)
                )
                self.fields["subject"].queryset = Subject.objects.filter(
                    pk__in=assignments.values_list("subject_id", flat=True)
                )
            else:
                self.fields["school_class"].queryset = SchoolClass.objects.none()
                self.fields["subject"].queryset = Subject.objects.none()

    def clean(self):
        cleaned = super().clean()
        school_class = cleaned.get("school_class")
        subject = cleaned.get("subject")
        if school_class and subject and subject.grade != school_class.grade:
            self.add_error("subject", "Choose a subject that belongs to this class's grade.")
        return cleaned
