"""Weekly class timetables."""
from django.db import models

from apps.academics.models import AcademicYear

DAY_CHOICES = [
    ("Monday", "Monday"),
    ("Tuesday", "Tuesday"),
    ("Wednesday", "Wednesday"),
    ("Thursday", "Thursday"),
    ("Friday", "Friday"),
]


class TimetableSlot(models.Model):
    school_class = models.ForeignKey("academics.SchoolClass", on_delete=models.CASCADE, related_name="slots")
    day = models.CharField(max_length=10, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    subject = models.ForeignKey("academics.Subject", null=True, blank=True, on_delete=models.SET_NULL, related_name="slots")
    teacher = models.ForeignKey(
        "teachers.Teacher", null=True, blank=True, on_delete=models.SET_NULL, related_name="timetable_slots"
    )
    room = models.CharField(max_length=20, blank=True)
    academic_year = models.ForeignKey(
        AcademicYear, null=True, blank=True, on_delete=models.SET_NULL, related_name="slots"
    )

    class Meta:
        ordering = ["school_class__grade", "school_class__section", "day", "start_time"]
        unique_together = [("school_class", "day", "start_time")]

    def __str__(self):
        return f"{self.school_class.name} · {self.day} {self.start_time:%H:%M}"
