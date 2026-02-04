from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "Profile"


class UserAdmin(BaseUserAdmin):
    model = User

    list_display = (
        "email",
        "subscription_type",
        "is_staff",
        "is_superuser",
        "is_active",
    )

    list_filter = (
        "subscription_type",
        "is_staff",
        "is_superuser",
        "is_active",
    )

    search_fields = ("email",)
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Subscription", {"fields": ("subscription_type",)}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "subscription_type",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )

    inlines = (ProfileInline,)


admin.site.register(User, UserAdmin)
