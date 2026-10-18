"""Announcements and the school events calendar."""
from django.conf import settings
from django.db import models

AUDIENCE_CHOICES = [
    ("Everyone", "Everyone"),
    ("Students", "Students"),
    ("Teachers", "Teachers"),
    ("Grade 12", "Grade 12"),
    ("Parents", "Parents"),
]

PRIORITY_CHOICES = [("High", "High"), ("Normal", "Normal"), ("Low", "Low")]

EVENT_TYPE_CHOICES = [
    ("meeting", "Meeting"),
    ("exam", "Exam"),
    ("holiday", "Holiday"),
    ("sports", "Sports"),
    ("ceremony", "Ceremony"),
    ("registration", "Registration"),
]


class Announcement(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    audience = models.CharField(max_length=40, choices=AUDIENCE_CHOICES, default="Everyone")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="Normal")
    date = models.DateField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="announcements"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return self.title


class SchoolEvent(models.Model):
    title = models.CharField(max_length=200)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, default="meeting")
    date = models.DateField()
    location = models.CharField(max_length=120, blank=True)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["date"]

    def __str__(self):
        return self.title
