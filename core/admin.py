from django.contrib import admin
from .models import Training, Enrollment, TrainingEnquiry, EnquiryMessage


@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_display = ("title", "duration", "fee", "is_active")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("user", "training", "enrolled_at")


@admin.register(TrainingEnquiry)
class TrainingEnquiryAdmin(admin.ModelAdmin):
    list_display = ("user", "training", "created_at")


@admin.register(EnquiryMessage)
class EnquiryMessageAdmin(admin.ModelAdmin):
    list_display = ("enquiry", "sender", "created_at")


