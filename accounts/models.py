from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.conf import settings


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
        return self.create_user(email, password, **extra_fields)


# class User(AbstractUser):
#     username = None
#     email = models.EmailField(unique=True)

#     FREE = "FREE"
#     PRO = "PRO"

#     SUBSCRIPTION_CHOICES = [
#         (FREE, "Free"),
#         (PRO, "Pro"),
#     ]

#     subscription_type = models.CharField(
#         max_length=10,
#         choices=SUBSCRIPTION_CHOICES,
#         default=FREE
#     )

#     USERNAME_FIELD = "email"
#     REQUIRED_FIELDS = []

#     objects = UserManager()

#     def is_pro(self):
#         return self.subscription_type == self.PRO

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


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


class User(AbstractUser):
    #  Remove username completely
    username = None

    #  Use email as login
    email = models.EmailField(unique=True)

    # Optional: Google provides this automatically
    full_name = models.CharField(max_length=100, blank=True)

    #  Subscription
    FREE = "FREE"
    PRO = "PRO"

    SUBSCRIPTION_CHOICES = [
        (FREE, "Free"),
        (PRO, "Pro"),
    ]

    subscription_type = models.CharField(
        max_length=10,
        choices=SUBSCRIPTION_CHOICES,
        default=FREE
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def is_pro(self):
        return self.subscription_type == self.PRO

    def __str__(self):
        return self.email



from django.db import models
from django.conf import settings


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
    experience = models.IntegerField(null=True, blank=True)
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


