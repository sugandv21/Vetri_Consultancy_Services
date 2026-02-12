from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User, Profile
from accounts.decorators import admin_required
from .decorators import staff_required
from django.utils import timezone
from datetime import timedelta
from jobs.models import JobApplication
from django.shortcuts import get_object_or_404
from accounts.models import Notification
from accounts.models import Payment
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

from .models import SubscriptionPricing
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import SubscriptionPricing, Payment, User

import razorpay
import json
@csrf_exempt
@login_required
def payment(request):

    # ---------------- PLAN FROM SESSION ----------------
    selected_plan = request.session.get("selected_plan")

    if not selected_plan:
        messages.error(request, "No plan selected.")
        return redirect("settings")

    if selected_plan not in [User.PRO, User.PRO_PLUS]:
        messages.error(request, "Invalid plan selected.")
        return redirect("settings")

    pricing = SubscriptionPricing.objects.filter(plan=selected_plan).first()

    if not pricing:
        messages.error(request, "Pricing not configured. Contact admin.")
        return redirect("settings")

    amount = pricing.price
    plan_name = dict(User.PLAN_CHOICES).get(selected_plan, selected_plan)

    # ============================================================
    # 🔵 HANDLE RAZORPAY PAYMENT VERIFY (POST)
    # ============================================================
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            razorpay_payment_id = data.get("razorpay_payment_id")
            razorpay_order_id = data.get("razorpay_order_id")
            razorpay_signature = data.get("razorpay_signature")

            if not razorpay_payment_id or not razorpay_order_id or not razorpay_signature:
                print("MISSING RAZORPAY DATA")
                return JsonResponse({"redirect_url": reverse("settings")})

            client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )

            # ---------------- SESSION ORDER CHECK ----------------
            stored_order_id = request.session.get("razorpay_order_id")

            if not stored_order_id:
                print("SESSION ORDER ID MISSING")
                return JsonResponse({"redirect_url": reverse("settings")})

            # SECURITY: prevent fake callback
            if razorpay_order_id != stored_order_id:
                print("ORDER ID MISMATCH")
                return JsonResponse({"redirect_url": reverse("settings")})

            # ---------------- SIGNATURE VERIFY ----------------
            client.utility.verify_payment_signature({
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_order_id": razorpay_order_id,
                "razorpay_signature": razorpay_signature
            })

            # ===================================================
            # 🟢 IDEMPOTENT PAYMENT CREATION (CRITICAL FIX)
            # prevents duplicate callbacks in production
            # ===================================================
            payment_obj, created = Payment.objects.get_or_create(
                razorpay_payment_id=razorpay_payment_id,
                defaults={
                    "user": request.user,
                    "payment_type": "PLAN",
                    "amount": amount,
                    "status": "SUCCESS",
                }
            )

            # Activate plan ONLY first time
            if created:
                user = request.user
                user.plan = selected_plan
                user.plan_status = User.ACTIVE
                user.plan_start = timezone.now()
                user.plan_end = timezone.now() + timedelta(days=30)
                user.save()

            # cleanup session
            request.session.pop("selected_plan", None)
            request.session.pop("razorpay_order_id", None)

            return JsonResponse({"redirect_url": reverse("dashboard")})

        except Exception as e:
            print("RAZORPAY VERIFY ERROR:", str(e))
            return JsonResponse({"redirect_url": reverse("settings")})

    # ============================================================
    # 🟡 CREATE ORDER (GET)
    # ============================================================
    try:
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        order = client.order.create({
            "amount": int(amount * 100),  # paise
            "currency": "INR",
            "receipt": f"user_{request.user.id}_{selected_plan}",
            "payment_capture": 1
        })

        # store order in session
        request.session["razorpay_order_id"] = order["id"]

    except Exception as e:
        print("RAZORPAY ORDER ERROR:", str(e))
        messages.error(request, "Payment gateway error. Please try again later.")
        return redirect("settings")

    return render(request, "accounts/payment.html", {
        "amount": amount,
        "plan_name": plan_name,
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "order_id": order["id"],
    })




from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.db.models import Count
from django.db.models.functions import TruncWeek


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
        return redirect("dashboard")

    return render(
        request,
        "accounts/profile_wizard.html",
        {
            "profile": profile,
            "completion": profile.completion_percentage()
        }
    )

