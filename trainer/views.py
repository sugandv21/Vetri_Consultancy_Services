from django.shortcuts import render
from accounts.decorators import trainer_required


# dashboard
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta

from django.utils.timezone import localdate
from consultation.models import ConsultantSession
from accounts.decorators import trainer_required
from mock_interview.models import MockInterview
from accounts.models import Notification



@trainer_required
def trainer_dashboard(request):

    # Get current local time (IST safe)
    now = timezone.localtime()

    # Today start and end (00:00 → 23:59 local time)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    # ---------------- TODAY SESSIONS ----------------
    today_sessions = ConsultantSession.objects.filter(
        trainer=request.user,
        status="SCHEDULED",
        scheduled_at__gte=today_start,
        scheduled_at__lt=today_end
    ).select_related("user").order_by("scheduled_at")

    # ---------------- UPCOMING SESSIONS ----------------
    upcoming_sessions = ConsultantSession.objects.filter(
        trainer=request.user,
        status="SCHEDULED",
        scheduled_at__gte=today_end
    ).select_related("user").order_by("scheduled_at")[:5]

    # ---------------- COMPLETED COUNT ----------------
    completed_sessions = ConsultantSession.objects.filter(
        trainer=request.user,
        status="COMPLETED"
    ).count()

    # ---------------- ATTENDED COUNT (optional analytics) ----------------
    attended_sessions = ConsultantSession.objects.filter(
        trainer=request.user,
        status="ATTENDED"
    ).count()
    
    
    assigned_mock_count = MockInterview.objects.filter(
        consultant=request.user,
        status="SCHEDULED"
    ).count()


    trainer_alerts = request.user.notifications.filter(is_read=False).count()


    context = {
        "today_sessions": today_sessions,
        "upcoming_sessions": upcoming_sessions,
        "completed_sessions": completed_sessions,
        "attended_sessions": attended_sessions,
        "today_date": today_start.date(),
        "assigned_mock_count": assigned_mock_count,
        "trainer_alerts": trainer_alerts
    }

    return render(request, "trainer/trainer_dashboard.html", context)

# sessions
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from accounts.decorators import trainer_required
from consultation.models import ConsultantSession

from django.utils import timezone
from datetime import timedelta
from consultation.models import ConsultantSession


@trainer_required
def sessions_today(request):

    now = timezone.localtime()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    sessions = ConsultantSession.objects.filter(
        trainer=request.user,
        status="SCHEDULED",
        scheduled_at__gte=today_start,
        scheduled_at__lt=today_end
    ).select_related("user").order_by("scheduled_at")

    return render(request, "trainer/sessions_today.html", {
        "sessions": sessions
    })




from django.utils import timezone
from consultation.models import ConsultantSession


@trainer_required
def sessions_upcoming(request):

    now = timezone.localtime()

    upcoming_sessions = ConsultantSession.objects.filter(
        trainer=request.user,
        status="SCHEDULED",
        scheduled_at__gt=now
    ).select_related("user").order_by("scheduled_at")

    return render(request, "trainer/sessions_upcoming.html", {
        "sessions": upcoming_sessions
    })





@trainer_required
def attend_session(request, session_id):

    session = get_object_or_404(
        ConsultantSession,
        id=session_id,
        trainer=request.user
    )

    if request.method == "POST":

        feedback = request.POST.get("feedback")

        if not feedback:
            messages.error(request, "Feedback required")
            return redirect("sessions_today")

        session.feedback = feedback
        session.status = "ATTENDED"
        session.save()
        
        admin_alert(f"Consultation attended by trainer for {session.candidate.email}")


        messages.success(request, "Session marked attended")
        return redirect("trainer_sessions_completed")

    return render(request, "trainer/session_attend.html", {
        "session": session
    })


from django.shortcuts import get_object_or_404, redirect
from accounts.models import Notification


# @trainer_required
# def submit_feedback(request, session_id):

#     session = get_object_or_404(
#         ConsultantSession,
#         id=session_id,
#         trainer=request.user
#     )

#     if request.method == "POST":

#         feedback = request.POST.get("feedback")

#         if not feedback:
#             messages.error(request, "Feedback required.")
#             return redirect("trainer_submit_feedback", session_id=session.id)

#         session.feedback = feedback
#         session.status = "ATTENDED"
#         session.save()

#         # notify candidate
#         Notification.objects.create(
#             user=session.user,
#             title="Session Completed",
#             message="Your consultation session has been completed. Admin will review shortly."
#         )

#         messages.success(request, "Session marked attended.")
#         return redirect("sessions_today")

#     return render(request, "trainer/session_feedback.html", {
#         "session": session
#     })



# training
@trainer_required
def training_students(request):
    return render(request, "trainer/training_students.html")


@trainer_required
def module_progress(request):
    return render(request, "trainer/module_progress.html")


# mock interviews
@trainer_required
def mock_interviews(request):
    return render(request, "trainer/mock_interviews.html")


