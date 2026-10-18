"""Daily attendance registers."""
from django.db import models

from apps.academics.models import AcademicYear

ATTENDANCE_STATUS = [
    ("present", "Present"),
    ("absent", "Absent"),
    ("late", "Late"),
    ("excused", "Excused"),
]


class AttendanceSession(models.Model):
    date = models.DateField(db_index=True)
    school_class = models.ForeignKey("academics.SchoolClass", on_delete=models.CASCADE, related_name="attendance_sessions")
    teacher = models.ForeignKey(
        "teachers.Teacher", null=True, blank=True, on_delete=models.SET_NULL, related_name="attendance_sessions"
    )
    academic_year = models.ForeignKey(
        AcademicYear, null=True, blank=True, on_delete=models.SET_NULL, related_name="attendance_sessions"
    )
    taken_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]
        unique_together = [("date", "school_class")]

    def __str__(self):
        return f"{self.school_class.name} · {self.date}"

    @property
    def counts(self):
        tally = {"present": 0, "absent": 0, "late": 0, "excused": 0}
        for record in self.records.all():
            tally[record.status] = tally.get(record.status, 0) + 1
        return tally


class AttendanceRecord(models.Model):
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name="records")
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="attendance_records")
    status = models.CharField(max_length=10, choices=ATTENDANCE_STATUS, default="present")

    class Meta:
        unique_together = [("session", "student")]
        ordering = ["student__first_name"]

    def __str__(self):
        return f"{self.student.full_name} — {self.get_status_display()}"
