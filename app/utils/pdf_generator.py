# app/utils/pdf_generator.py
import os
from datetime import datetime
from fpdf import FPDF
from sqlalchemy.orm import Session
import json

from app.models.sales_note import SalesNote, SalesNoteItem

class PDFGenerator:
    @staticmethod
    def generate_sales_note_pdf(db: Session, sales_note_id: int):
        """
        Generates a PDF for a sales note and saves it to the configured storage path.
        Returns the path to the generated PDF.
        """
        # Get the sales note and its items
        sales_note = db.query(SalesNote).filter(SalesNote.id == sales_note_id).first()
        if not sales_note:
            raise ValueError(f"Sales note with ID {sales_note_id} not found")

        items = db.query(SalesNoteItem).filter(SalesNoteItem.sales_note_id == sales_note_id).all()

        # Get customer information
        customer = db.execute(f"SELECT * FROM customers WHERE id = {sales_note.customer_id}").fetchone()

        # Get product information for each item
        products = {}
        for item in items:
            product = db.execute(f"SELECT * FROM products WHERE id = {item.product_id}").fetchone()
            products[item.product_id] = product

        # Create PDF
        pdf = FPDF()
        pdf.add_page()

        # Set up font
        pdf.set_font("Arial", "B", 16)

        # Title
        pdf.cell(190, 10, "SALES NOTE", 0, 1, "C")
        pdf.cell(190, 10, f"#{sales_note.note_number}", 0, 1, "C")
        pdf.ln(10)

        # Date and Status
        pdf.set_font("Arial", "", 10)
        pdf.cell(95, 10, f"Date: {sales_note.note_date.strftime('%Y-%m-%d')}", 0, 0)
        pdf.cell(95, 10, f"Status: {sales_note.status.upper()}", 0, 1, "R")
        pdf.ln(5)

        # Customer Information
        pdf.set_font("Arial", "B", 12)
        pdf.cell(190, 10, "Customer Information:", 0, 1)
        pdf.set_font("Arial", "", 10)
        pdf.cell(190, 10, f"Name: {customer['name']}", 0, 1)
        pdf.cell(190, 10, f"Email: {customer['email']}", 0, 1)
        pdf.cell(190, 10, f"Phone: {customer['phone'] if customer['phone'] else 'N/A'}", 0, 1)
        pdf.ln(10)

        # Items Table
        pdf.set_font("Arial", "B", 12)
        pdf.cell(190, 10, "Items:", 0, 1)

        # Table Header
        pdf.set_fill_color(200, 200, 200)
        pdf.cell(80, 10, "Product", 1, 0, "C", True)
        pdf.cell(30, 10, "Quantity", 1, 0, "C", True)
        pdf.cell(40, 10, "Unit Price", 1, 0, "C", True)
        pdf.cell(40, 10, "Subtotal", 1, 1, "C", True)

        # Table Content
        pdf.set_font("Arial", "", 10)
        for item in items:
            product = products[item.product_id]
            pdf.cell(80, 10, product['name'], 1, 0)
            pdf.cell(30, 10, str(item.quantity), 1, 0, "C")
            pdf.cell(40, 10, f"${item.unit_price:.2f}", 1, 0, "R")
            pdf.cell(40, 10, f"${item.subtotal:.2f}", 1, 1, "R")

        # Totals
        pdf.ln(5)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(150, 10, "Subtotal:", 0, 0, "R")
        pdf.cell(40, 10, f"${sales_note.total_amount - sales_note.tax_amount:.2f}", 0, 1, "R")
        pdf.cell(150, 10, "Tax:", 0, 0, "R")
        pdf.cell(40, 10, f"${sales_note.tax_amount:.2f}", 0, 1, "R")
        pdf.set_font("Arial", "B", 12)
        pdf.cell(150, 10, "Total:", 0, 0, "R")
        pdf.cell(40, 10, f"${sales_note.total_amount:.2f}", 0, 1, "R")

        # Create directory if it doesn't exist
        pdf_dir = os.getenv("PDF_STORAGE_PATH", "/tmp/sales_notes_pdfs")
        os.makedirs(pdf_dir, exist_ok=True)

        # Save PDF
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        pdf_filename = f"sales_note_{sales_note.id}_{timestamp}.pdf"
        pdf_path = os.path.join(pdf_dir, pdf_filename)
        pdf.output(pdf_path)

        # Update sales note with PDF path
        sales_note.pdf_path = pdf_path
        db.commit()

        return pdf_path
