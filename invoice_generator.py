from dataclasses import dataclass, field
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import re

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet


# -----------------------------
# DATA CLASSES
# -----------------------------

@dataclass
class MoneyBox:
    title: str
    amount: str
    notes: list[str] = field(default_factory=list)


@dataclass
class InvoiceItem:
    item: str
    description: str
    price: str


@dataclass
class Invoice:
    title: str
    company_name: str
    company_address: str
    company_phone: str
    license_number: str

    prepared_for: str
    client_address: str
    prepared_date: str
    scope: str

    charges: MoneyBox
    payments: MoneyBox
    balance: MoneyBox
    items: list[InvoiceItem]


# -----------------------------
# PDF FUNCTIONS
# -----------------------------

def clean_filename(text):
    text = re.sub(r"[^\w\-_\. ]", "_", text)
    return text.strip().replace(" ", "_")


def build_invoice_pdf(invoice, filename="material_invoice.pdf"):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    left_margin = 0.6 * inch
    right_margin = width - 0.6 * inch
    usable_width = right_margin - left_margin

    y = height - 0.6 * inch

    # -----------------------------
    # LOGO - TOP LEFT
    # -----------------------------
    logo_path = "company_logo.png"  # put your logo image in the same folder

    try:
        c.drawImage(
            logo_path,
            left_margin,
            y - 55,
            width= 1.6 * inch,
            height= 1.0 * inch,
            preserveAspectRatio=True,
            mask="auto"
        )
    except Exception:
        pass  # if logo is missing, continue without crashing

    # -----------------------------
    # COMPANY INFO - TOP RIGHT
    # -----------------------------
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(right_margin, y, invoice.company_name)
    y -= 14

    c.setFont("Helvetica", 10)
    c.drawRightString(right_margin, y, invoice.company_address)
    y -= 14
    c.drawRightString(right_margin, y, invoice.company_phone)
    y -= 14
    c.drawRightString(right_margin, y, invoice.license_number)

    # -----------------------------
    # TITLE
    # -----------------------------
    y = height - 2.0 * inch
    c.setFont("Helvetica-Bold", 26)
    c.drawString(left_margin, y, invoice.title)


    # -----------------------------
    # SCOPE - BOLD, NO EXTRA GAP
    # -----------------------------
    y -= 20
    c.setFont("Helvetica-Bold", 10)
    c.drawString(left_margin, y, f"Scope of Work: {invoice.scope}")


    # -----------------------------
    # PREPARED FOR / DATE BOX
    # -----------------------------
    y -= 30

    prepared_data = [
        ["PREPARED FOR", "PREPARED DATE"],
        [
            f"{invoice.prepared_for}\n{invoice.client_address}",
            invoice.prepared_date
        ]
    ]

    prepared_table = Table(
        prepared_data,
        colWidths=[usable_width * 0.65, usable_width * 0.35]
    )

    prepared_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("ALIGN", (1, 1), (1, 1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
    ]))

    prepared_table.wrapOn(c, width, height)
    prepared_height = prepared_table._height
    prepared_table.drawOn(c, left_margin, y - prepared_height)

    y -= prepared_height



    # -----------------------------
    # CHARGES / PAYMENTS / BALANCE BOX
    # no big gap after scope
    # -----------------------------
    y -= 25

    summary_data = [
        [invoice.charges.title, invoice.payments.title, invoice.balance.title],
        [invoice.charges.amount, invoice.payments.amount, invoice.balance.amount],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[usable_width / 3, usable_width / 3, usable_width / 3]
    )

    summary_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))

    summary_table.wrapOn(c, width, height)
    summary_height = summary_table._height
    summary_table.drawOn(c, left_margin, y - summary_height)

    y -= summary_height

    # -----------------------------
    # ITEMS TABLE
    # aligned with boxes above
    # -----------------------------
    y -= 25

    item_data = [["ITEM", "DESCRIPTION", "PRICE"]]

    for item in invoice.items:
        item_data.append([
            item.item,
            item.description,
            item.price
        ])

    items_table = Table(
        item_data,
        colWidths=[usable_width * 0.22, usable_width * 0.61, usable_width * 0.17]
    )

    items_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("ALIGN", (2, 1), (2, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    items_table.wrapOn(c, width, height)
    items_height = items_table._height

    if y - items_height < 0.6 * inch:
        c.showPage()
        y = height - 0.6 * inch

    items_table.drawOn(c, left_margin, y - items_height)

    c.save()


# -----------------------------
# GUI FUNCTIONS
# -----------------------------

items = []


def add_item():
    item_name = item_entry.get().strip()
    item_desc = desc_entry.get().strip()
    item_price = price_entry.get().strip()

    if not item_name or not item_price:
        messagebox.showwarning("Missing item", "Item name and price are required.")
        return

    new_item = InvoiceItem(
        item=item_name,
        description=item_desc,
        price=item_price
    )

    items.append(new_item)

    item_list.insert(tk.END, f"{item_name} | {item_desc} | {item_price}")

    item_entry.delete(0, tk.END)
    desc_entry.delete(0, tk.END)
    price_entry.delete(0, tk.END)


def generate_invoice():
    if not prepared_for_entry.get().strip():
        messagebox.showwarning("Missing info", "Prepared For is required.")
        return

    invoice = Invoice(
        title="Material Invoice",

        company_name="D. Dimas General Services",
        company_address="739 Ruth Dr. Pleasant Hill, CA 94523",
        company_phone="(925) 272-5002",
        license_number="Lic. 5016053",

        prepared_for=prepared_for_entry.get().strip(),
        client_address=client_address_entry.get().strip(),
        prepared_date=prepared_date_entry.get().strip(),
        scope=scope_entry.get().strip(),

        charges=MoneyBox(
            title="Total Charges",
            amount=total_charges_entry.get().strip()
        ),

        payments=MoneyBox(
            title="Total Payments",
            amount=total_payments_entry.get().strip()
        ),

        balance=MoneyBox(
            title="Balance Due",
            amount=balance_due_entry.get().strip()
        ),

        items=items
    )

    safe_client = clean_filename(invoice.prepared_for)
    safe_date = clean_filename(invoice.prepared_date)

    pdf_file = f"material_invoice_{safe_client}_{safe_date}.pdf"

    build_invoice_pdf(invoice, pdf_file)

    messagebox.showinfo("Success", f"PDF created:\n{pdf_file}")


# -----------------------------
# GUI LAYOUT
# -----------------------------

root = tk.Tk()
root.title("Material Invoice Form")
root.geometry("700x850")
root.resizable(True, True)

tk.Label(root, text="Material Invoice Form", font=("Arial", 18, "bold")).pack(pady=10)

tk.Label(root, text="Prepared For").pack()
prepared_for_entry = tk.Entry(root, width=70)
prepared_for_entry.pack()

tk.Label(root, text="Client Address").pack()
client_address_entry = tk.Entry(root, width=70)
client_address_entry.pack()

tk.Label(root, text="Prepared Date").pack()
prepared_date_entry = tk.Entry(root, width=70)
prepared_date_entry.pack()

tk.Label(root, text="Scope").pack()
scope_entry = tk.Entry(root, width=70)
scope_entry.pack()

tk.Label(root, text="Total Charges").pack()
total_charges_entry = tk.Entry(root, width=70)
total_charges_entry.pack()

tk.Label(root, text="Total Payments").pack()
total_payments_entry = tk.Entry(root, width=70)
total_payments_entry.pack()

tk.Label(root, text="Balance Due").pack()
balance_due_entry = tk.Entry(root, width=70)
balance_due_entry.pack()

tk.Label(root, text="Add Material Item", font=("Arial", 14, "bold")).pack(pady=15)

tk.Label(root, text="Item Name").pack()
item_entry = tk.Entry(root, width=70)
item_entry.pack()

tk.Label(root, text="Description").pack()
desc_entry = tk.Entry(root, width=70)
desc_entry.pack()

tk.Label(root, text="Price").pack()
price_entry = tk.Entry(root, width=70)
price_entry.pack()

tk.Button(root, text="Add Item to Invoice", command=add_item).pack(pady=10)

tk.Label(root, text="Items Added").pack()
item_list = tk.Listbox(root, width=95, height=10)
item_list.pack()

tk.Button(
    root,
    text="Done - Generate PDF",
    command=generate_invoice,
    bg="lightgreen",
    width=30
).pack(pady=20)

root.mainloop()