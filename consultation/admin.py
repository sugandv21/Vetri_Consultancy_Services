


from django.contrib import admin
from .models import ConsultantSession


@admin.register(ConsultantSession)
class ConsultantSessionAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "topic",
        "status",
        "scheduled_at",
        "created_at",
    )

    list_filter = ("status", "created_at")

    search_fields = (
        "user__email",
        "topic",
    )

    ordering = ("-created_at",)

    # Fields visible in admin edit page
    fieldsets = (
        ("User Request", {
            "fields": (
                "user",
                "topic",
                "message",
                "created_at",
            )
        }),
        ("Consultant Scheduling", {
            "fields": (
                "status",
                "scheduled_at",
                "meeting_link",
            )
        }),
    )

    readonly_fields = ("created_at",)
