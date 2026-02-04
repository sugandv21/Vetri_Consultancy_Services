from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User
from accounts.decorators import admin_required
from django.contrib.auth.decorators import login_required
from .models import Profile
from .decorators import staff_required

@admin_required
def post_job(request):
    return render(request, "jobs/post_job.html")

def login_user(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        if not email or not password:
            messages.error(request, "Email and password are required.")
            return redirect("login")

        user = authenticate(request, email=email, password=password)

        if user is None:
            messages.error(request, "Invalid email or password.")
            return redirect("login")

        login(request, user)
        messages.success(request, "Login successful.")
        return redirect("dashboard")

    return render(request, "accounts/login.html")

from django.contrib.auth import authenticate, login

def register_user(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm = request.POST.get("confirm_password")
        mobile = request.POST.get("mobile_number")
        subscription = request.POST.get("subscription", User.FREE)

        if not all([full_name, email, password, confirm, mobile]):
            messages.error(request, "All fields are required.")
            return redirect("register")

        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect("register")

        user = User.objects.create_user(
            email=email,
            password=password,
            subscription_type=subscription,
        )

        # Profile already created by signal
        profile = user.profile
        profile.full_name = full_name
        profile.mobile_number = mobile
        profile.save()        

        #  Authenticate user FIRST
        user = authenticate(request, email=email, password=password)

        #  Then login (no backend error)
        if user is not None:
            login(request, user)

        if subscription == User.PRO:
            return redirect("payment")

        return redirect("profile_wizard")

    return render(request, "accounts/register.html")




@login_required
def payment(request):
    # Block FREE users
    if request.user.subscription_type != User.PRO:
        return redirect("dashboard")

    if request.method == "POST":
        # Fake payment success
        messages.success(request, "Payment successful! Welcome to Pro 🎉")
        return redirect("profile_wizard")

    return render(request, "accounts/payment.html")



def logout_user(request):
    logout(request)
    messages.success(request, "You have logged out successfully.")
    return redirect("login")



# @login_required
# def profile_wizard(request):
#     profile = request.user.profile

#     if request.method == "POST":
#         profile.full_name = request.POST.get("full_name")
#         profile.experience = request.POST.get("experience")
#         profile.location = request.POST.get("location")
#         profile.skills = request.POST.get("skills")
#         profile.save()

#         messages.success(request, "Profile updated successfully.")
#         return redirect("dashboard")

#     return render(
#         request,
#         "accounts/profile_wizard.html",
#         {
#             "profile": profile,
#             "completion": profile.completion_percentage()
#         }
#     )
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, render

from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


@login_required
def profile_wizard(request):
    profile = request.user.profile

    if request.method == "POST":
        profile.full_name = request.POST.get("full_name")
        profile.mobile_number = request.POST.get("mobile_number", "").strip()

        experience = request.POST.get("experience")
        profile.experience = int(experience) if experience else None

        profile.location = request.POST.get("location")
        profile.skills = request.POST.get("skills")

        if request.FILES.get("resume"):
            profile.resume = request.FILES.get("resume")

        profile.save()

        # ✅ Check completion AFTER save
        completion = profile.completion_percentage()

        # ✅ Send email only ONCE
        if completion == 100 and not profile.completion_email_sent:
            send_mail(
                subject="🎉 Profile Completed Successfully!",
                message=(
                    f"Hi {profile.full_name or 'there'},\n\n"
                    "Your profile has been completed successfully.\n\n"
                    "You can now apply for jobs, save opportunities, "
                    "and track your applications from your dashboard.\n\n"
                    "Warm regards,\n"
                    "Vetri Consultancy Services"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[request.user.email],
                fail_silently=False,  # IMPORTANT
            )

            profile.completion_email_sent = True
            profile.save(update_fields=["completion_email_sent"])

        messages.success(request, "Profile updated successfully.")
        return redirect("dashboard")

    return render(
        request,
        "accounts/profile_wizard.html",
        {
            "profile": profile,
            "completion": profile.completion_percentage()
        }
    )


@login_required
def my_profile(request):
    profile = request.user.profile

    if request.method == "POST":
        profile.full_name = request.POST.get("full_name")
        profile.mobile_number = request.POST.get("mobile_number", "").strip()

        experience = request.POST.get("experience")
        profile.experience = int(experience) if experience else None

        profile.location = request.POST.get("location")
        profile.skills = request.POST.get("skills")

        if request.FILES.get("resume"):
            profile.resume = request.FILES.get("resume")

        profile.save()

        # Check completion AFTER save
        completion = profile.completion_percentage()

        # Send email only ONCE
        if completion == 100 and not profile.completion_email_sent:
            send_mail(
                subject="🎉 Profile Completed Successfully!",
                message=(
                    f"Hi {profile.full_name or 'there'},\n\n"
                    "Your profile has been completed successfully.\n\n"
                    "You can now apply for jobs, save opportunities, "
                    "and track your applications from your dashboard.\n\n"
                    "Warm regards,\n"
                    "Vetri Consultancy Services"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[request.user.email],
                fail_silently=False,
            )

            profile.completion_email_sent = True
            profile.save(update_fields=["completion_email_sent"])

        messages.success(request, "Profile updated successfully.")
        return redirect("my_profile")

    return render(
        request,
        "accounts/profile.html",
        {
            "profile": profile,
            "completion": profile.completion_percentage()
        }
    )


#setting
@login_required
def settings_view(request):
    if request.method == "POST":
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if new_password:
            if new_password != confirm_password:
                messages.error(request, "Passwords do not match.")
                return redirect("settings")

            request.user.set_password(new_password)
            request.user.save()
            messages.success(request, "Password updated successfully.")
            return redirect("login")

    return render(request, "accounts/settings.html")

#upgrade to pro
@login_required
def upgrade_to_pro(request):
    if request.method == "POST":
        user = request.user

        # Already pro? it skips
        if user.subscription_type == User.PRO:
            return redirect("dashboard")

        # Mark as PRO and payment follow
        user.subscription_type = User.PRO
        user.save(update_fields=["subscription_type"])

        return redirect("payment")

    return redirect("settings")

#canditate list 

@staff_required
def candidate_list(request):
    candidates = (
        User.objects
        .filter(is_staff=False)
        .select_related("profile")
        .order_by("-date_joined")
    )

    return render(
        request,
        "accounts/candidate.html",
        {"candidates": candidates}
    )

#canditate and  admin dashboard
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from jobs.models import SavedJob, JobApplication
from core.models import Enrollment   # adjust import if Enrollment is in another app


# @login_required
# def dashboard_view(request):

#     # Admin / Consultant 
#     if request.user.is_staff:
#         return redirect("admin_dashboard")

#     # Candidate profile completion check
#     if request.user.profile.completion_percentage() < 50:
#         return redirect("profile_wizard")

#     saved_jobs_count = SavedJob.objects.filter(user=request.user).count()
#     applications_count = JobApplication.objects.filter(user=request.user).count()

#     # ✅ NEW: Enrolled trainings count
#     enrolled_trainings_count = Enrollment.objects.filter(
#         user=request.user
#     ).count()

#     return render(
#         request,
#         "accounts/dashboard.html",
#         {
#             "saved_jobs_count": saved_jobs_count,
#             "applications_count": applications_count,
#             "enrolled_trainings_count": enrolled_trainings_count,
#         }
#     )



#admin dashboard
from jobs.models import Job, JobApplication
from core.models import Training, Enrollment, TrainingEnquiry
@staff_required
def admin_dashboard(request):
    total_candidates = User.objects.filter(is_staff=False).count()
    total_jobs = Job.objects.count()
    pending_jobs = Job.objects.filter(status="PENDING").count()
    active_jobs = Job.objects.filter(status="PUBLISHED").count()
    total_applications = JobApplication.objects.count()
    total_trainings = Training.objects.count()
    total_enrollments = Enrollment.objects.count()
    total_enquiries = TrainingEnquiry.objects.count()

    return render(
        request,
        "accounts/admin_dashboard.html",
        {
            "total_candidates": total_candidates,
            "total_jobs": total_jobs,
            "pending_jobs": pending_jobs,
            "active_jobs": active_jobs,
            "total_applications": total_applications,
            "total_trainings": total_trainings,
            "total_enrollments": total_enrollments,
            "total_enquiries": total_enquiries,
        }
    )
# #candidate resume view:
# @login_required
# def resume_view(request):
#     profile = request.user.profile
#     return render(request, "accounts/resume.html", {"profile": profile})

from jobs.models import JobApplication
from accounts.decorators import staff_required
from django.shortcuts import get_object_or_404

@staff_required
def candidate_detail(request, user_id):
    candidate = get_object_or_404(User, id=user_id, is_staff=False)

    applications = JobApplication.objects.filter(user=candidate)

    enrollments = Enrollment.objects.filter(user=candidate).select_related("training")

    return render(
        request,
        "accounts/candidate_detail.html",
        {
            "candidate": candidate,
            "applications": applications,
            "enrollments": enrollments,
        }
    )
    
    



from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def ai_chat_page(request):
    return render(request, "accounts/ai_chatbox.html")

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from accounts.ai_helper import get_ai_help
import json


@csrf_exempt
@require_POST
def ai_chatbot(request):
    if not request.user.is_authenticated:
        return JsonResponse({"reply": "Please login to use the assistant."})

    data = json.loads(request.body)
    message = data.get("message")
    page = data.get("page")

    reply = get_ai_help(request.user, message, page)

    return JsonResponse({"reply": reply})


#email update
#and
#status update by admin

from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from accounts.decorators import staff_required
from jobs.models import JobApplication

@staff_required
@require_POST
def update_application_status(request, app_id):
    application = get_object_or_404(JobApplication, id=app_id)
    old_status = application.status

    new_status = request.POST.get("status")

    if new_status not in dict(JobApplication.STATUS_CHOICES):
        messages.error(request, "Invalid status selected.")
        return redirect("candidate_detail", user_id=application.user.id)

    application.status = new_status
    application.save()

    # Send email ONLY when moved to INTERVIEW
    if old_status != "INTERVIEW" and new_status == "INTERVIEW":
        candidate = application.user
        job = application.job

        subject = "🎉 Shortlisted for Screening Interview"
        message = (
            f"Dear {candidate.profile.full_name or 'Candidate'},\n\n"
            f"We are pleased to inform you that you have been shortlisted "
            f"for a screening interview for the position of "
            f"{job.title} at {job.company_name}.\n\n"
            "You will receive the interview meeting link shortly.\n\n"
            "Please start preparing and give it your best.\n\n"
            "Wishing you all the very best!\n\n"
            "Regards,\n"
            "Vetri Consultancy Services"
        )

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[candidate.email],
                fail_silently=False,
            )
        except Exception as e:
            # Email failure should NOT block admin action
            messages.warning(
                request,
                "Status updated, but email could not be sent."
            )

    messages.success(request, "Application status updated.")
    return redirect("candidate_detail", user_id=application.user.id)




from django.contrib.auth.decorators import login_required
from core.models import Enrollment
from jobs.models import JobApplication, Job
from jobs.models import SavedJob, JobApplication
from core.models import Enrollment

@login_required
def dashboard(request):
    enrollments = Enrollment.objects.filter(
        user=request.user
    ).select_related("training")

    context = {
        "saved_jobs_count": SavedJob.objects.filter(
            user=request.user
        ).count(),

        "applications_count": JobApplication.objects.filter(
            user=request.user
        ).count(),

        "enrolled_trainings_count": enrollments.count(),
        "enrollments": enrollments,
    }

    return render(request, "accounts/dashboard.html", context)

