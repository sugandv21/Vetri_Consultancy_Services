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



#from django.core.mail import send_mail
from accounts.utils.email import safe_send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, render

@login_required
def profile_wizard(request):
    profile, created = Profile.objects.get_or_create(user=request.user)


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

        completion = profile.completion_percentage()

        if completion == 100 and not profile.completion_email_sent:
            safe_send_mail(
                subject="🎉 Profile Completed Successfully!",
                message=(
                    f"Hi {profile.full_name or 'there'},\n\n"
                    "Your profile has been completed successfully.\n\n"
                    "You can now apply for jobs and track applications.\n\n"
                    "Vetri Consultancy Services"
                ),
                recipient_list=[request.user.email],
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
    profile, created = Profile.objects.get_or_create(user=request.user)


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

        completion = profile.completion_percentage()

        if completion == 100 and not profile.completion_email_sent:
            safe_send_mail(
                subject="🎉 Profile Completed Successfully!",
                message=(
                    f"Hi {profile.full_name or 'there'},\n\n"
                    "Your profile has been completed successfully.\n\n"
                    "You can now apply for jobs and track applications.\n\n"
                    "Vetri Consultancy Services"
                ),
                recipient_list=[request.user.email],
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

from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
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

        profile, _ = Profile.objects.get_or_create(user=candidate)

        subject = "🎉 Shortlisted for Screening Interview"
        message = (
            f"Dear {profile.full_name or 'Candidate'},\n\n"
            f"We are pleased to inform you that you have been shortlisted "
            f"for a screening interview for the position of "
            f"{job.title} at {job.company_name}.\n\n"
            "You will receive the interview meeting link shortly.\n\n"
            "Please start preparing and give it your best.\n\n"
            "Wishing you all the very best!\n\n"
            "Regards,\n"
            "Vetri Consultancy Services"
        )

        sent = safe_send_mail(
            subject=subject,
            message=message,
            recipient_list=[candidate.email],
        )

        if not sent:
            messages.warning(request, "Status updated but email failed.")

    messages.success(request, "Application status updated.")
    return redirect("candidate_detail", user_id=application.user.id)
