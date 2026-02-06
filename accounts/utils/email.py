import resend
from django.conf import settings

resend.api_key = settings.RESEND_API_KEY


def safe_send_mail(subject, message, recipient_list):
    """
    Sends email using Resend API.
    Never crashes the site.
    Returns True if sent, False if failed.
    """
    try:
        for email in recipient_list:
            resend.Emails.send({
                "from": settings.DEFAULT_FROM_EMAIL,
                "to": [email],
                "subject": subject,
                "text": message,
            })
        return True

    except Exception as e:
        print("EMAIL FAILED:", e)
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


