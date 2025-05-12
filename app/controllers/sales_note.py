# app/controllers/sales_note.py
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
import uuid

from app.models.sales_note import SalesNote, SalesNoteItem
from app.schemas.sales_note import SalesNoteCreate, SalesNoteUpdate
from app.utils.pdf_generator import PDFGenerator

class SalesNoteController:
    @staticmethod
    def get_sales_notes(db: Session, skip: int = 0, limit: int = 100, customer_id: int = None):
        query = db.query(SalesNote)
        if customer_id:
            query = query.filter(SalesNote.customer_id == customer_id)
        return query.order_by(SalesNote.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_sales_note(db: Session, sales_note_id: int):
        sales_note = db.query(SalesNote).filter(SalesNote.id == sales_note_id).first()
        if sales_note is None:
            raise HTTPException(status_code=404, detail="Sales note not found")
        return sales_note

    @staticmethod
    def get_sales_note_by_number(db: Session, note_number: str):
        return db.query(SalesNote).filter(SalesNote.note_number == note_number).first()

    @staticmethod
    def create_sales_note(db: Session, sales_note: SalesNoteCreate):
        # Verify customer exists
        customer = db.execute(f"SELECT id FROM customers WHERE id = {sales_note.customer_id}").fetchone()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Generate a unique note number
        current_year = datetime.now().year
        note_number = f"SN-{current_year}-{str(uuid.uuid4())[:8].upper()}"

        # Create sales note
        db_sales_note = SalesNote(
            note_number=note_number,
            customer_id=sales_note.customer_id,
            total_amount=sales_note.total_amount,
            tax_amount=sales_note.tax_amount,
            status=sales_note.status,
            note_date=datetime.now()
        )
        db.add(db_sales_note)
        db.flush()

        # Create sales note items
        for item in sales_note.items:
            # Verify product exists
            product = db.execute(f"SELECT id, price FROM products WHERE id = {item.product_id}").fetchone()
            if not product:
                db.rollback()
                raise HTTPException(status_code=404, detail=f"Product with ID {item.product_id} not found")

            # Create item
            db_item = SalesNoteItem(
                sales_note_id=db_sales_note.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                subtotal=item.subtotal
            )
            db.add(db_item)

        db.commit()
        db.refresh(db_sales_note)
        return db_sales_note

    @staticmethod
    def update_sales_note(db: Session, sales_note_id: int, sales_note: SalesNoteUpdate):
        db_sales_note = SalesNoteController.get_sales_note(db, sales_note_id)

        # Check if update is allowed based on status
        if db_sales_note.status in ["paid", "canceled"]:
            raise HTTPException(status_code=400, detail="Cannot update a paid or canceled sales note")

        # Update sales note data
        update_data = sales_note.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_sales_note, key, value)

        db.commit()
        db.refresh(db_sales_note)
        return db_sales_note

    @staticmethod
    def delete_sales_note(db: Session, sales_note_id: int):
        db_sales_note = SalesNoteController.get_sales_note(db, sales_note_id)

        # Check if delete is allowed based on status
        if db_sales_note.status in ["paid"]:
            raise HTTPException(status_code=400, detail="Cannot delete a paid sales note")

        # Delete sales note items first
        db.execute(f"DELETE FROM sales_note_items WHERE sales_note_id = {sales_note_id}")

        # Delete sales note
        db.delete(db_sales_note)
        db.commit()
        return {"message": "Sales note deleted successfully"}

    @staticmethod
    def get_sales_note_items(db: Session, sales_note_id: int):
        # Verify sales note exists
        SalesNoteController.get_sales_note(db, sales_note_id)

        # Get items
        items = db.query(SalesNoteItem).filter(SalesNoteItem.sales_note_id == sales_note_id).all()
        return items

    @staticmethod
    def generate_pdf(db: Session, sales_note_id: int):
        # Verify sales note exists
        sales_note = SalesNoteController.get_sales_note(db, sales_note_id)

        # Generate PDF
        pdf_path = PDFGenerator.generate_sales_note_pdf(db, sales_note_id)

        # Update sales note with PDF path
        sales_note.pdf_path = pdf_path
        db.commit()

        return {"pdf_path": pdf_path}

    @staticmethod
    def change_status(db: Session, sales_note_id: int, status: str):
        valid_statuses = ["draft", "issued", "paid", "canceled"]
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

        db_sales_note = SalesNoteController.get_sales_note(db, sales_note_id)

        # Handle status transitions
        if db_sales_note.status == "paid" and status != "paid":
            raise HTTPException(status_code=400, detail="Cannot change status of a paid sales note")

        if db_sales_note.status == "canceled" and status != "canceled":
            raise HTTPException(status_code=400, detail="Cannot change status of a canceled sales note")

        # Update status
        db_sales_note.status = status
        db.commit()
        db.refresh(db_sales_note)

        return db_sales_note
