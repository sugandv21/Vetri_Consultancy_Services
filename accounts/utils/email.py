import logging
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

def safe_send_mail(subject, message, recipient_list):
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"EMAIL FAILED: {e}")
        return False
