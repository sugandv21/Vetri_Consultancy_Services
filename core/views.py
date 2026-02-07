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
    enrolled_ids = Enrollment.objects.filter(
        user=request.user
    ).values_list("training_id", flat=True)

    return render(request, "core/training_list.html", {
        "trainings": trainings,
        "enrolled_ids": enrolled_ids
    })

@login_required
def enroll_training(request, training_id):
    if request.method != "POST":
        return redirect("training_detail", training_id=training_id)

    training = get_object_or_404(
        Training,
        id=training_id,
        is_active=True
    )

    enrollment, created = Enrollment.objects.get_or_create(
        user=request.user,
        training=training
    )

    if created:
        messages.success(
            request,
            "Payment successful! You are now enrolled 🎉"
        )
    else:
        messages.info(
            request,
            "You are already enrolled in this training."
        )

    return redirect("training_detail", training_id=training.id)


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
def training_detail(request, training_id):
    training = get_object_or_404(Training, id=training_id)
    return render(request, "core/training_detail.html", {
        "training": training
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
