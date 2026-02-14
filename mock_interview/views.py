from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from .models import MockInterview, InterviewFeedback
from accounts.models import Notification

User = get_user_model()


# ---------------------------------
# CANDIDATE REQUEST INTERVIEW
# ---------------------------------
@login_required
def schedule_mock(request):

    if request.method == "POST":

        interview = MockInterview.objects.create(
            candidate=request.user,
            preferred_date=request.POST.get("preferred_date"),
            preferred_time=request.POST.get("preferred_time"),
            status="pending"
        )

        # 🔔 notify admins
        Notification.objects.create(
            user=None,
            title="Mock Interview Request",
            message=f"New mock interview request from {request.user.email} completed",
            type=Notification.TRAINER,
            is_admin_alert=True
        )


        return redirect("my_mock_interviews")

    return render(request, "mock_interview/schedule.html")



# ---------------------------------
# CANDIDATE VIEW INTERVIEWS
# ---------------------------------
@login_required
def my_mock_interviews(request):

    interviews = MockInterview.objects.filter(candidate=request.user).order_by("-preferred_date")

    return render(request, "mock_interview/my_interviews.html", {
        "interviews": interviews
    })


# ---------------------------------
# JOIN INTERVIEW PAGE
# ---------------------------------
@login_required
def join_mock(request, pk):

    interview = get_object_or_404(MockInterview, pk=pk)

    # only owner or admin can open
    if interview.candidate != request.user and not request.user.is_staff:
        return redirect("my_mock_interviews")

    return render(request, "mock_interview/join.html", {
        "interview": interview
    })


# ---------------------------------
# ADMIN DASHBOARD LIST PAGE
# ---------------------------------
from .models import MockInterview, InterviewFeedback

@staff_member_required
def admin_mock_list(request):

    interviews = MockInterview.objects.all().select_related("candidate","consultant")

    # attach feedback existence flag
    feedback_map = set(
        InterviewFeedback.objects.values_list("interview_id", flat=True)
    )

    for i in interviews:
        i.has_feedback = i.id in feedback_map

    return render(request, "mock_interview/admin_list.html", {
        "interviews": interviews
    })



# ---------------------------------
# ADMIN UPDATE PAGE
# Upload meeting link + confirm time
# ---------------------------------
@staff_member_required
def admin_mock_update(request, pk):

    interview = get_object_or_404(MockInterview, pk=pk)
    consultants = User.objects.filter(is_staff=True)

    if request.method == "POST":

        interview.consultant_id = request.POST.get("consultant") or None
        interview.scheduled_datetime = request.POST.get("scheduled_datetime") or None
        interview.meeting_link = request.POST.get("meeting_link")
        interview.status = request.POST.get("status")

        interview.save()

        # 🔔 notify candidate when scheduled
        if interview.status == "scheduled":
            Notification.objects.create(
                user=interview.candidate,
                title="Interview Scheduled",
                message="Your mock interview has been scheduled. Check My Interview section."
            )

            # 🔔 notify admin (THIS FIXES COUNTER)
            Notification.objects.create(
                user=None,
                title="Interview Scheduled",
                message=f"Trainer Completed interview for {interview.candidate.email} and submitted report",
                type=Notification.TRAINER
            )

            # 🔔 notify trainer (NEW)
            if interview.consultant:
                Notification.objects.create(
                    user=interview.consultant,
                    title="New Mock Interview Assigned",
                    message=f"You have been assigned a mock interview with {interview.candidate.email}"
                )


        return redirect("admin_mock_list")

    return render(request, "mock_interview/admin_update.html", {
        "interview": interview,
        "consultants": consultants
    })


# ---------------------------------
# ADMIN SUBMIT FEEDBACK
# ---------------------------------
@staff_member_required
def mock_feedback(request, pk):

    interview = get_object_or_404(MockInterview, pk=pk)

    if request.method == "POST":
        InterviewFeedback.objects.update_or_create(
            interview=interview,
            defaults={
                "rating": request.POST.get("rating"),
                "strengths": request.POST.get("strengths"),
                "improvements": request.POST.get("improvements"),
                "notes": request.POST.get("notes"),
            }
        )

        interview.status = "completed"
        interview.save()

        # 🔔 notify candidate feedback ready
        # 🔔 notify candidate
        Notification.objects.create(
            user=interview.candidate,
            title="Interview Feedback Ready",
            message="Your mock interview feedback has been updated. Check My Interview → Feedback."
        )

        # 🔔 notify admin (THIS FIXES COUNTER)
        Notification.objects.create(
            user=None,
            title="Feedback Submitted",
            message=f"Trainer submitted feedback for {interview.candidate.email}",
            type=Notification.TRAINER
        )


        return redirect("admin_mock_list")

    return render(request, "mock_interview/feedback.html", {
        "interview": interview
    })


# ---------------------------------
# CANDIDATE VIEW REPORT
# ---------------------------------
@login_required
def mock_report(request, pk):

    interview = get_object_or_404(MockInterview, pk=pk)

    if interview.candidate != request.user and not request.user.is_staff:
        return redirect("my_mock_interviews")

    feedback = get_object_or_404(InterviewFeedback, interview=interview)

    return render(request, "mock_interview/report.html", {
        "feedback": feedback
    })
