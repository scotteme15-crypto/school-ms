from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Kind(models.TextChoices):
        RESULT = "result", "Result"
        WARNING = "warning", "Warning"
        ANNOUNCEMENT = "announcement", "Announcement"
        EXAM = "exam", "Exam"
        SYSTEM = "system", "System"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.SYSTEM)
    url = models.CharField(max_length=300, blank=True)
    read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
