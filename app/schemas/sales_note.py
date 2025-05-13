# app/schemas/sales_note.py
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class SalesNoteItemBase(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
    unit_price: float = Field(gt=0)
    subtotal: float = Field(gt=0)

class SalesNoteItemCreate(SalesNoteItemBase):
    pass

class SalesNoteItemResponse(SalesNoteItemBase):
    id: int
    sales_note_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class SalesNoteBase(BaseModel):
    customer_id: int
    total_amount: float = Field(gt=0)
    tax_amount: float = Field(ge=0)
    status: str = "draft"

class SalesNoteCreate(SalesNoteBase):
    items: List[SalesNoteItemCreate]

class SalesNoteUpdate(BaseModel):
    total_amount: Optional[float] = Field(default=None, gt=0)
    tax_amount: Optional[float] = Field(default=None, ge=0)
    status: Optional[str] = None

class SalesNoteResponse(SalesNoteBase):
    id: int
    note_number: str
    note_date: datetime
    pdf_path: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: List[SalesNoteItemResponse] = []

    class Config:
        from_attributes = True
