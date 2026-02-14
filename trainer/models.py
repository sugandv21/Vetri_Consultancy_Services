from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class ConsultationSession(models.Model):

    STATUS_CHOICES = [
        ("SCHEDULED", "Scheduled"),
        ("COMPLETED", "Completed"),
        ("MISSED", "Missed"),
    ]

    candidate = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="trainer_sessions"   # changed
    )

    trainer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="trainer_assigned_sessions"  # changed
    )

    topic = models.CharField(max_length=200)
    meeting_link = models.URLField()

    scheduled_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="SCHEDULED")

    feedback = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.candidate} - {self.topic}"
