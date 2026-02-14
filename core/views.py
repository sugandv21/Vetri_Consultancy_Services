from django.shortcuts import render
from django.db.models import Q
from .models import (
    HomeHero,
    HomeFeature,
    FeatureSection,
    SiteStatistic,
    HomeCTA,
    FAQ,
    Testimonial,
)

from jobs.utils import visible_jobs_for_user
from jobs.models import JobApplication


from .utils.certificate_generator import generate_certificate


def public_home(request):
    # BLOCK ADMIN FROM PUBLIC PAGE
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("admin_dashboard")

    # ---------------- HERO ----------------
    hero = HomeHero.objects.filter(is_active=True).first()

    # ---------------- SERVICES SECTION ----------------
    feature_section = FeatureSection.objects.filter(is_active=True).first()

    if feature_section:
        features = feature_section.features.filter(is_active=True).order_by("order")
    else:
        features = []

    stats = SiteStatistic.objects.filter(is_active=True)
    cta = HomeCTA.objects.filter(is_active=True).first()
    faqs = FAQ.objects.filter(is_active=True).order_by("order")
    
    testimonials = Testimonial.objects.filter(is_active=True).order_by("-created_at")[:6]

    context = {
        "hero": hero,
        "feature_section": feature_section,
        "features": features,
        "stats": stats,
        "cta": cta,
        "faqs": faqs,
        "testimonials": testimonials
    }


    # ======================================================
    # DASHBOARD PREVIEW (ONLY FOR LOGGED IN USERS)
    # ======================================================
    if request.user.is_authenticated and not request.user.is_staff:

        profile = getattr(request.user, "profile", None)

        recommended_jobs = []
        applied_ids = []

        if profile:
            jobs_qs = visible_jobs_for_user(request.user)

            # ---------- Skill Matching ----------
            if profile.skills:
                skills = [s.strip() for s in profile.skills.split(",") if s.strip()]

                skill_query = Q()
                for skill in skills:
                    skill_query |= Q(skills__icontains=skill) | Q(title__icontains=skill)

                jobs_qs = jobs_qs.filter(skill_query)

            recommended_jobs = jobs_qs.order_by("-created_at")[:6]

            # ---------- Already Applied Jobs ----------
            applied_ids = list(
                JobApplication.objects.filter(user=request.user)
                .values_list("job_id", flat=True)
            )

        context.update({
            "profile": profile,
            "recommended_jobs": recommended_jobs,
            "applied_ids": applied_ids,
        })

    return render(request, "core/home.html", context)

from accounts.decorators import staff_required
from django.contrib.auth import get_user_model
from jobs.models import Job, JobApplication

User = get_user_model()

@staff_required
def admin_home(request):
    context = {
        "total_candidates": User.objects.filter(is_staff=False).count(),
        "total_jobs": Job.objects.count(),
        "pending_jobs": Job.objects.filter(status="PENDING").count(),
        "active_jobs": Job.objects.filter(status="PUBLISHED").count(),
        "total_applications": JobApplication.objects.count(),
    }
    return render(request, "core/admin_home.html", context)

from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Training, Enrollment, TrainingEnquiry


@login_required
def training_list(request):
    trainings = Training.objects.filter(is_active=True)

    enrolled_ids = set(
        Enrollment.objects.filter(user=request.user)
        .values_list("training_id", flat=True)
    )

    free_eligible = request.user.can_get_free_training()

    return render(request, "core/training_list.html", {
        "trainings": trainings,
        "enrolled_ids": enrolled_ids,
        "free_eligible": free_eligible
    })


from core.models import Payment

@login_required
def enroll_training(request, training_id):

    if request.method != "POST":
        return redirect("training_detail", training_id=training_id)

    training = get_object_or_404(Training, id=training_id, is_active=True)
    user = request.user

    # Already enrolled
    if Enrollment.objects.filter(user=user, training=training).exists():
        messages.info(request, "You are already enrolled in this training.")
        return redirect("training_detail", training_id=training.id)

    # ---------------- FREE BENEFIT ----------------
    if user.can_get_free_training():

        Enrollment.objects.create(user=user, training=training)

        Payment.objects.create(
            user=user,
            payment_type="TRAINING",
            amount=0,
            status="SUCCESS",
            training=training
        )

        messages.success(request, "🎉 Free enrollment applied (PRO PLUS benefit).")
        return redirect("training_detail", training_id=training.id)

    # ---------------- PAID TRAINING ----------------
    messages.info(request, "Please complete payment to enroll.")
    return redirect("training_pay", training_id=training.id)


