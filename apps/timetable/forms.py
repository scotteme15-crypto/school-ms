"""Form for creating and editing weekly timetable slots."""
from django import forms

from .models import TimetableSlot


class TimetableSlotForm(forms.ModelForm):
    class Meta:
        model = TimetableSlot
        fields = [
            "school_class",
            "day",
            "start_time",
            "end_time",
            "subject",
            "teacher",
            "room",
            "academic_year",
        ]
        widgets = {
            "start_time": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "end_time": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
        }

    def clean(self):
        cleaned = super().clean()
        # Replace the raw unique_together message with a friendlier clash error.
        self._validate_unique = False

        start_time = cleaned.get("start_time")
        end_time = cleaned.get("end_time")
        if start_time and end_time and end_time <= start_time:
            self.add_error("end_time", "The end time must be after the start time.")

        school_class = cleaned.get("school_class")
        day = cleaned.get("day")
        if school_class and day and start_time:
            clash = TimetableSlot.objects.filter(
                school_class=school_class, day=day, start_time=start_time
            )
            if self.instance.pk:
                clash = clash.exclude(pk=self.instance.pk)
            if clash.exists():
                self.add_error(
                    "start_time",
                    "This class already has a lesson at that time on that day.",
                )
        return cleaned
