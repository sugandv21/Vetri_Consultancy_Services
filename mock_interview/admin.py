from django.contrib import admin
from .models import MockInterview, InterviewFeedback


@admin.register(MockInterview)
class MockInterviewAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "candidate",
        "consultant",
        "preferred_date",
        "preferred_time",
        "scheduled_datetime",
        "status",
    )

    list_filter = ("status", "preferred_date", "preferred_time")

    search_fields = ("candidate__email", "candidate__username")

    ordering = ("-preferred_date",)

    fieldsets = (

        ("Candidate Request", {
            "fields": ("candidate", "preferred_date", "preferred_time")
        }),

        ("Admin Scheduling", {
            "fields": ("consultant", "scheduled_datetime", "status")
        }),

        ("Meeting", {
            "fields": ("meeting_link",)
        }),
    )


@admin.register(InterviewFeedback)
class InterviewFeedbackAdmin(admin.ModelAdmin):

    list_display = ("interview", "rating", "created_at")
    readonly_fields = ("created_at",)
