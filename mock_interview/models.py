from django.db import models
from django.conf import settings


class MockInterview(models.Model):

    STATUS_CHOICES = [
        ("pending","Pending"),
        ("scheduled","Scheduled"),
        ("in_progress","In Progress"),
        ("completed","Completed"),
    ]

    TIME_SLOT_CHOICES = [
        ("morning","Morning"),
        ("afternoon","Afternoon"),
        ("evening","Evening"),
    ]

    # Candidate
    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="candidate_mock_interviews"
    )

    # Trainer
    consultant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trainer_mock_interviews"
    )

    # Booking preference
    preferred_date = models.DateField(null=True,blank=True)
    preferred_time = models.CharField(max_length=20,choices=TIME_SLOT_CHOICES,null=True,blank=True)

    # Scheduled by admin
    scheduled_datetime = models.DateTimeField(null=True,blank=True)
    meeting_link = models.URLField(blank=True,null=True)

    # Interview state
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default="pending")

    # tracking
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.candidate} - {self.status}"


class InterviewFeedback(models.Model):

    interview = models.OneToOneField(MockInterview,on_delete=models.CASCADE)

    rating = models.IntegerField()
    communication = models.IntegerField(default=0)
    technical = models.IntegerField(default=0)
    problem_solving = models.IntegerField(default=0)

    strengths = models.TextField()
    improvements = models.TextField()
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def average_score(self):
        return round((self.communication + self.technical + self.problem_solving) / 3, 1)
