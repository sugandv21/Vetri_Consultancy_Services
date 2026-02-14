from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils.timezone import localtime, make_aware
from datetime import datetime
from django.contrib.auth import get_user_model

from accounts.decorators import admin_required
from accounts.models import Notification
from .models import ConsultantSession

User = get_user_model()


# ---------------- REQUESTED ----------------
@admin_required
def admin_session_requests(request):
    sessions = ConsultantSession.objects.filter(status="REQUESTED").order_by("-created_at")
    return render(request, "consultation/admin/requests.html", {"sessions": sessions})


# ---------------- SCHEDULE SESSION ----------------
@admin_required
def schedule_session(request, session_id):

    session = get_object_or_404(ConsultantSession, id=session_id)

    # get trainers every request (NOT globally)
    trainers = User.objects.filter(is_staff=True, is_superuser=False)

    if request.method == "POST":

        trainer_id = request.POST.get("trainer")
        meeting_link = request.POST.get("meeting_link")
        scheduled_at = request.POST.get("scheduled_at")

        if not trainer_id or not meeting_link or not scheduled_at:
            messages.error(request, "All fields required.")
            return redirect("schedule_session", session_id=session.id)

        trainer = get_object_or_404(User, id=trainer_id)

        dt = datetime.strptime(scheduled_at, "%Y-%m-%dT%H:%M")

        session.trainer = trainer
        session.meeting_link = meeting_link
        session.scheduled_at = make_aware(dt)
        session.status = "SCHEDULED"
        session.save()

        # -------- notify candidate --------
        Notification.objects.create(
            user=session.user,
            title="Consultation Scheduled",
            message=f"Your consultation is scheduled on {localtime(session.scheduled_at).strftime('%d %b %I:%M %p')}"
        )

        # -------- notify trainer --------
        Notification.objects.create(
            user=trainer,
            title="New Session Assigned",
            message=f"You have a consultation with {session.user.email} on {localtime(session.scheduled_at).strftime('%d %b %I:%M %p')}"
        )

        messages.success(request, "Session scheduled successfully.")
        return redirect("admin_session_scheduled")

    return render(request, "consultation/admin/schedule.html", {
        "session": session,
        "trainers": trainers
    })


# ---------------- SCHEDULED ----------------
@admin_required
def admin_session_scheduled(request):
    sessions = ConsultantSession.objects.filter(
        status__in=["SCHEDULED", "ATTENDED"]
    ).order_by("scheduled_at")

    return render(request, "consultation/admin/scheduled.html", {"sessions": sessions})


# ---------------- COMPLETED ----------------
@admin_required
def admin_session_completed(request):
    sessions = ConsultantSession.objects.filter(status="COMPLETED").order_by("-scheduled_at")
    return render(request, "consultation/admin/completed.html", {"sessions": sessions})


# ---------------- ADMIN VERIFY COMPLETION ----------------
@admin_required
def mark_completed(request, session_id):

    session = get_object_or_404(ConsultantSession, id=session_id)

    # Only allow after trainer attended
    if session.status != "ATTENDED":
        messages.error(request, "Trainer has not completed the session yet.")
        return redirect("admin_session_scheduled")

    # Ensure feedback exists
    if not session.feedback or not session.feedback.strip():
        messages.error(request, "Trainer has not submitted feedback.")
        return redirect("admin_session_scheduled")

    session.status = "COMPLETED"
    session.save()

    # Notify candidate
    Notification.objects.create(
        user=session.user,
        title="Session Verified",
        message="Your consultation session has been verified by admin."
    )

    messages.success(request, "Session verified and closed successfully.")
    return redirect("admin_session_completed")
