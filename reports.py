
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from datetime import datetime

def money(cur: str, v: float) -> str:
    return f"{cur}{float(v):,.2f}"

def export_tax_working_pack(path, practice_name, company_name, period_label, currency, pl, vat, notes=""):
    c = canvas.Canvas(path, pagesize=A4)
    w, h = A4
    m = 15*mm

    c.setFillColorRGB(0.06, 0.23, 0.55)
    c.rect(0, h-25*mm, w, 25*mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(m, h-16*mm, practice_name)
    c.setFont("Helvetica", 10)
    c.drawString(m, h-22*mm, "VAT & Tax Working Pack (Draft)")
    c.setFillColor(colors.black)

    c.setFont("Helvetica-Bold", 12)
    c.drawString(m, h-40*mm, company_name)
    c.setFont("Helvetica", 10)
    c.drawString(m, h-48*mm, f"Period: {period_label}")
    c.drawString(m, h-56*mm, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    c.showPage()

    c.setFont("Helvetica-Bold", 14)
    c.drawString(m, h-20*mm, "Profit & Loss (from transactions)")
    y = h-35*mm
    for label, val in [("Income", pl.get("income",0)), ("Expenses", pl.get("expense",0)), ("Profit", pl.get("profit",0))]:
        c.setFont("Helvetica", 10)
        c.drawString(m, y, label)
        c.setFont("Helvetica-Bold", 10)
        c.drawRightString(w-m, y, money(currency, val))
        y -= 8*mm
    c.showPage()

    c.setFont("Helvetica-Bold", 14)
    c.drawString(m, h-20*mm, "VAT Summary (Estimate)")
    y = h-35*mm
    for label, val in [
        ("Sales (VAT-inclusive)", vat.get("sales_vat_inclusive",0)),
        ("Purchases (VAT-inclusive)", vat.get("purchases_vat_inclusive",0)),
        ("Output VAT", vat.get("output_vat",0)),
        ("Input VAT", vat.get("input_vat",0)),
        ("VAT Payable/(Refund)", vat.get("vat_payable",0)),
    ]:
        c.setFont("Helvetica", 10)
        c.drawString(m, y, label)
        c.setFont("Helvetica-Bold", 10)
        c.drawRightString(w-m, y, money(currency, val))
        y -= 8*mm
    c.showPage()

    c.setFont("Helvetica-Bold", 12)
    c.drawString(m, h-25*mm, "Notes / Adjustments (fill in before submission)")
    c.setFont("Helvetica", 10)
    t = c.beginText(m, h-35*mm)
    for line in (notes or "").splitlines()[:40]:
        t.textLine(line[:120])
    c.drawText(t)
    c.save()
