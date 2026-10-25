import os
import csv
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "sample_docs")

def ensure_sample_dir():
    os.makedirs(SAMPLE_DIR, exist_ok=True)

def generate_pdf_invoice(filepath: str, title: str, vendor: str, invoice_no: str, date: str, items: list, subtotal: float, tax: float, total: float):
    doc = SimpleDocTemplate(filepath, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    story = []
    
    # Title & Vendor Header
    story.append(Paragraph(f"<b>{vendor}</b>", styles['Heading1']))
    story.append(Paragraph("1200 Industrial Parkway, Suite 400<br/>Chicago, IL 60601 | accounts@vendor.com", styles['Normal']))
    story.append(Spacer(1, 15))
    
    # Metadata Box
    meta_data = [
        [f"Document: {title}", f"Invoice #: {invoice_no}"],
        [f"Date: {date}", f"Payment Terms: Net 30"]
    ]
    meta_table = Table(meta_data, colWidths=[260, 260])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
        ('PADDING', (0,0), (-1,-1), 6),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 20))
    
    # Line Items Table
    table_data = [["Description", "Qty", "Unit Price", "Total"]]
    for item in items:
        table_data.append([
            item["desc"],
            str(item["qty"]),
            f"${item['unit']:,.2f}",
            f"${item['total']:,.2f}"
        ])
    
    # Totals rows
    table_data.append(["", "", "Subtotal:", f"${subtotal:,.2f}"])
    table_data.append(["", "", "Sales Tax:", f"${tax:,.2f}"])
    table_data.append(["", "", "Grand Total:", f"${total:,.2f}"])
    
    item_table = Table(table_data, colWidths=[280, 60, 90, 90])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, len(items)), 0.5, colors.lightgrey),
        ('FONTNAME', (2, len(items)+1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (2, -1), (-1, -1), colors.HexColor("#f1f5f9")),
    ]))
    story.append(item_table)
    
    story.append(Spacer(1, 30))
    story.append(Paragraph("<i>Thank you for your business. Remit payment within terms.</i>", styles['Italic']))
    
    doc.build(story)


def generate_all_samples():
    ensure_sample_dir()
    
    # 1. Clean HVAC Inbound Invoice (Auto-passes)
    clean_hvac = os.path.join(SAMPLE_DIR, "Apex_HVAC_Supply_INV-8821.pdf")
    generate_pdf_invoice(
        clean_hvac,
        title="INVOICE",
        vendor="Apex HVAC Supply Co.",
        invoice_no="INV-8821",
        date="2026-09-02",
        items=[
            {"desc": "Commercial Compressor Model X-400", "qty": 2, "unit": 450.00, "total": 900.00},
            {"desc": "R-410A Refrigerant 25lb Cylinder", "qty": 4, "unit": 180.00, "total": 720.00},
            {"desc": "Heavy Duty Copper Tubing 50ft Coil", "qty": 3, "unit": 85.00, "total": 255.00}
        ],
        subtotal=1875.00,
        tax=150.00,
        total=2025.00
    )

    # 2. Logistics Bill of Lading with Discrepancy (Math mismatch: Total billed is $500 too high)
    error_freight = os.path.join(SAMPLE_DIR, "NorthStar_Logistics_BOL-4091_MATH_ERROR.pdf")
    generate_pdf_invoice(
        error_freight,
        title="FREIGHT BILL & RECONCILIATION",
        vendor="NorthStar Freight Logistics LLC",
        invoice_no="BOL-4091",
        date="2026-09-04",
        items=[
            {"desc": "LTL Freight Transit (Chicago -> Detroit)", "qty": 1, "unit": 850.00, "total": 850.00},
            {"desc": "Fuel Surcharge Baseline 14%", "qty": 1, "unit": 119.00, "total": 119.00},
            {"desc": "Liftgate & Inside Delivery Accessorial", "qty": 1, "unit": 125.00, "total": 125.00}
        ],
        subtotal=1094.00,
        tax=0.00,
        total=1594.00 # Stated total is $1,594.00 instead of $1,094.00 (Vendor overbilling)
    )

    # 3. High-Value Equipment Invoice (Triggers High-Value Compliance Flag > $5,000)
    high_value = os.path.join(SAMPLE_DIR, "Metro_Dental_Supply_INV-9904_HIGH_VALUE.pdf")
    generate_pdf_invoice(
        high_value,
        title="EQUIPMENT ORDER INVOICE",
        vendor="Metro Dental Lab & Equipment Inc.",
        invoice_no="INV-9904",
        date="2026-09-05",
        items=[
            {"desc": "Digital Intraoral 3D Imaging Scanner", "qty": 1, "unit": 6200.00, "total": 6200.00},
            {"desc": "Autoclave Sterilization Chamber 20L", "qty": 1, "unit": 1450.00, "total": 1450.00}
        ],
        subtotal=7650.00,
        tax=612.00,
        total=8262.00
    )

    # 4. Inbound CSV Dispatch Feed
    csv_file = os.path.join(SAMPLE_DIR, "Dispatch_Batch_0907.csv")
    with open(csv_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "description", "quantity", "unit_price", "total", "item_code"])
        writer.writerow(["2026-09-06", "Emergency Plumbing Service Call", "1", "185.00", "185.00", "SRV-PLUMB"])
        writer.writerow(["2026-09-06", "Cast Iron Pipe Section Replacement", "2", "120.00", "240.00", "MAT-PIPE"])
        writer.writerow(["2026-09-06", "Master Technician Overtime Labor", "3.5", "95.00", "332.50", "LAB-OT"])
    
    print(f"Generated sample operational documents in {SAMPLE_DIR}")

if __name__ == "__main__":
    generate_all_samples()
