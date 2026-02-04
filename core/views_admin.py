from django.shortcuts import render
from accounts.decorators import staff_required
from core.models import Enrollment, TrainingEnquiry
from django.shortcuts import get_object_or_404



@staff_required
def admin_enrollments(request):
    enrollments = Enrollment.objects.select_related("user", "training")
    return render(request, "core/admin_enrollments.html", {
        "enrollments": enrollments
    })


from django.db.models import OuterRef, Subquery

@staff_required
def admin_enquiries(request):
    latest_message = EnquiryMessage.objects.filter(
        enquiry=OuterRef("pk")
    ).order_by("-created_at")

    enquiries = TrainingEnquiry.objects.annotate(
        last_message=Subquery(latest_message.values("message")[:1]),
        last_message_time=Subquery(latest_message.values("created_at")[:1]),
    ).select_related("user", "training")

    return render(request, "core/admin_enquiries.html", {
        "enquiries": enquiries
    })
    
from django.shortcuts import redirect
from core.models import Training
from django.contrib import messages

@staff_required
def add_training(request):
    if request.method == "POST":
        Training.objects.create(
            title=request.POST["title"],
            description=request.POST["description"],
            duration=request.POST["duration"],
            fee=request.POST["fee"],
            image=request.FILES.get("image"),  
            is_active=True
        )
        messages.success(request, "Training added successfully.")
        return redirect("admin_enrollments")

    return render(request, "core/add_training.html")

@staff_required
def admin_training_list(request):
    trainings = Training.objects.all().order_by("-created_at")
    return render(request, "core/admin_training_list.html", {
        "trainings": trainings
    })
    
    
#edit/update
@staff_required
def edit_training(request, training_id):
    training = get_object_or_404(Training, id=training_id)

    if request.method == "POST":
        training.title = request.POST["title"]
        training.description = request.POST["description"]
        training.duration = request.POST["duration"]
        training.fee = request.POST["fee"]
        training.is_active = "is_active" in request.POST

        if request.FILES.get("image"):
            training.image = request.FILES["image"]

        training.save()
        messages.success(request, "Training updated successfully.")
        return redirect("admin_training_list")

    return render(request, "core/edit_training.html", {
        "training": training
    })


#delete
@staff_required
def delete_training(request, training_id):
    training = get_object_or_404(Training, id=training_id)

    if request.method == "POST":
        training.delete()
        messages.success(request, "Training deleted successfully.")
        return redirect("admin_training_list")

    return render(request, "core/delete_training.html", {
        "training": training
    })

from accounts.decorators import staff_required
from core.models import TrainingEnquiry, EnquiryMessage


@staff_required
def admin_enquiry_chat(request, enquiry_id):
    enquiry = get_object_or_404(TrainingEnquiry, id=enquiry_id)

    if request.method == "POST":
        EnquiryMessage.objects.create(
            enquiry=enquiry,
            sender=request.user,
            message=request.POST.get("message")
        )
        return redirect("admin_enquiry_chat", enquiry_id=enquiry.id)

    messages_qs = enquiry.messages.select_related("sender").order_by("created_at")

    return render(request, "core/admin_enquiry_chat.html", {
        "enquiry": enquiry,
        "messages": messages_qs
    })


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from accounts.decorators import staff_required
from core.models import Enrollment


@staff_required
def edit_enrollment(request, enrollment_id):
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)

    if request.method == "POST":
        enrollment.mentor_name = request.POST.get("mentor_name")
        enrollment.mentor_email = request.POST.get("mentor_email")
        enrollment.course_timing = request.POST.get("course_timing")
        enrollment.training_link = request.POST.get("training_link")
        enrollment.is_completed = "is_completed" in request.POST

        if request.FILES.get("certificate"):
            enrollment.certificate = request.FILES["certificate"]

        enrollment.save()
        messages.success(request, "Enrollment details updated successfully.")
        return redirect("admin_enrollments")

    return render(request, "core/edit_enrollment.html", {
        "enrollment": enrollment
    })
