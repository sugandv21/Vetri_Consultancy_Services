from django.utils import timezone
from datetime import timedelta
from .models import ConsultantSession


SESSION_LIMITS = {
    "FREE": 0,
    "PRO": 1,
    "PRO_PLUS": 4,
}


def can_book_session(user):

    limit = SESSION_LIMITS.get(user.plan, 0)

    if limit is None:
        return True

    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0)

    used = ConsultantSession.objects.filter(
        user=user,
        created_at__gte=month_start
    ).count()

    return used < limit
