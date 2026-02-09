from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from accounts.decorators import staff_required
from .models import ConsultantSession


# ---------------- REQUESTED ----------------
@staff_required
def admin_session_requests(request):
    sessions = ConsultantSession.objects.filter(status="REQUESTED").order_by("-created_at")
    return render(request, "consultation/admin/requests.html", {"sessions": sessions})


# ---------------- SCHEDULE SESSION ----------------
@staff_required
def schedule_session(request, session_id):
    session = get_object_or_404(ConsultantSession, id=session_id)

    if request.method == "POST":
        session.meeting_link = request.POST.get("meeting_link")
        session.scheduled_at = request.POST.get("scheduled_at")
        session.status = "SCHEDULED"
        session.save()

        messages.success(request, "Session scheduled successfully.")
        return redirect("admin_session_scheduled")

    return render(request, "consultation/admin/schedule.html", {"session": session})


# ---------------- SCHEDULED ----------------
@staff_required
def admin_session_scheduled(request):
    sessions = ConsultantSession.objects.filter(status="SCHEDULED").order_by("scheduled_at")
    return render(request, "consultation/admin/scheduled.html", {"sessions": sessions})


# ---------------- COMPLETED ----------------
@staff_required
def admin_session_completed(request):
    sessions = ConsultantSession.objects.filter(status="COMPLETED").order_by("-scheduled_at")
    return render(request, "consultation/admin/completed.html", {"sessions": sessions})


# ---------------- MARK COMPLETED ----------------
@staff_required
def mark_completed(request, session_id):
    session = get_object_or_404(ConsultantSession, id=session_id)
    session.status = "COMPLETED"
    session.save()

    messages.success(request, "Session marked completed.")
    return redirect("admin_session_completed")
