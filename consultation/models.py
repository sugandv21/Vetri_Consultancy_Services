from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class ConsultantSession(models.Model):

    REQUESTED = "REQUESTED"
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

    STATUS_CHOICES = [
        (REQUESTED, "Requested"),
        (SCHEDULED, "Scheduled"),
        (COMPLETED, "Completed"),
        (CANCELLED, "Cancelled"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")

    topic = models.CharField(max_length=200)
    message = models.TextField(blank=True)

    meeting_link = models.URLField(blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=REQUESTED)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.status}"