@login_required
def training_enquiry(request, training_id):
    training = get_object_or_404(Training, id=training_id)

    if request.method == "POST":
        TrainingEnquiry.objects.create(
            user=request.user,
            training=training,
            message=request.POST.get("message")
        )
        messages.success(request, "Enquiry sent.")
        return redirect("training_list")

    return render(request, "core/enquiry_form.html", {"training": training})


from core.models import Training, TrainingEnquiry, EnquiryMessage
from django.contrib.auth.decorators import login_required


@login_required
def training_enquiry_chat(request, training_id):
    training = get_object_or_404(Training, id=training_id)

    enquiry, _ = TrainingEnquiry.objects.get_or_create(
        user=request.user,
        training=training
    )

    if request.method == "POST":
        EnquiryMessage.objects.create(
            enquiry=enquiry,
            sender=request.user,
            message=request.POST.get("message")
        )
        return redirect("training_enquiry_chat", training_id=training.id)

    messages_qs = enquiry.messages.select_related("sender").order_by("created_at")

    return render(request, "core/enquiry_form.html", {
        "training": training,
        "enquiry": enquiry,
        "messages": messages_qs
    })
    
#training_detail
from core.models import Enrollment

def training_detail(request, training_id):
    training = get_object_or_404(Training, id=training_id)

    free_eligible = False
    already_enrolled = False

    if request.user.is_authenticated:
        already_enrolled = Enrollment.objects.filter(
            user=request.user,
            training=training
        ).exists()

        if not already_enrolled:
            free_eligible = request.user.can_get_free_training()

    return render(request, "core/training_detail.html", {
        "training": training,
        "free_eligible": free_eligible,
        "already_enrolled": already_enrolled,
    })




#Public view pages
from .models import ServicePage

def services_view(request):
    page = ServicePage.objects.filter(is_active=True).prefetch_related("services").first()

    return render(request, "core/services.html", {
        "page": page
    })


from .models import PricingPage

def pricing_view(request):
    page = PricingPage.objects.filter(is_active=True)\
        .prefetch_related("plans__features")\
        .first()

    return render(request, "core/pricing.html", {
        "page": page
    })


from .models import AboutPage

def about_view(request):
    about = AboutPage.objects.filter(is_active=True).first()
    return render(request, "core/about.html", {"about": about})




from .models import ContactMessage

def contact_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message_text = request.POST.get("message")

        ContactMessage.objects.create(
            name=name,
            email=email,
            message=message_text
        )

        messages.success(request, "Your message has been sent successfully!")

        return redirect("contact")

    return render(request, "core/contact.html")



import razorpay
import json
from django.conf import settings
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

from .models import Training, Enrollment
from core.models import Payment
@login_required
def training_pay(request, training_id):

    training = get_object_or_404(Training, id=training_id, is_active=True)

    # already enrolled safety
    if Enrollment.objects.filter(user=request.user, training=training).exists():
        messages.info(request, "You are already enrolled.")
        return redirect("training_detail", training_id=training.id)

    # free benefit should not go to payment
    if request.user.can_get_free_training():
        return redirect("training_detail", training_id=training.id)

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    order = client.order.create({
        "amount": int(training.fee * 100),  # paise
        "currency": "INR",
        "payment_capture": 1
    })

    # store BOTH
    request.session["training_payment_training"] = training.id
    request.session["training_payment_order"] = order["id"]

    return render(request, "core/training_payment.html", {
        "training": training,
        "order_id": order["id"],
        "amount_paise": int(training.fee * 100),
        "razorpay_key": settings.RAZORPAY_KEY_ID,
    })


