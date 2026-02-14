from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Profile, ResumeReview, Notification




@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("email",)

    list_display = (
        "email",
        "plan",
        "plan_status",
        "ai_requests_used",
        "job_applications_used",
        "is_staff",
    )

    list_filter = ("plan", "plan_status", "is_staff")

    search_fields = ("email", "full_name")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("full_name",)}),
        (
            "Subscription",
            {
                "fields": (
                    "plan",
                    "plan_status",
                    "plan_start",
                    "plan_end",
                    "usage_reset_date",
                    "ai_requests_used",
                    "job_applications_used",
                    "mentor_sessions_used",
                )
            },
        ),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )

    filter_horizontal = ()
    readonly_fields = ("date_joined",)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "mobile_number", "experience", "location")
    search_fields = ("user__email", "mobile_number")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "user",
        "is_admin_alert",
        "is_read",
        "created_at",
    )

    list_filter = (
        "is_admin_alert",
        "is_read",
        "created_at",
    )

    search_fields = (
        "title",
        "message",
        "user__email",
    )

    ordering = ("-created_at",)

    actions = ["mark_as_read"]

    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)

    
@admin.register(ResumeReview)
class ResumeReviewAdmin(admin.ModelAdmin):
    list_display = ("profile", "review_type", "created_at")
    list_filter = ("review_type",)
    search_fields = ("profile__user__email",)
    ordering = ("-created_at",)

