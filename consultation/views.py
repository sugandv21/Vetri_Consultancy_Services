from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ConsultantSession
from .services import can_book_session


@login_required
def request_session(request):

    if not can_book_session(request.user):
        messages.error(request, "Monthly session limit reached. Upgrade your plan.")
        return redirect("dashboard")

    if request.method == "POST":
        topic = request.POST.get("topic")
        message = request.POST.get("message")

        session = ConsultantSession.objects.create(
            user=request.user,
            topic=topic,
            message=message
        )

        # PRIORITY ALERT FOR PRO PLUS
        if request.user.plan == "PRO_PLUS":
            from accounts.models import Notification
            from django.contrib.auth import get_user_model

            User = get_user_model()

            admins = User.objects.filter(is_staff=True)

            for admin in admins:
                Notification.objects.create(
                    user=admin,
                    title="🚨 Priority Consultation Request",
                    message=f"{request.user.profile.full_name or request.user.email} (Pro Plus) requested a session: {topic}"
                )


        messages.success(request, "Session request submitted.")
        return redirect("my_sessions")

    return render(request, "consultation/request_session.html")


@login_required
def my_sessions(request):
    sessions = ConsultantSession.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "consultation/my_sessions.html", {"sessions": sessions})
