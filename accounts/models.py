from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from django.contrib.auth.models import BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(email, password, **extra_fields)


#subscription section
class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=100, blank=True)

    # ---------------------------
    # PLAN TYPES (What they bought)
    # ---------------------------
    FREE = "FREE"
    PRO = "PRO"
    PRO_PLUS = "PRO_PLUS"

    PLAN_CHOICES = [
        (FREE, "Free"),
        (PRO, "Pro"),
        (PRO_PLUS, "Pro Plus"),
    ]

    plan = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        default=FREE
    )

    # ---------------------------
    # PLAN STATUS (Billing state)
    # ---------------------------
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    TRIAL = "TRIAL"

    PLAN_STATUS = [
        (ACTIVE, "Active"),
        (EXPIRED, "Expired"),
        (CANCELLED, "Cancelled"),
        (TRIAL, "Trial"),
    ]

    plan_status = models.CharField(
        max_length=20,
        choices=PLAN_STATUS,
        default=TRIAL
    )

    # ---------------------------
    # BILLING DATES
    # ---------------------------
    plan_start = models.DateTimeField(null=True, blank=True)
    plan_end = models.DateTimeField(null=True, blank=True)

    # ---------------------------
    # USAGE TRACKING (QUOTAS RESET MONTHLY)
    # ---------------------------
    ai_requests_used = models.IntegerField(default=0)
    job_applications_used = models.IntegerField(default=0)
    mentor_sessions_used = models.IntegerField(default=0)

    usage_reset_date = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    # ---------------------------
    # HELPERS
    # ---------------------------
    def is_pro(self):
        return self.plan in [self.PRO, self.PRO_PLUS] and self.plan_status == self.ACTIVE

    def is_pro_plus(self):
        return self.plan == self.PRO_PLUS and self.plan_status == self.ACTIVE

    def can_use_ai(self):
        if self.plan == self.FREE:
            return False
        if self.plan == self.PRO:
            return self.ai_requests_used < 50
        return True  # unlimited for pro plus
    
    def can_get_free_training(self):
        """
        Only PRO_PLUS users get 1 free training
        """
        if self.plan != self.PRO_PLUS or self.plan_status != self.ACTIVE:
            return False

        from core.models import Enrollment
        free_used = Enrollment.objects.filter(user=self).count()

        return free_used == 0


    def __str__(self):
        return self.email



class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    # Basic info
    full_name = models.CharField(max_length=100, blank=True)
    mobile_number = models.CharField(max_length=15, blank=True)

    # Professional info
    experience = models.PositiveIntegerField(default=0)

    location = models.CharField(max_length=100, blank=True)
    skills = models.CharField(max_length=255, blank=True)

    # Resume
    resume = models.FileField(
        upload_to="resumes/",
        blank=True,
        null=True
    )

    # ✅ Track one-time profile completion email
    completion_email_sent = models.BooleanField(default=False)

    def completion_percentage(self):
        """
        Calculates profile completion percentage accurately.
        Safe for Google login users and normal signup users.
        """

        filled = 0
        total = 6  # total number of profile fields

        if self.full_name and self.full_name.strip():
            filled += 1

        if self.mobile_number and self.mobile_number.strip():
            filled += 1

        # experience can be 0, so check None only
        if self.experience is not None:
            filled += 1

        if self.location and self.location.strip():
            filled += 1

        if self.skills and self.skills.strip():
            filled += 1

        # FileField must be checked via name
        if self.resume and self.resume.name:
            filled += 1

        return int((filled / total) * 100)

    def __str__(self):
        return f"{self.user.email} Profile"

    
def debug_completion(self):
    return {
        "full_name": bool(self.full_name and self.full_name.strip()),
        "mobile_number": bool(self.mobile_number and self.mobile_number.strip()),
        "experience": self.experience is not None,
        "location": bool(self.location and self.location.strip()),
        "skills": bool(self.skills and self.skills.strip()),
        "resume": bool(self.resume and self.resume.name),
    }


#resume review
class ResumeReview(models.Model):

    BASIC = "BASIC"
    ADVANCED = "ADVANCED"

    REVIEW_TYPE = [
        (BASIC, "Pro Suggestion"),
        (ADVANCED, "Pro Plus Optimization"),
    ]

    profile = models.ForeignKey(
        "accounts.Profile",
        on_delete=models.CASCADE,
        related_name="resume_reviews"
    )

    review_type = models.CharField(max_length=20, choices=REVIEW_TYPE)
    feedback = models.TextField()
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("profile", "review_type")

    def __str__(self):
        return f"{self.profile.user.email} - {self.review_type}"


#notfication
class Notification(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True
    )


    title = models.CharField(max_length=200)
    message = models.TextField()

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.title}"



class Payment(models.Model):

    PAYMENT_TYPE = [
        ("PLAN", "Subscription Plan"),
        ("TRAINING", "Training Purchase"),
    ]

    STATUS = [
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS)

    training = models.ForeignKey(
        "core.Training",
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.payment_type} - {self.amount}"


class SubscriptionPricing(models.Model):

    PLAN_CHOICES = [
        ("PRO", "Pro"),
        ("PRO_PLUS", "Pro Plus"),
    ]

    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, unique=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.plan} - ₹{self.price}"
