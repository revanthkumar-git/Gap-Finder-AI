from typing import List
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Report
from app.auth import get_current_user, log_audit_event
from app.schemas import ReportResponse

router = APIRouter(prefix="/reports", tags=["Reporting"])

class ReportGenerateRequest(BaseModel):
    title: str
    report_type: str
    period: str
    include_benchmarks: bool = True
    include_tax_analysis: bool = True

@router.get("", response_model=List[ReportResponse])
def get_reports(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Report).order_by(Report.generated_date.desc()).all()

@router.post("/generate", response_model=ReportResponse)
def generate_report(req: ReportGenerateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rep = Report(
        title=req.title,
        report_type=req.report_type,
        period=req.period,
        file_format="PDF",
        status="Ready",
        summary=f"Automated {req.report_type} generated for period {req.period}. Benchmarks included: {req.include_benchmarks}.",
        generated_date=datetime.utcnow()
    )
    db.add(rep)
    db.commit()
    db.refresh(rep)
    log_audit_event(db, action="GENERATE_REPORT", user=current_user, entity_type="Report", entity_id=str(rep.id), details=f"Generated {rep.title}")
    return rep