from django.db.models import Count
from django.db.models.functions import ExtractWeek
from jobs.models import JobApplication

@login_required
def my_profile(request):
    profile = request.user.profile

    # -------------------- HANDLE FORM SUBMIT --------------------
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

       # completion email
        completion = profile.completion_percentage()
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

    # -------------------- ANALYTICS (ONLY FOR PAGE LOAD) --------------------
    responses = (
        JobApplication.objects
        .filter(
            user=request.user,
            status__in=["IN_REVIEW", "INTERVIEW", "CLOSED"]
        )
        .annotate(week=ExtractWeek("applied_at"))
        .values("week")
        .annotate(total=Count("id"))
        .order_by("week")
    )

    chart_labels = []
    chart_data = []

    for row in responses:
        chart_labels.append(f"Week {row['week']}")
        chart_data.append(row["total"])

    # -----------------------------------------------------------------------

    return render(
        request,
        "accounts/profile.html",
        {
            "profile": profile,
            "completion": profile.completion_percentage(),
            "plan": request.user.plan,
            "chart_labels": chart_labels,
            "chart_data": chart_data,
        }
    )


from django.urls import reverse
from django.contrib.auth import update_session_auth_hash

@login_required
def settings_view(request):

    reason = request.GET.get("upgrade_required")

    messages_map = {
        "mock": "Mock interviews are available only for Pro Plus members.",
        "consultant": "Consultant sessions require a paid plan.",
        "resume": "AI resume optimization is available in Pro and Pro Plus plans.",
    }

    message = messages_map.get(reason)

    if request.method == "POST":
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if new_password:
            if new_password != confirm_password:
                messages.error(request, "Passwords do not match.")
                return redirect(f"{reverse('settings')}?upgrade_required={reason or ''}")

            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)

            messages.success(request, "Password updated successfully.")
            return redirect("settings")

    payments = Payment.objects.filter(user=request.user).order_by("-created_at")

    return render(request, "accounts/settings.html", {
        "upgrade_message": message,
        "payments": payments
    })

from django.http import HttpResponse
from .models import Payment
from .services.invoice import build_invoice
from django.contrib.auth.decorators import login_required


@login_required
def download_invoice(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)

    buffer = build_invoice(payment, request.user)

    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="invoice_{payment.id}.pdf"'

    return response

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

    # ---------------- SUBSCRIPTION FILTER ----------------
    plan = request.GET.get("plan")
    if plan in ["FREE", "PRO", "PRO_PLUS"]:
        candidates = candidates.filter(plan=plan)

    # ---------------- HIRING STAGE FILTER ----------------
    stage = request.GET.get("stage")

    if stage == "PENDING":
        candidates = candidates.filter(
            job_applications__status="APPLIED"
        ).distinct()

    elif stage == "INTERVIEW":
        candidates = candidates.filter(
            job_applications__status="INTERVIEW"
        ).distinct()

    return render(request, "accounts/candidate.html", {"candidates": candidates})

#canditate and  admin dashboard
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from jobs.models import SavedJob, JobApplication
from core.models import Enrollment   # adjust import if Enrollment is in another app




#admin dashboard
from jobs.models import Job, JobApplication
from core.models import Training, Enrollment, TrainingEnquiry
from accounts.models import Notification


