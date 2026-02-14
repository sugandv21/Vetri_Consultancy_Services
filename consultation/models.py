from django.db import models
from django.conf import settings


class ConsultantSession(models.Model):

    # ================= STATUS FLOW =================
    REQUESTED = "REQUESTED"
    SCHEDULED = "SCHEDULED"
    ATTENDED = "ATTENDED"      # trainer submitted feedback
    COMPLETED = "COMPLETED"    # admin verified
    CANCELLED = "CANCELLED"

    STATUS_CHOICES = [
        (REQUESTED, "Requested"),
        (SCHEDULED, "Scheduled"),
        (ATTENDED, "Attended"),
        (COMPLETED, "Completed"),
        (CANCELLED, "Cancelled"),
    ]

    # ================= USERS =================

    # Candidate
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="consultation_requests"
    )

    # Trainer
    trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_consultations",
        limit_choices_to={"is_staff": True, "is_superuser": False}
    )

    # ================= SESSION DETAILS =================
    topic = models.CharField(max_length=200)
    message = models.TextField(blank=True)

    meeting_link = models.URLField(blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)

    # ================= TRAINER ACTION =================
    feedback = models.TextField(blank=True)

    # ================= STATUS =================
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=REQUESTED
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "scheduled_at"]),
            models.Index(fields=["trainer", "status"]),
        ]

    def __str__(self):
        return f"{self.user} → {self.status}"
