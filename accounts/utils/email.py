import logging
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

def safe_send_mail(subject, message, recipient_list):
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            fail_silently=False,   # still detect failure
        )
        return True

    except Exception as e:
        logger.error(f"EMAIL FAILED: {e}")   # visible in Render logs
        return False




# from django.core.mail import send_mail
# from django.conf import settings
# import logging

# logger = logging.getLogger(__name__)

# def safe_send_mail(subject, message, recipient_list):
#     try:
#         send_mail(
#             subject,
#             message,
#             settings.DEFAULT_FROM_EMAIL,
#             recipient_list,
#             fail_silently=False,
#         )
#         return True
#     except Exception as e:
#         logger.error(f"MAIL ERROR: {e}")
#         return False



