# app/views/sales_note.py
from fastapi import APIRouter, Depends, Query, Path, Body, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi.responses import FileResponse
import os

from app.schemas.sales_note import SalesNoteCreate, SalesNoteUpdate, SalesNoteResponse
from app.controllers.sales_note import SalesNoteController
from app.database import get_db

router = APIRouter()

@router.get("/", response_model=List[SalesNoteResponse])
def read_sales_notes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    customer_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Get all sales notes with pagination and filtering"""
    return SalesNoteController.get_sales_notes(db, skip=skip, limit=limit, customer_id=customer_id)

@router.post("/", response_model=SalesNoteResponse, status_code=201)
def create_sales_note(
    sales_note: SalesNoteCreate,
    db: Session = Depends(get_db)
):
    """Create a new sales note"""
    return SalesNoteController.create_sales_note(db, sales_note)

@router.get("/{sales_note_id}", response_model=SalesNoteResponse)
def read_sales_note(
    sales_note_id: int = Path(..., gt=0),
    db: Session = Depends(get_db)
):
    """Get a specific sales note by ID"""
    return SalesNoteController.get_sales_note(db, sales_note_id)

@router.put("/{sales_note_id}", response_model=SalesNoteResponse)
def update_sales_note(
    sales_note_id: int = Path(..., gt=0),
    sales_note: SalesNoteUpdate = Body(...),
    db: Session = Depends(get_db)
):
    """Update a sales note"""
    return SalesNoteController.update_sales_note(db, sales_note_id, sales_note)

@router.delete("/{sales_note_id}")
def delete_sales_note(
    sales_note_id: int = Path(..., gt=0),
    db: Session = Depends(get_db)
):
    """Delete a sales note"""
    return SalesNoteController.delete_sales_note(db, sales_note_id)

@router.post("/{sales_note_id}/generate-pdf")
def generate_pdf(
    sales_note_id: int = Path(..., gt=0),
    db: Session = Depends(get_db)
):
    """Generate PDF for a sales note"""
    return SalesNoteController.generate_pdf(db, sales_note_id)

@router.get("/{sales_note_id}/pdf")
def get_pdf(
    sales_note_id: int = Path(..., gt=0),
    db: Session = Depends(get_db)
):
    """Get the PDF file for a sales note"""
    sales_note = SalesNoteController.get_sales_note(db, sales_note_id)

    if not sales_note.pdf_path or not os.path.exists(sales_note.pdf_path):
        raise HTTPException(status_code=404, detail="PDF not found. Generate it first.")

    return FileResponse(sales_note.pdf_path, media_type="application/pdf", filename=f"sales_note_{sales_note_id}.pdf")

@router.post("/{sales_note_id}/status")
def change_status(
    sales_note_id: int = Path(..., gt=0),
    status: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """Change the status of a sales note"""
    return SalesNoteController.change_status(db, sales_note_id, status)