@staff_required
def admin_dashboard(request):

    # ---------------- USERS ----------------
    candidate_users = User.objects.filter(is_staff=False)

    total_candidates = candidate_users.count()

    free_users = candidate_users.filter(plan=User.FREE).count()

    paid_users = candidate_users.exclude(plan=User.FREE).count()

    expired_users = candidate_users.filter(plan_status=User.EXPIRED).count()

    # ---------------- JOBS ----------------
    total_jobs = Job.objects.count()
    pending_jobs = Job.objects.filter(status="PENDING").count()
    active_jobs = Job.objects.filter(status="PUBLISHED").count()

    # ---------------- APPLICATIONS ----------------
    total_applications = JobApplication.objects.count()
    pending_applications = JobApplication.objects.filter(status="APPLIED").count()
    interview_applications = JobApplication.objects.filter(status="INTERVIEW").count()

    # ---------------- TRAINING ----------------
    total_trainings = Training.objects.count()
    total_enrollments = Enrollment.objects.count()
    total_enquiries = TrainingEnquiry.objects.count()

    # ---------------- SLA MONITORING ----------------
    from django.utils import timezone
    from datetime import timedelta

    one_day_ago = timezone.now() - timedelta(hours=24)

    last_message = EnquiryMessage.objects.filter(
        enquiry=OuterRef("pk")
    ).order_by("-created_at")

    delayed_queryset = TrainingEnquiry.objects.annotate(
        last_sender=Subquery(last_message.values("sender")[:1]),
        last_message_time=Subquery(last_message.values("created_at")[:1])
    ).filter(
        last_sender__isnull=False,
        last_message_time__lte=one_day_ago
    ).exclude(
        last_sender=request.user.id
    )

    delayed_enquiries = delayed_queryset.count()


    # ---------------- ALERTS ----------------
    job_notifications = Notification.objects.filter(
        user__isnull=True,
        is_read=False,
        created_at__gte=one_day_ago
    ).order_by("-created_at")

    new_app_count = job_notifications.count()
    recent_notifications = job_notifications[:5]

    notifications = request.user.notifications.filter(
        is_read=False,
        created_at__gte=one_day_ago
    ).order_by("-created_at")
    # ---------------- UNREAD ADMIN ALERTS ----------------
    unread_notifications = Notification.objects.filter(
        user__isnull=True,   # admin/global alerts only
        is_read=False
    ).count()

    return render(request, "accounts/admin_dashboard.html", {

        # users
        "total_candidates": total_candidates,
        "free_users": free_users,
        "paid_users": paid_users,
        "expired_users": expired_users,

        # jobs
        "total_jobs": total_jobs,
        "pending_jobs": pending_jobs,
        "active_jobs": active_jobs,

        # applications
        "total_applications": total_applications,
        "pending_applications": pending_applications,
        "interview_applications": interview_applications,

        # training
        "total_trainings": total_trainings,
        "total_enrollments": total_enrollments,
        "total_enquiries": total_enquiries,

        # SLA
        "delayed_enquiries": delayed_enquiries,
        "unread_notifications": unread_notifications,

        # alerts
        "new_app_count": new_app_count,
        "recent_notifications": recent_notifications,
        "notifications": notifications,
    })


# #candidate resume view:
# @login_required
# def resume_view(request):
#     profile = request.user.profile
#     return render(request, "accounts/resume.html", {"profile": profile})



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
from accounts.models import Notification


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
    
    
    Notification.objects.create(
        user=application.user,
        title="Application Status Updated",
        message=f"Your application for {application.job.title} is now {new_status}."
    )


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
from collections import OrderedDict


@login_required
def dashboard(request):

    # block admin entering candidate dashboard
    if request.user.is_staff:
        return redirect("admin_dashboard")

    user = request.user
    profile = user.profile

    # ---------------- DATA ----------------
    enrollments = Enrollment.objects.filter(user=user).select_related("training")
    one_day_ago = timezone.now() - timedelta(hours=24)

    notifications = user.notifications.filter(
        is_read=False,
        created_at__gte=one_day_ago
    ).order_by("-created_at")[:5]


    applications = JobApplication.objects.filter(user=user)
    interviews = applications.filter(status="INTERVIEW")
    
    # ---------------- RESPONSE ANALYTICS (LAST 4 WEEKS RANGE) ----------------
    

    today = timezone.now().date()

    # Build last 4 weeks (Mon → Sun)
    week_ranges = []
    week_map = OrderedDict()

    for i in range(3, -1, -1):
        start = today - timedelta(days=today.weekday(), weeks=i)
        end = start + timedelta(days=6)
        label = f"{start.strftime('%d %b')} - {end.strftime('%d %b')}"
        week_ranges.append((start, end, label))
        week_map[label] = 0

    # Fetch responded applications
    responses = JobApplication.objects.filter(
        user=user,
        status__in=["IN_REVIEW", "INTERVIEW", "CLOSED"]
    )

    # Count responses per week range
    for app in responses:
        applied_date = app.applied_at.date()
        for start, end, label in week_ranges:
            if start <= applied_date <= end:
                week_map[label] += 1

    chart_labels = list(week_map.keys())
    chart_data = list(week_map.values())
    # -------------------------------------------------------------------------



    # consultant sessions used this month
    sessions_used = user.sessions.filter(status="COMPLETED").count()

    # resume optimization usage
    resume_used = profile.resume_reviews.count()

    # ---------------- PLAN LIMITS ----------------
    if user.plan == "FREE":
        job_limit = 20
        resume_limit = 0
        session_limit = 0

    elif user.plan == "PRO":
        job_limit = 100
        resume_limit = 1
        session_limit = 1

    else:  # PRO_PLUS
        job_limit = None   # unlimited
        resume_limit = None
        session_limit = 4

    # ---------------- CONTEXT ----------------
    context = {
        "plan": user.plan,

        "saved_jobs_count": SavedJob.objects.filter(user=user).count(),

        "applications_count": applications.count(),
        "job_limit": job_limit,

        "interviews_count": interviews.count(),

        "resume_used": resume_used,
        "resume_limit": resume_limit,

        "sessions_used": sessions_used,
        "session_limit": session_limit,

        "completion": profile.completion_percentage(),

        "enrolled_trainings_count": enrollments.count(),
        "enrollments": enrollments,

        "notifications": notifications,
        "chart_labels": chart_labels,
        "chart_data": chart_data,

    }

    return render(request, "accounts/updated_dashboard.html", context)



