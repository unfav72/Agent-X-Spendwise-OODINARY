"""
Spendwise AI - Excel and PDF Sample Statement Generator
Creates data/sample_statement.xlsx and data/sample_statement.pdf for upload testing.
"""

import os
import csv
import openpyxl
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_excel():
    csv_path = os.path.join("data", "sample_transactions.csv")
    xlsx_path = os.path.join("data", "sample_statement.xlsx")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Statement"

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            ws.append(row)

    wb.save(xlsx_path)
    print(f"Generated Excel statement at {xlsx_path}")

def generate_pdf():
    csv_path = os.path.join("data", "sample_transactions.csv")
    pdf_path = os.path.join("data", "sample_statement.pdf")

    doc = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=12
    )
    elements.append(Paragraph("HDFC Bank Account Statement (Synthetic Audit Copy)", title_style))
    elements.append(Paragraph("Account No: 50100492819283 | Currency: INR | Branch: Indiranagar, Bangalore", styles["Normal"]))
    elements.append(Spacer(1, 15))

    # Load first 25 transactions for clean PDF representation
    table_data = [["Date", "Description", "Debit", "Credit", "Reference"]]
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        count = 0
        for r in reader:
            table_data.append([
                r["transaction_date"],
                r["description"][:32],
                r["debit"],
                r["credit"],
                r["reference_id"]
            ])
            count += 1
            if count >= 30:
                break

    t = Table(table_data, colWidths=[75, 230, 65, 65, 115])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("ALIGN", (2, 0), (3, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
    ]))
    elements.append(t)
    doc.build(elements)
    print(f"Generated PDF statement at {pdf_path}")

if __name__ == "__main__":
    generate_excel()
    generate_pdf()

