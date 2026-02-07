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

    mentor_name = models.CharField(max_length=150, blank=True)
    mentor_email = models.EmailField(blank=True)
    course_timing = models.CharField(max_length=150, blank=True)
    training_link = models.URLField(blank=True) 

    certificate = models.FileField(
        upload_to="certificates/",
        blank=True,
        null=True
    )

    is_completed = models.BooleanField(default=False)

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
    
    
class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.email}"

from django.db import models

class HomeHero(models.Model):
    title = models.CharField(max_length=200)
    highlight_text = models.CharField(max_length=100, blank=True)
    subtitle = models.TextField()

    background_image = models.ImageField(upload_to="home/hero/")

    overlay_opacity = models.FloatField(
        default=0.4,
        help_text="0 = no overlay, 1 = fully dark"
    )

    is_active = models.BooleanField(default=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Homepage Hero Section"
        verbose_name_plural = "Homepage Hero Section"

    def __str__(self):
        return self.title
class FeatureSection(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title
    
class HomeFeature(models.Model):

    LINK_TYPE = (
        ("enquiry", "Career Enquiry Page"),
        ("jobs", "Jobs Page"),
        ("training", "Training Page"),
    )

    section = models.ForeignKey(
        FeatureSection,
        on_delete=models.CASCADE,
        related_name="features",
        default=1
    )



    title = models.CharField(max_length=100)
    description = models.TextField()

    link_type = models.CharField(max_length=20, choices=LINK_TYPE)

    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title



class SiteStatistic(models.Model):
    label = models.CharField(max_length=100)
    value = models.PositiveIntegerField()
    suffix = models.CharField(max_length=10, blank=True, help_text="Example: + or %")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]
        verbose_name = "Homepage Statistic"
        verbose_name_plural = "Homepage Statistics"

    def __str__(self):
        return f"{self.label} - {self.value}{self.suffix}"

class HomeCTA(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.TextField(blank=True)

    button_text = models.CharField(max_length=50, default="Create Free Account")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Homepage Bottom CTA"
        verbose_name_plural = "Homepage Bottom CTA"

    def __str__(self):
        return self.title

class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()

    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.question

from django.db import models

class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    designation = models.CharField(max_length=150, blank=True)
    company = models.CharField(max_length=150, blank=True)
    message = models.TextField()
    photo = models.ImageField(upload_to="testimonials/")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class AboutPage(models.Model):
    title = models.CharField(max_length=200, default="About Us")
    subtitle = models.CharField(max_length=255, blank=True)

    section_title = models.CharField(max_length=150, default="Who We Are")

    content_1 = models.TextField(blank=True)
    content_2 = models.TextField(blank=True)
    content_3 = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "About Page"
        verbose_name_plural = "About Page"

    def __str__(self):
        return self.title
    
    
class ServicePage(models.Model):
    title = models.CharField(max_length=120, default="Our Services")
    subtitle = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return "Services Page"


class ServiceItem(models.Model):
    page = models.ForeignKey(ServicePage, on_delete=models.CASCADE, related_name="services")
    name = models.CharField(max_length=120)
    description = models.TextField()
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


class PricingPage(models.Model):
    title = models.CharField(max_length=120, default="Pricing Plans")
    subtitle = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return "Pricing Page"


class PricingPlan(models.Model):
    page = models.ForeignKey(PricingPage, on_delete=models.CASCADE, related_name="plans")
    name = models.CharField(max_length=50)
    price = models.CharField(max_length=50)
    description = models.CharField(max_length=120, blank=True)

    badge = models.CharField(max_length=50, blank=True)  # Most Popular
    button_text = models.CharField(max_length=50, default="Choose Plan")

    is_current = models.BooleanField(default=False)
    is_highlighted = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


class PricingFeature(models.Model):
    plan = models.ForeignKey(PricingPlan, on_delete=models.CASCADE, related_name="features")
    text = models.CharField(max_length=150)
    included = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.text
