# app/models/sales_note.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.database import Base

class SalesNote(Base):
    __tablename__ = "sales_notes"

    id = Column(Integer, primary_key=True, index=True)
    note_number = Column(String, unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    total_amount = Column(Float, nullable=False)
    tax_amount = Column(Float, nullable=False)
    note_date = Column(DateTime, default=func.now(), nullable=False)
    status = Column(String, nullable=False, default="draft")  # draft, issued, paid, canceled
    pdf_path = Column(String)  # Path to the generated PDF
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class SalesNoteItem(Base):
    __tablename__ = "sales_note_items"

    id = Column(Integer, primary_key=True, index=True)
    sales_note_id = Column(Integer, ForeignKey("sales_notes.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