#resume_review
from .resume_ai import generate_resume_suggestions
from .models import ResumeReview
#pro user -not pdf
@login_required
def generate_resume_review(request):

    user = request.user

    if user.plan not in [User.PRO, User.PRO_PLUS]:
        messages.warning(request, "Upgrade to PRO to use resume suggestions.")
        return redirect("settings")

    profile = user.profile

    feedback = generate_resume_suggestions(profile, None, mode="pro")


    ResumeReview.objects.update_or_create(
        profile=profile,
        review_type="BASIC",
        defaults={"feedback": feedback}
    )

    return redirect("my_profile")


#pro plus user
from .resume_parser import extract_text

from .resume_ai import generate_resume_suggestions


@login_required
def generate_advanced_resume_review(request):

    user = request.user

    if user.plan != User.PRO_PLUS:
        messages.warning(request, "Only Pro Plus users allowed.")
        return redirect("settings")

    profile = user.profile

    if not profile.resume:
        messages.error(request, "Upload resume first.")
        return redirect("my_profile")

    # Extract PDF text
    resume_text = extract_text(profile.resume.path)

    # Optional job description from form later
    job_description = request.POST.get("job_description")

    # Generate ATS analysis
    feedback = generate_resume_suggestions(profile, resume_text, mode="pro_plus")



    ResumeReview.objects.update_or_create(
        profile=profile,
        review_type="ADVANCED",
        defaults={"feedback": feedback}
    )

    messages.success(request, "ATS Resume analysis generated.")
    return redirect("my_profile")



from core.models import TrainingEnquiry
from accounts.models import Notification
from django.utils import timezone
from datetime import timedelta
# Shows enquiries waiting > 24 hours
from django.db.models import OuterRef, Subquery
from django.utils import timezone
from datetime import timedelta
from core.models import TrainingEnquiry, EnquiryMessage
from accounts.decorators import staff_required


@staff_required
def admin_delayed_enquiries(request):

    one_day_ago = timezone.now() - timedelta(hours=24)

    last_message = EnquiryMessage.objects.filter(
        enquiry=OuterRef("pk")
    ).order_by("-created_at")

    enquiries = TrainingEnquiry.objects.annotate(
        last_sender=Subquery(last_message.values("sender")[:1]),
        last_message_time=Subquery(last_message.values("created_at")[:1])
    ).filter(
        last_sender__isnull=False,
        last_message_time__lte=one_day_ago
    ).exclude(
        last_sender=request.user.id
    ).select_related("user", "training")

    return render(
        request,
        "accounts/admin_enquiry_list.html",
        {
            "title": "Delayed Enquiries",
            "enquiries": enquiries
        }
    )


# Shows admin inbox
@staff_required
def admin_unread_alerts(request):

    alerts = Notification.objects.filter(
        user__isnull=True,   # admin/global alerts only
        is_read=False
    ).order_by("-created_at")

    return render(
        request,
        "accounts/admin_alerts.html",
        {
            "title": "Unread Alerts",
            "alerts": alerts
        }
    )


from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect
from accounts.models import Notification
from accounts.decorators import staff_required

@staff_required
@require_POST
def mark_alert_read(request, alert_id):
    alert = get_object_or_404(Notification, id=alert_id)
    alert.is_read = True
    alert.save()
    return redirect("admin_unread_alerts")