# escalations
@trainer_required
def escalations(request):
    return render(request, "trainer/escalations.html")
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages

from accounts.decorators import trainer_required
from consultation.models import ConsultantSession
from accounts.models import Notification


# ================= DASHBOARD =================
@trainer_required
def trainer_dashboard(request):

    now = timezone.localtime()

    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    # TODAY
    today_sessions = ConsultantSession.objects.filter(
        trainer=request.user,
        status="SCHEDULED",
        scheduled_at__gte=today_start,
        scheduled_at__lt=today_end
    ).select_related("user").order_by("scheduled_at")

    # UPCOMING
    upcoming_sessions = ConsultantSession.objects.filter(
        trainer=request.user,
        status="SCHEDULED",
        scheduled_at__gte=today_end
    ).select_related("user").order_by("scheduled_at")[:5]

    # COMPLETED COUNTS
    completed_sessions = ConsultantSession.objects.filter(
        trainer=request.user,
        status="COMPLETED"
    ).count()

    attended_sessions = ConsultantSession.objects.filter(
        trainer=request.user,
        status="ATTENDED"
    ).count()

    return render(request, "trainer/trainer_dashboard.html", {
        "today_sessions": today_sessions,
        "upcoming_sessions": upcoming_sessions,
        "completed_sessions": completed_sessions,
        "attended_sessions": attended_sessions,
        "today_date": today_start.date(),
    })


# ================= TODAY SESSIONS =================
@trainer_required
def sessions_today(request):

    now = timezone.localtime()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    sessions = ConsultantSession.objects.filter(
        trainer=request.user,
        status="SCHEDULED",
        scheduled_at__gte=today_start,
        scheduled_at__lt=today_end
    ).select_related("user").order_by("scheduled_at")

    return render(request, "trainer/sessions_today.html", {"sessions": sessions})


# ================= UPCOMING =================
@trainer_required
def sessions_upcoming(request):

    now = timezone.localtime()

    sessions = ConsultantSession.objects.filter(
        trainer=request.user,
        status="SCHEDULED",
        scheduled_at__gt=now
    ).select_related("user").order_by("scheduled_at")

    return render(request, "trainer/sessions_upcoming.html", {"sessions": sessions})


# ================= COMPLETED =================
@trainer_required
def sessions_completed(request):

    sessions = ConsultantSession.objects.filter(
        trainer=request.user,
        status__in=["ATTENDED", "COMPLETED"]
    ).select_related("user").order_by("-scheduled_at")

    return render(request, "trainer/sessions_completed.html", {"sessions": sessions})


# ================= FEEDBACK / ATTEND =================
@trainer_required
def submit_feedback(request, session_id):

    session = get_object_or_404(
        ConsultantSession,
        id=session_id,
        trainer=request.user
    )

    # Already handled
    if session.status != "SCHEDULED":
        messages.error(request, "Session already handled.")
        return redirect("trainer_sessions_today")

    # Prevent future attendance
    if session.scheduled_at > timezone.now():
        messages.error(request, "You cannot attend before scheduled time.")
        return redirect("trainer_sessions_today")

    if request.method == "POST":

        feedback = request.POST.get("feedback")

        if not feedback:
            messages.error(request, "Feedback required.")
            return redirect("trainer_submit_feedback", session_id=session.id)

        session.feedback = feedback
        session.status = "ATTENDED"
        session.save()

        # Notify candidate
        Notification.objects.create(
            user=session.user,
            title="Consultation Completed",
            message="Trainer has completed your consultation session. Admin will verify shortly."
        )

        messages.success(request, "Session marked attended.")
        return redirect("trainer_sessions_completed")

    return render(request, "trainer/session_feedback.html", {"session": session})


from core.models import Enrollment, ModuleProgress
from django.shortcuts import render, get_object_or_404
from accounts.decorators import trainer_required
@trainer_required
def trainer_training_students(request):

    enrollments = Enrollment.objects.filter(
        mentor_email=request.user.email
    ).select_related("training", "user").prefetch_related("module_progress__module", "completion")

    for e in enrollments:
        total = e.module_progress.count()
        done = e.module_progress.filter(is_completed=True).count()
        e.progress_percent = int((done/total)*100) if total else 0

    return render(request, "trainer/trainer_trainings.html", {
        "enrollments": enrollments
    })


from core.models import Enrollment, ModuleProgress
from django.shortcuts import get_object_or_404
from accounts.decorators import trainer_required

@trainer_required
def trainer_student_progress(request, enrollment_id):

    enrollment = get_object_or_404(
        Enrollment.objects.select_related("user", "training"),
        id=enrollment_id
    )

    progress_list = enrollment.module_progress.select_related("module").order_by("module__order")

    total = progress_list.count()
    completed = progress_list.filter(is_completed=True).count()
    percent = int((completed / total) * 100) if total else 0

    return render(request, "trainer/student_progress.html", {
        "enrollment": enrollment,
        "progress_list": progress_list,
        "percent": percent
    })


