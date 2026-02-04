from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


from django.db import models

class Training(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    duration = models.CharField(max_length=100)
    fee = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(
        upload_to="training_images/",
        blank=True,
        null=True
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title



class Enrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    training = models.ForeignKey(Training, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "training")

    def __str__(self):
        return f"{self.user} → {self.training}"


class TrainingEnquiry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    training = models.ForeignKey("Training", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Enquiry: {self.user} - {self.training}"


class EnquiryMessage(models.Model):
    enquiry = models.ForeignKey(
        TrainingEnquiry,
        related_name="messages",
        on_delete=models.CASCADE
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def is_admin(self):
        return self.sender.is_staff

    def __str__(self):
        return f"Message by {self.sender}"