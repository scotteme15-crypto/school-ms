"""Forms for announcements and the school events calendar."""
from django import forms

from .models import Announcement, SchoolEvent


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ["title", "body", "audience", "priority", "date"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 6}),
            "date": forms.DateInput(attrs={"type": "date"}),
        }


class SchoolEventForm(forms.ModelForm):
    class Meta:
        model = SchoolEvent
        fields = ["title", "event_type", "date", "location", "note"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "note": forms.Textarea(attrs={"rows": 4}),
        }
