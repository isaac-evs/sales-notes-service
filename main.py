from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.database import engine
from app.models.sales_note import SalesNote, SalesNoteItem
from app.views import sales_note as sales_note_views

# Create database tables
SalesNote.__table__.create(bind=engine, checkfirst=True)
SalesNoteItem.__table__.create(bind=engine, checkfirst=True)

# Create storage directory for PDFs
pdf_dir = os.getenv("PDF_STORAGE_PATH", "/tmp/sales_notes_pdfs")
os.makedirs(pdf_dir, exist_ok=True)

app = FastAPI(title="Sales Notes Service")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sales_note_views.router, prefix="/api/sales-notes", tags=["sales-notes"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Sales Notes Service API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
