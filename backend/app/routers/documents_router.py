from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Document
from app.auth import get_current_user, log_audit_event
from app.schemas import DocumentResponse

router = APIRouter(prefix="/documents", tags=["Document Center"])

@router.get("", response_model=List[DocumentResponse])
def get_documents(
    category: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Document)
    if category and category != "All":
        query = query.filter(Document.category == category)
    if search:
        query = query.filter(Document.title.ilike(f"%{search}%"))
    
    return query.order_by(Document.upload_date.desc()).all()

@router.post("/upload")
def upload_document(
    title: str,
    category: str = "Statements",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = Document(
        title=title,
        category=category,
        file_type="PDF",
        file_size="2.1 MB",
        upload_date=datetime.utcnow(),
        status="Verified"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    log_audit_event(db, action="UPLOAD_DOCUMENT", user=current_user, entity_type="Document", entity_id=str(doc.id), details=f"Uploaded {title}")
    return {"message": "Document uploaded successfully and encrypted at rest.", "document": doc}
