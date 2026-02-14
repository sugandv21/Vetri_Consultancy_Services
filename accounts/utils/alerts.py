from accounts.models import Notification

from django.contrib.auth import get_user_model

User = get_user_model()


# ---------------- USER NOTIFICATION ----------------
def notify_user(user, title, message):
    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        is_admin_alert=False
    )


# ---------------- ADMIN ALERT ----------------
def admin_alert(title, message):
    Notification.objects.create(
        user=None,
        title=title,
        message=message,
        is_admin_alert=True
    )
