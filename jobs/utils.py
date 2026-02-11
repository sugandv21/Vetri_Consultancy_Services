from .models import Job


def visible_jobs_for_user(user):
    """
    Everyone can SEE all published jobs
    (used for listing & detail page)
    """
    return Job.objects.filter(status="PUBLISHED")


from accounts.models import User

def can_user_apply(user, job):

    if not user.is_authenticated:
        return False

    plan = getattr(user, "plan", User.FREE)

    # FREE jobs → everyone logged in
    if job.visibility == "FREE":
        return True

    # PRO jobs → PRO & PROPLUS
    if job.visibility == "PRO":
        return plan in [User.PRO, User.PRO_PLUS]

    # PROPLUS jobs → only PROPLUS
    if job.visibility == "PROPLUS":
        return plan == User.PRO_PLUS

    return False

from django.utils import timezone
from datetime import timedelta
from jobs.models import JobApplication


def can_apply(user):
    """
    Monthly job application quota based on subscription plan
    Returns: allowed, used, limit
    """

    # FREE PLAN → 20 applications/month
    if user.plan == User.FREE:
        limit = 20

    # PRO PLAN → 100 applications/month
    elif user.plan == User.PRO:
        limit = 100

    # PRO PLUS → unlimited
    else:
        return True, 0, None

    one_month_ago = timezone.now() - timedelta(days=30)

    used = JobApplication.objects.filter(
        user=user,
        applied_at__gte=one_month_ago
    ).count()

    allowed = used < limit

    return allowed, used, limit
