from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from io import BytesIO


def build_invoice(payment, user):
    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()
    elements = []

    # Header
    elements.append(Paragraph("VCS Career Consultancy", styles["Title"]))
    elements.append(Paragraph("Invoice", styles["Heading2"]))
    elements.append(Spacer(1, 20))

    # Customer info
    # Customer details
    customer_name = getattr(user.profile, "full_name", user.email)
    purchase_date = payment.created_at.strftime("%d %b %Y")

    elements.append(Paragraph(f"<b>Customer Name:</b> {customer_name}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Email:</b> {user.email}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Purchase Date:</b> {purchase_date}", styles["Normal"]))
    elements.append(Spacer(1, 20))


    # Description
    if payment.payment_type == "PLAN":
        desc = f"Subscription Plan - {user.plan}"
    else:
        desc = payment.training.title if payment.training else "Training Purchase"

    amount = "FREE" if payment.amount == 0 else f"₹{payment.amount}"

    data = [
        ["Description", "Amount"],
        [desc, amount],
    ]

    table = Table(data, colWidths=[350, 150])
    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 30))

    elements.append(Paragraph("Thank you for your purchase!", styles["Normal"]))

    pdf.build(elements)
    buffer.seek(0)

    return buffer
