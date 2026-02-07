from django.utils import timezone
from jobs.models import JobApplication

# monthly limits
LIMITS = {
    "FREE": 5,
    "PRO": 10,
    "PRO_PLUS": None,  # unlimited
}


def applications_used_this_month(user):
    now = timezone.now()
    start_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    return JobApplication.objects.filter(
        user=user,
        applied_at__gte=start_month
    ).count()


def get_active_plan(user):
    """
    Billing-safe plan detection.
    Expired users automatically fallback to FREE.
    """
    if user.plan_status != "ACTIVE":
        return "FREE"
    return user.plan


def can_apply(user):
    tier = get_active_plan(user)

    limit = LIMITS.get(tier)

    # unlimited plan
    if limit is None:
        return True, None, None

    used = applications_used_this_month(user)

    if used >= limit:
        return False, used, limit

    return True, used, limit
