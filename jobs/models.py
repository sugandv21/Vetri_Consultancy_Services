from django.db import models
from django.conf import settings


class Job(models.Model):

    JOB_TYPE_CHOICES = [
        ('FT', 'Full-time'),
        ('IN', 'Internship'),
        ('CT', 'Contract'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('PUBLISHED', 'Published'),
        ('REJECTED', 'Rejected'),
    ]

    VISIBILITY_CHOICES = [
        ('FREE', 'Free'),
        ('PRO', 'Pro'),
    ]

    title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200)
    location = models.CharField(max_length=100)

    experience_min = models.PositiveIntegerField()
    experience_max = models.PositiveIntegerField()

    # ✅ SINGLE source of truth for Free / Pro
    visibility = models.CharField(
        max_length=10,
        choices=VISIBILITY_CHOICES,
        default='FREE'
    )

    job_type = models.CharField(
        max_length=2,
        choices=JOB_TYPE_CHOICES
    )

    description = models.TextField()
    skills = models.CharField(max_length=255)
    deadline = models.DateField()

    # ✅ Fresher tag (admin-safe)
    tag_fresher = models.BooleanField(default=False)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="jobs_created"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.company_name}"


# =========================
# Saved Jobs
# =========================
class SavedJob(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_jobs"
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="saved_by"
    )
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "job")
        ordering = ["-saved_at"]

    def __str__(self):
        return f"{self.user} saved {self.job}"


# =========================
# Job Applications
# =========================
class JobApplication(models.Model):

    STATUS_CHOICES = [
        ("APPLIED", "Applied"),
        ("IN_REVIEW", "In Review"),
        ("INTERVIEW", "Interview"),
        ("CLOSED", "Closed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_applications"
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="applications"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="APPLIED"
    )

    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "job")
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.user} applied for {self.job}"

