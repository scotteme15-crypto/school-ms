from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """An append-only record of security- and data-sensitive actions."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_logs"
    )
    user_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=32, blank=True)
    action = models.CharField(max_length=120)
    module = models.CharField(max_length=64, blank=True)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Audit log entry"

    def __str__(self):
        return f"{self.user_name or 'System'} — {self.action}"