@csrf_exempt
@login_required
def verify_training_payment(request):

    if request.method != "POST":
        return JsonResponse({"redirect_url": reverse("training_list")})

    data = json.loads(request.body)

    payment_id = data.get("razorpay_payment_id")
    order_id = data.get("razorpay_order_id")
    signature = data.get("razorpay_signature")

    stored_order = request.session.get("training_payment_order")
    training_id = request.session.get("training_payment_training")

    if not stored_order or not training_id:
        return JsonResponse({"redirect_url": reverse("training_list")})

    # SECURITY: order mismatch protection
    if order_id != stored_order:
        return JsonResponse({"redirect_url": reverse("training_list")})

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    try:
        client.utility.verify_payment_signature({
            "razorpay_payment_id": payment_id,
            "razorpay_order_id": order_id,
            "razorpay_signature": signature
        })

        training = Training.objects.get(id=training_id)
        user = request.user

        # prevent duplicate enrollment
        enrollment, created = Enrollment.objects.get_or_create(
            user=user,
            training=training,
            defaults={"enrolled_at": timezone.now()}
        )

        # record payment only once
        if created:
            Payment.objects.create(
                user=user,
                payment_type="TRAINING",
                amount=training.fee,
                status="SUCCESS",
                training=training
            )

        # cleanup session
        request.session.pop("training_payment_training", None)
        request.session.pop("training_payment_order", None)

        return JsonResponse({
            "redirect_url": reverse("training_detail", args=[training.id])
        })

    except Exception as e:
        print("PAYMENT VERIFY FAILED:", str(e))
        return JsonResponse({
            "redirect_url": reverse("training_detail", args=[training_id])
        })


from core.models import Enrollment, ModuleProgress

def candidate_training_modules(request, training_id):

    enrollment = Enrollment.objects.filter(
        user=request.user,
        training_id=training_id
    ).first()

    if not enrollment:
        return redirect("candidate_dashboard")

    progress_list = ModuleProgress.objects.filter(
        enrollment=enrollment
    ).select_related("module").order_by("module__order")

    context = {
        "enrollment": enrollment,
        "progress_list": progress_list,
        "training": enrollment.training
    }

    return render(request, "candidate/training_modules.html", context)



from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from core.models import ModuleProgress, TrainingCompletion
from core.utils.certificate_generator import generate_certificate


from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.conf import settings
from django.core.files import File
import os



@login_required
def complete_module(request, progress_id):

    # ---------------- GET PROGRESS ----------------
    try:
        progress = ModuleProgress.objects.select_related("enrollment").get(
            id=progress_id,
            enrollment__user=request.user
        )
    except ModuleProgress.DoesNotExist:
        return JsonResponse({"success": False}, status=404)

    # already completed (avoid double click issues)
    if progress.is_completed:
        return JsonResponse({"success": True})

    # ---------------- MARK MODULE COMPLETE ----------------
    progress.is_completed = True
    progress.completed_at = timezone.now()
    progress.save()

    enrollment = progress.enrollment

    # ---------------- CALCULATE PROGRESS ----------------
    total = enrollment.module_progress.count()
    completed = enrollment.module_progress.filter(is_completed=True).count()
    percent = int((completed / total) * 100) if total else 0

    # ---------------- COURSE COMPLETION ----------------
    if percent == 100 and not enrollment.is_completed:

        enrollment.is_completed = True

        # generate certificate PDF
        file_path = generate_certificate(enrollment)   # returns: certificates/filename.pdf

        if file_path:
            full_path = os.path.join(settings.MEDIA_ROOT, file_path)

            # attach file properly to Django FileField
            if os.path.exists(full_path):
                with open(full_path, "rb") as f:
                    enrollment.certificate.save(
                        os.path.basename(full_path),
                        File(f),
                        save=False
                    )

        enrollment.save()

        # update completion tracker
        TrainingCompletion.objects.filter(
            enrollment=enrollment
        ).update(status=TrainingCompletion.COMPLETED_BY_TRAINER)

    # ---------------- RESPONSE ----------------
    return JsonResponse({
        "success": True,
        "percent": percent,
        "completed": percent == 100
    })
