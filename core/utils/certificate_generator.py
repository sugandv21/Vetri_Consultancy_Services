import os
from django.conf import settings
from core.models import CertificateDesign


def generate_certificate(enrollment):

    print("\n======= CERTIFICATE DEBUG START =======")

    design = CertificateDesign.objects.first()

    if not design:
        print("❌ No CertificateDesign found in DB")
        return None

    print("Company:", design.company_name)
    print("Background:", design.background)
    print("Logo:", design.logo)
    print("Signature:", design.signature)

    try:
        from reportlab.pdfgen import canvas

        filename = f"{enrollment.user.id}_{enrollment.training.id}.pdf"
        file_path = os.path.join(settings.MEDIA_ROOT, "certificates", filename)

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        c = canvas.Canvas(file_path)
        c.drawString(100, 750, f"Certificate for {enrollment.user}")
        c.drawString(100, 700, f"Training: {enrollment.training.title}")
        c.save()

        print("✅ PDF CREATED:", file_path)
        print("======= CERTIFICATE DEBUG END =======\n")

        return f"certificates/{filename}"

    except Exception as e:
        print("❌ CERTIFICATE ERROR:", str(e))
        print("======= CERTIFICATE DEBUG END =======\n")
        return None
