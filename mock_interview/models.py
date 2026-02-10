from django.db import models
from django.conf import settings


class MockInterview(models.Model):

    STATUS_CHOICES = [
        ("pending","Pending"),
        ("scheduled","Scheduled"),
        ("completed","Completed"),
    ]

    TIME_SLOT_CHOICES = [
        ("morning","Morning"),
        ("afternoon","Afternoon"),
        ("evening","Evening"),
    ]

    # IMPORTANT FIX HERE
    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="candidate_mock_interviews"
    )

    consultant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="consultant_mock_interviews"
    )



    # NEW
    preferred_date = models.DateField(null=True,blank=True)
    preferred_time = models.CharField(max_length=20,choices=TIME_SLOT_CHOICES,null=True,blank=True)
    scheduled_datetime = models.DateTimeField(null=True,blank=True)

    meeting_link = models.URLField(blank=True,null=True)
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default="pending")


class InterviewFeedback(models.Model):
    interview = models.OneToOneField(MockInterview,on_delete=models.CASCADE)
    rating = models.IntegerField()
    strengths = models.TextField()
    improvements = models.TextField()
    notes = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
