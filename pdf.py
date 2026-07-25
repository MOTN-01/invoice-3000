from datetime import date
from decimal import Decimal
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph


def generate_invoice(invoicee, address, works, price, invoice_number, material, material_price, biz):
    today = date.today().strftime("%m/%d/%Y")
    total_price = Decimal(price) + Decimal(material_price)

    PAGE_W, PAGE_H = letter
    MARGIN = 50
    CONTENT_W = PAGE_W - 2 * MARGIN
    DESC_W = int(CONTENT_W * 0.70)
    PRICE_X = PAGE_W - MARGIN - 10

    ACCENT  = colors.HexColor('#1e3a8a')
    BLACK   = colors.HexColor('#1a1a1a')
    GRAY    = colors.HexColor('#888888')
    DIVIDER = colors.HexColor('#cccccc')

    def esc(text):
        return (text.replace('&', '&amp;')
                    .replace('<', '&lt;')
                    .replace('>', '&gt;')
                    .replace('\n', '<br/>'))

    body = ParagraphStyle('body', fontName='Helvetica', fontSize=10, leading=14, textColor=BLACK)

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)

    # ── Header ───────────────────────────────────────────────────────────────
    y = PAGE_H - 45
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(BLACK)
    c.drawString(MARGIN, y, biz.get('company', ''))
    c.setFont("Helvetica-Bold", 30)
    c.setFillColor(ACCENT)
    c.drawRightString(PAGE_W - MARGIN, y, "INVOICE")

    y -= 18
    c.setFont("Helvetica", 10)
    c.setFillColor(GRAY)
    c.drawString(MARGIN, y, biz.get('street', ''))
    c.drawRightString(PAGE_W - MARGIN, y, f"#{invoice_number}")

    y -= 13
    c.drawString(MARGIN, y, biz.get('phone', ''))
    c.drawRightString(PAGE_W - MARGIN, y, today)

    y -= 18
    c.setStrokeColor(ACCENT)
    c.setLineWidth(1.5)
    c.line(MARGIN, y, PAGE_W - MARGIN, y)

    # ── Bill To + Balance Due ─────────────────────────────────────────────────
    y -= 22
    top_of_billing = y

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(GRAY)
    c.drawString(MARGIN, y, "BILL TO")
    y -= 14

    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(BLACK)
    c.drawString(MARGIN, y, invoicee.name)
    y -= 13

    c.setFont("Helvetica", 10)
    c.drawString(MARGIN, y, invoicee.street)
    y -= 13
    c.drawString(MARGIN, y, invoicee.city_state_zip)
    y -= 13

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(GRAY)
    c.drawRightString(PAGE_W - MARGIN, top_of_billing, "BALANCE DUE")
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(ACCENT)
    c.drawRightString(PAGE_W - MARGIN, top_of_billing - 22, f"${total_price:.2f}")
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(GRAY)
    c.drawRightString(PAGE_W - MARGIN, top_of_billing - 38, "Due upon receipt")

    y -= 16
    c.setStrokeColor(DIVIDER)
    c.setLineWidth(0.75)
    c.line(MARGIN, y, PAGE_W - MARGIN, y)

    # ── Items header bar ─────────────────────────────────────────────────────
    y -= 14
    c.setFillColor(ACCENT)
    c.roundRect(MARGIN, y - 5, CONTENT_W, 22, 3, stroke=0, fill=1)
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.white)
    c.drawString(MARGIN + 10, y + 3, "DESCRIPTION")
    c.drawRightString(PRICE_X, y + 3, "AMOUNT")

    # ── Work row ─────────────────────────────────────────────────────────────
    y -= 20
    p1 = Paragraph(esc(works), body)
    _, h1 = p1.wrapOn(c, DESC_W, 600)
    p1.drawOn(c, MARGIN + 10, y - h1)
    c.setFont("Helvetica", 10)
    c.setFillColor(BLACK)
    c.drawRightString(PRICE_X, y - 4, f"${Decimal(price):.2f}")
    y -= h1 + 10

    has_materials = bool(material.strip()) or Decimal(material_price) != 0

    if has_materials:
        c.setStrokeColor(DIVIDER)
        c.setLineWidth(0.5)
        c.line(MARGIN, y, PAGE_W - MARGIN, y)

        # ── Materials row ────────────────────────────────────────────────────
        y -= 14
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(GRAY)
        c.drawString(MARGIN + 10, y, "MATERIALS")
        c.setFont("Helvetica", 10)
        c.setFillColor(BLACK)
        c.drawRightString(PRICE_X, y - 1, f"${Decimal(material_price):.2f}")

        y -= 14
        p2 = Paragraph(esc(material), body)
        _, h2 = p2.wrapOn(c, DESC_W, 600)
        p2.drawOn(c, MARGIN + 10, y - h2)
        y -= h2 + 20
    else:
        y -= 20

    # ── Total ────────────────────────────────────────────────────────────────
    c.setStrokeColor(ACCENT)
    c.setLineWidth(1)
    c.line(MARGIN, y, PAGE_W - MARGIN, y)
    y -= 18

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(BLACK)
    c.drawString(MARGIN + DESC_W + 10, y, "TOTAL")
    c.setFillColor(ACCENT)
    c.drawRightString(PRICE_X, y, f"${total_price:.2f}")

    # ── Notes ─────────────────────────────────────────────────────────────────
    y -= 35
    c.setStrokeColor(DIVIDER)
    c.setLineWidth(0.5)
    c.line(MARGIN, y, PAGE_W - MARGIN, y)
    y -= 14

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(GRAY)
    c.drawString(MARGIN, y, "NOTES")
    y -= 14

    p_addr = Paragraph(esc(address), body)
    _, h_addr = p_addr.wrapOn(c, CONTENT_W, 200)
    p_addr.drawOn(c, MARGIN, y - h_addr)

    c.save()
    buf.seek(0)
    return buf
