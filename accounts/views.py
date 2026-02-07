from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User, Profile
from accounts.decorators import admin_required
from .decorators import staff_required
from django.utils import timezone
from datetime import timedelta
from accounts.utils.email import safe_send_mail

# ---------------- LOGIN ----------------
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

        # ROLE BASED REDIRECT
        if user.is_staff:     # admin / consultant
            return redirect("admin_dashboard")
        else:                 # candidate
            return redirect("public_home")

    return render(request, "accounts/login.html")


# ---------------- REGISTER ----------------
def register_user(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm = request.POST.get("confirm_password")
        mobile = request.POST.get("mobile_number")

        # Validation
        if not all([full_name, email, password, confirm, mobile]):
            messages.error(request, "All fields are required.")
            return redirect("register")

        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect("register")

        # CREATE USER → ALWAYS FREE TRIAL
        user = User.objects.create_user(
            email=email,
            password=password,
            full_name=full_name,
            plan=User.FREE,
            plan_status=User.ACTIVE,   # Free is permanent active plan
            plan_start=timezone.now(),
            plan_end=None,             # No expiry for free users
            usage_reset_date=timezone.now(),
        )

        # Profile created by signal
        profile = user.profile
        profile.full_name = full_name
        profile.mobile_number = mobile
        profile.save()

        # IMPORTANT: specify backend (because Google auth also exists)
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)

        return redirect("my_profile")

    return render(request, "accounts/register.html")


# ---------------- LOGOUT ----------------
def logout_user(request):
    logout(request)
    messages.success(request, "You have logged out successfully.")
    return redirect("login")



@admin_required
def post_job(request):
    return render(request, "jobs/post_job.html")

@login_required
def payment(request):
    selected_plan = request.session.get("selected_plan")

    if not selected_plan:
        messages.error(request, "No plan selected.")
        return redirect("settings")

    # Plan pricing
    if selected_plan == User.PRO:
        amount = 8999
        plan_name = "Pro"

    elif selected_plan == User.PRO_PLUS:
        amount = 29999
        plan_name = "Pro Plus"

    else:
        messages.error(request, "Invalid plan.")
        return redirect("settings")

    # Simulated payment success
    if request.method == "POST":
        user = request.user

        user.plan = selected_plan
        user.plan_status = User.ACTIVE
        user.plan_start = timezone.now()
        # user.plan_end = timezone.now() + timedelta(days=30)
        # user.plan_end = timezone.now() + timedelta(hours=1)
        user.plan_end = timezone.now() + timedelta(minutes=2)



        user.save()

        # clear session
        del request.session["selected_plan"]

        messages.success(request, f"Payment successful! Welcome to {plan_name} ")
        return redirect("dashboard")

    return render(request, "accounts/payment.html", {
        "amount": amount,
        "plan_name": plan_name
    })






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
           
            sent = safe_send_mail(
                subject="🎉 Profile Completed Successfully!",
                message=(
                    f"Hi {profile.full_name or 'there'},\n\n"
                    "Your profile has been completed successfully.\n\n"
                    "You can now apply for jobs and track applications.\n\n"
                    "Vetri Consultancy Services"
                ),
                recipient_list=[request.user.email],
            )

            if sent:
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
    """
    Step 1 of upgrade:
    User chooses plan → store intent → go to payment
    DOES NOT activate subscription
    """
    request.session["selected_plan"] = User.PRO
    return redirect("payment")

@login_required
def upgrade_to_pro_plus(request):
    request.session["selected_plan"] = User.PRO_PLUS
    return redirect("payment")


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

    # allow only active paid users or admin
    if not (
        request.user.is_staff or
        (request.user.plan in [User.PRO, User.PRO_PLUS] and request.user.plan_status == User.ACTIVE)
    ):
        messages.warning(request, "AI Assistant is a PRO feature. Please upgrade your plan.")
        return redirect("settings")

    return render(request, "accounts/ai_chatbox.html")



from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from accounts.ai_helper import get_ai_help
import json


@csrf_exempt
@require_POST
def ai_chatbot(request):

           
        # block free users
    if not (
        request.user.plan in [User.PRO, User.PRO_PLUS]
        and request.user.plan_status == User.ACTIVE
    ):
        return JsonResponse({
            "reply": "This feature is available only for PRO users. Upgrade your plan."
        })


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

    # send mail ONLY when moved to INTERVIEW
    if old_status != "INTERVIEW" and new_status == "INTERVIEW":
        candidate = application.user
        job = application.job

        subject = "🎉 Shortlisted for Screening Interview"
        message = (
            f"Dear {candidate.profile.full_name or 'Candidate'},\n\n"
            f"You have been shortlisted for a screening interview for "
            f"{job.title} at {job.company_name}.\n\n"
            "Prepare well. Meeting link will be shared soon.\n\n"
            "Regards,\n"
            "Vetri Consultancy Services"
        )

        sent = safe_send_mail(
            subject=subject,
            message=message,
            recipient_list=[candidate.email],
        )

        if sent:
            messages.success(request, "Application status updated & email sent.")
        else:
            messages.warning(request, "Status updated but email failed.")

    else:
        messages.success(request, "Application status updated.")

    return redirect("candidate_detail", user_id=application.user.id)






from django.contrib.auth.decorators import login_required
from core.models import Enrollment
from jobs.models import JobApplication, Job
from jobs.models import SavedJob, JobApplication
from core.models import Enrollment

@login_required
def dashboard(request):

    # block admin entering candidate dashboard
    if request.user.is_staff:
        return redirect("admin_dashboard")

    enrollments = Enrollment.objects.filter(
        user=request.user
    ).select_related("training")

    context = {
        "saved_jobs_count": SavedJob.objects.filter(user=request.user).count(),
        "applications_count": JobApplication.objects.filter(user=request.user).count(),
        "enrolled_trainings_count": enrollments.count(),
        "enrollments": enrollments,
    }

    return render(request, "accounts/dashboard.html", context)


