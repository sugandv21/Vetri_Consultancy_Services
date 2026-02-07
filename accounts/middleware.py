from django.utils import timezone
from django.contrib import messages
from .models import User

class SubscriptionMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.user.is_authenticated and not request.user.is_staff:


            user = request.user

            if user.plan in [User.PRO, User.PRO_PLUS]:
                if user.plan_end and timezone.now() > user.plan_end:

                    if user.plan_status != User.EXPIRED:
                        user.plan = User.FREE
                        user.plan_status = User.EXPIRED
                        user.plan_start = None
                        user.plan_end = None

                        user.save(update_fields=[
                            "plan",
                            "plan_status",
                            "plan_start",
                            "plan_end",
                        ])

                        if not request.session.get("shown_expiry_message"):
                            messages.warning(
                                request,
                                "Your subscription has expired. You are now on Free plan."
                            )
                            request.session["shown_expiry_message"] = True

        return self.get_response(request)
