from django.contrib import admin
from .models import ConsultantSession


@admin.register(ConsultantSession)
class ConsultantSessionAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "trainer",
        "topic",
        "status",
        "scheduled_at",
        "created_at",
    )

    list_filter = ("status", "created_at", "trainer")

    search_fields = (
        "user__email",
        "trainer__email",
        "topic",
    )

    ordering = ("-created_at",)

    # ---------------- FORM LAYOUT ----------------
    fieldsets = (

        ("Candidate Request", {
            "fields": (
                "user",
                "topic",
                "message",
                "created_at",
            )
        }),

        ("Admin Scheduling", {
            "fields": (
                "trainer",
                "scheduled_at",
                "meeting_link",
            )
        }),

        ("Trainer Feedback", {
            "fields": (
                "feedback",
            )
        }),

        ("Admin Closure", {
            "fields": (
                "status",
            )
        }),
    )

    readonly_fields = ("created_at",)

    # prevent editing after closed
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status == "COMPLETED":
            return [field.name for field in self.model._meta.fields]
        return self.readonly_fields
