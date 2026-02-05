from django.shortcuts import render

def public_home(request):
    return render(request, 'core/home.html')

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
def services_view(request):
    return render(request, "core/services.html")

def pricing_view(request):
    return render(request, "core/pricing.html")

def about_view(request):
    return render(request, "core/about.html")



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
