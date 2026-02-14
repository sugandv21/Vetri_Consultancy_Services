from django.shortcuts import render
from accounts.decorators import staff_required
from core.models import Enrollment, TrainingEnquiry
from django.shortcuts import get_object_or_404



from django.db.models import Count, Q
from core.models import Enrollment, ModuleProgress

@staff_required
def admin_enrollments(request):

    enrollments = Enrollment.objects.select_related("user", "training")

    # attach progress data
    for e in enrollments:
        total = e.module_progress.count()
        completed = e.module_progress.filter(is_completed=True).count()

        if total == 0:
            percent = 0
        else:
            percent = int((completed / total) * 100)

        e.total_modules = total
        e.completed_modules = completed
        e.percent = percent

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
        fee_value = request.POST.get("fee")

        Training.objects.create(
            title=request.POST.get("title"),
            description=request.POST.get("description"),
            duration=request.POST.get("duration") or "",
            fee=fee_value if fee_value else 0,
            image=request.FILES.get("image"),
            is_active=bool(request.POST.get("is_active")),
            placement_support=bool(request.POST.get("placement_support")),
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

from core.utils.certificate_generator import generate_certificate
from core.models import TrainingCompletion

@staff_required
def edit_enrollment(request, enrollment_id):
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)

    if request.method == "POST":
        enrollment.mentor_name = request.POST.get("mentor_name")
        enrollment.mentor_email = request.POST.get("mentor_email")
        enrollment.course_timing = request.POST.get("course_timing")
        enrollment.training_link = request.POST.get("training_link")

        completed_checked = "is_completed" in request.POST

        # only when switching from False → True
        if completed_checked and not enrollment.is_completed:
            enrollment.is_completed = True

            file_path = generate_certificate(enrollment)
            enrollment.certificate = file_path

            TrainingCompletion.objects.filter(
                enrollment=enrollment
            ).update(status=TrainingCompletion.COMPLETED_BY_TRAINER)

        else:
            enrollment.is_completed = completed_checked

        if request.FILES.get("certificate"):
            enrollment.certificate = request.FILES["certificate"]

        enrollment.save()
        messages.success(request, "Enrollment details updated successfully.")
        return redirect("admin_enrollments")

    return render(request, "core/edit_enrollment.html", {"enrollment": enrollment})



from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from .models import Training, Enrollment


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from .models import Training, TrainingModule


@staff_member_required
def training_modules_admin(request, training_id):

    training = get_object_or_404(Training, id=training_id)
    modules = TrainingModule.objects.filter(training=training).order_by("order")

    if request.method == "POST":

        # ADD MODULE
        if "add_module" in request.POST:
            title = request.POST.get("title")
            description = request.POST.get("description")

            order = modules.count() + 1

            TrainingModule.objects.create(
                training=training,
                title=title,
                description=description,
                order=order
            )

            return redirect("training_modules_admin", training_id=training.id)

        # DELETE MODULE
        if "delete_module" in request.POST:
            module_id = request.POST.get("module_id")
            TrainingModule.objects.filter(id=module_id, training=training).delete()
            return redirect("training_modules_admin", training_id=training.id)

    return render(request, "core/training_modules.html", {
        "training": training,
        "modules": modules
    })



@staff_member_required
def training_students_admin(request, training_id):
    training = get_object_or_404(Training, id=training_id)
    students = Enrollment.objects.filter(training=training)
    return render(request, "core/training_students.html", {"training": training, "students": students})


@staff_member_required
def training_progress_admin(request, training_id):
    training = get_object_or_404(Training, id=training_id)
    students = Enrollment.objects.filter(training=training)
    return render(request, "core/training_progress.html", {"training": training, "students": students})


from accounts.models import Notification
from accounts.decorators import admin_required

@admin_required
def admin_alerts(request):

    alerts = Notification.objects.filter(
        is_admin_alert=True
    ).order_by("-created_at")

    # mark read
    alerts.filter(is_read=False).update(is_read=True)

    return render(request, "accounts/admin_alerts.html", {
        "alerts": alerts
    })