# ================= TRAINING PLACEHOLDERS =================


from core.models import Enrollment
from accounts.decorators import trainer_required

@trainer_required
def module_progress(request):

    enrollments = (
        Enrollment.objects
        .select_related("user", "training")
        .prefetch_related("module_progress__module")
    )

    rows = []

    for e in enrollments:

        total = e.module_progress.count()
        completed = e.module_progress.filter(is_completed=True).count()

        percent = int((completed / total) * 100) if total else 0

        if percent == 100:
            status = "Completed"
        elif percent == 0:
            status = "Not Started"
        else:
            status = "In Progress"

        rows.append({
            "enrollment": e,
            "total": total,
            "completed": completed,
            "percent": percent,
            "status": status
        })

    return render(request, "trainer/module_progress.html", {
        "rows": rows
    })


from django.http import JsonResponse
from django.utils import timezone
from core.models import ModuleProgress, TrainingCompletion, Enrollment
from accounts.decorators import trainer_required
from core.utils.certificate_generator import generate_certificate
from accounts.utils.alerts import admin_alert


@trainer_required
def trainer_mark_module_complete(request, progress_id):

    try:
        progress = ModuleProgress.objects.select_related("enrollment").get(id=progress_id)
    except ModuleProgress.DoesNotExist:
        return JsonResponse({"success": False}, status=404)

    # prevent double complete
    if progress.is_completed:
        return JsonResponse({"success": True})

    progress.is_completed = True
    progress.completed_at = timezone.now()
    progress.save()

    enrollment = progress.enrollment

    total = enrollment.module_progress.count()
    completed = enrollment.module_progress.filter(is_completed=True).count()
    percent = int((completed / total) * 100) if total else 0

    # auto completion
    if percent == 100 and not enrollment.is_completed:
        enrollment.is_completed = True

        file_path = generate_certificate(enrollment)
        enrollment.certificate = file_path
        enrollment.save()

        TrainingCompletion.objects.update_or_create(
            enrollment=enrollment,
            defaults={"status": TrainingCompletion.COMPLETED_BY_TRAINER}
        )
        
        admin_alert(f"{request.user.email} marked course completed for {enrollment.user.email}")

    return JsonResponse({
        "success": True,
        "percent": percent,
        "completed": percent == 100
    })

# ================= MOCK INTERVIEWS =================
from mock_interview.models import MockInterview, InterviewFeedback
from django.utils import timezone

from django.utils import timezone
from datetime import timedelta
from mock_interview.models import MockInterview

@trainer_required
def trainer_mock_list(request):

    now = timezone.localtime()
    today = now.date()

    interviews = MockInterview.objects.filter(
        consultant=request.user
    ).order_by("scheduled_datetime")

    # ---------------- TODAY ----------------
    today_interviews = interviews.filter(
        scheduled_datetime__date=today
    )

    # ---------------- UPCOMING ----------------
    upcoming_interviews = interviews.filter(
        scheduled_datetime__date__gt=today,
        status="scheduled"
    )

    # ---------------- PENDING FEEDBACK ----------------
    pending_feedback = interviews.filter(
        status="scheduled",
        scheduled_datetime__lt=now
    )

    # ---------------- COMPLETED ----------------
    completed = interviews.filter(status="completed")

    return render(request, "trainer/mock_list.html", {
        "today_interviews": today_interviews,
        "upcoming_interviews": upcoming_interviews,
        "pending_feedback": pending_feedback,
        "completed": completed,
        "now": timezone.localtime(),  
    })

@trainer_required
def trainer_join_mock(request, pk):

    interview = get_object_or_404(
        MockInterview,
        pk=pk,
        consultant=request.user
    )

    return render(request, "trainer/mock_join.html", {
        "interview": interview
    })
from accounts.models import Notification

from accounts.utils.alerts import notify_user, admin_alert

@trainer_required
def trainer_mock_feedback(request, pk):

    interview = get_object_or_404(
        MockInterview,
        pk=pk,
        consultant=request.user
    )

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

        # candidate notification
        notify_user(
            interview.candidate,
            "Mock Interview Feedback Ready",
            "Your mock interview feedback has been submitted."
        )

        # admin alert
        admin_alert(
            "Trainer Submitted Feedback",
            f"{request.user.email} submitted feedback for {interview.candidate.email}"
        )

        return redirect("trainer_mock_list")

    return render(request, "trainer/mock_feedback.html", {"interview": interview})

@trainer_required
def trainer_mock_report(request, pk):

    interview = get_object_or_404(
        MockInterview,
        pk=pk,
        consultant=request.user
    )

    feedback = get_object_or_404(InterviewFeedback, interview=interview)

    return render(request, "trainer/mock_report.html", {
        "feedback": feedback
    })



# ================= ESCALATIONS =================
@trainer_required
def escalations(request):
    return render(request, "trainer/escalations.html")
