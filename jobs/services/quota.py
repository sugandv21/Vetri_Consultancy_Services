from django.utils import timezone
from jobs.models import JobApplication

LIMITS = {
    "FREE": 10,
    "PRO": 5,
    "PRO_PLUS": None,
}


def applications_used_this_month(user):
    now = timezone.localtime()
    start_month = now.date().replace(day=1)

    return JobApplication.objects.filter(
        user=user,
        applied_at__date__gte=start_month
    ).count()


def get_active_plan(user):
    if user.plan_status != "ACTIVE":
        return "FREE"
    return user.plan


def can_apply_quota(user):
    tier = get_active_plan(user)

    limit = LIMITS.get(tier, LIMITS["FREE"])

    if limit is None:
        return True, None, None

    used = applications_used_this_month(user)

    if used >= limit:
        return False, used, limit

    return True, used, limit
