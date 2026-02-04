from django.contrib import admin
from .models import Job, JobApplication, SavedJob


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "company_name",
        "location",
        "job_type",
        "visibility",
        "tag_fresher",
        "status",
        "created_by",
        "created_at",
    )

    # ✅ All fields here EXIST in Job model
    list_filter = (
        "status",
        "job_type",
        "visibility",
        "tag_fresher",
    )

    search_fields = (
        "title",
        "company_name",
        "skills",
        "location",
    )

    readonly_fields = ("created_at",)

    ordering = ("-created_at",)


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "job",
        "short_job_description",
        "status",
        "applied_at",
    )

    list_filter = (
        "status",
        "applied_at",
    )

    search_fields = (
        "user__username",
        "user__email",
        "job__title",
        "job__company_name",
    )

    readonly_fields = ("applied_at",)

    def short_job_description(self, obj):
        return obj.job.description[:100]

    short_job_description.short_description = "Job Description"


@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "job",
        "saved_at",
    )

    readonly_fields = ("saved_at",)

# from django.contrib import admin
# from .models import Job, JobApplication


# @admin.register(Job)
# class JobAdmin(admin.ModelAdmin):
#     list_display = (
#         "title",
#         "company_name",
#         "location",
#         "job_type",
#         "status",
#         "visibility",
#         "created_by",
#         "created_at",
#     )
#     list_filter = ("status", "job_type", "visibility", "tag_fresher")
#     search_fields = ("title", "company_name", "skills", "location")
#     readonly_fields = ("created_at",)
#     ordering = ("-created_at",)


# @admin.register(JobApplication)
# class JobApplicationAdmin(admin.ModelAdmin):
#     list_display = (
#         "user",
#         "job",
#         "job_description",
#         "status",
#         "applied_at",
#     )

#     list_filter = ("status", "applied_at")
#     search_fields = (
#         "user__username",
#         "user__email",
#         "job__title",
#         "job__company_name",
#     )

#     readonly_fields = ("applied_at",)

#     def job_description(self, obj):
#         return obj.job.description[:100]  

#     job_description.short_description = "Job Description"
