from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, RetirementPlan, Participant, InvestmentOption
from app.auth import get_current_user, log_audit_event
from app.schemas import RetirementPlanOverview

router = APIRouter(prefix="/retirement", tags=["Retirement Plans & Participants"])

@router.get("/plan-overview", response_model=RetirementPlanOverview)
def get_retirement_plan_overview(db: Session = Depends(get_db)):
    plan = db.query(RetirementPlan).first()
    return RetirementPlanOverview(
        id=plan.id,
        plan_name=plan.plan_name,
        sponsor_name=plan.sponsor_name,
        plan_number=plan.plan_number,
        total_plan_assets=plan.total_plan_assets,
        active_participants=plan.active_participants,
        participation_rate=plan.participation_rate,
        avg_contribution_rate=plan.avg_contribution_rate,
        employer_match_rate=plan.employer_match_rate,
        plan_health_score=plan.plan_health_score,
        compliance_status=plan.compliance_status
    )

@router.get("/fund-lineup")
def get_fund_lineup(db: Session = Depends(get_db)):
    plan = db.query(RetirementPlan).first()
    funds = db.query(InvestmentOption).filter(InvestmentOption.retirement_plan_id == plan.id).all()
    return [
        {
            "id": f.id,
            "fund_name": f.fund_name,
            "ticker": f.ticker,
            "asset_category": f.asset_category,
            "expense_ratio": f.expense_ratio,
            "one_year_return": f.one_year_return,
            "five_year_return": f.five_year_return,
            "morningstar_rating": f.morningstar_rating,
            "total_assets_allocated": f.total_assets_allocated
        } for f in funds
    ]

@router.get("/sponsor/compliance")
def get_sponsor_compliance():
    return {
        "status": "In Full Compliance",
        "last_audit_date": "July 15, 2026",
        "auditor": "Deloitte Fiduciary Assurance LLP",
        "form_5500_filing": {"status": "Filed Electronically", "confirmation_no": "EBSA-2026-948102"},
        "tests": [
            {"test_name": "Actual Deferral Percentage (ADP)", "threshold": "<= 2.0% spread", "actual": "1.14% spread", "result": "PASS"},
            {"test_name": "Actual Contribution Percentage (ACP)", "threshold": "<= 2.0% spread", "actual": "0.92% spread", "result": "PASS"},
            {"test_name": "Top-Heavy Determination Test", "threshold": "< 60% of total assets", "actual": "38.2%", "result": "PASS"},
            {"test_name": "IRC Section 415 Limit Monitoring", "threshold": "$69,000 max annual addition", "actual": "0 exceptions", "result": "PASS"}
        ]
    }

@router.get("/sponsor/analytics")
def get_sponsor_analytics():
    return {
        "participation_trend": [
            {"year": "2022", "rate": 78.2, "assets": 28.5},
            {"year": "2023", "rate": 81.5, "assets": 32.1},
            {"year": "2024", "rate": 84.0, "assets": 36.4},
            {"year": "2025", "rate": 86.8, "assets": 39.8},
            {"year": "2026", "rate": 88.4, "assets": 42.5},
        ],
        "contribution_distribution": [
            {"bracket": "< 3%", "participants": 74},
            {"bracket": "3% - 6%", "participants": 340},
            {"bracket": "6% - 9%", "participants": 560},
            {"bracket": "10%+", "participants": 266},
        ]
    }

# Participant Portal Endpoints
@router.get("/participant/me")
def get_participant_portal_data(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    participant = db.query(Participant).filter(Participant.user_id == current_user.id).first()
    if not participant:
        participant = db.query(Participant).first()

    return {
        "user_name": current_user.full_name if current_user else "Sophia Chen",
        "current_balance": participant.current_balance,
        "contribution_percent": participant.contribution_percent,
        "employer_match_percent": participant.employer_match_percent,
        "ytd_return_percent": participant.ytd_return_percent,
        "current_age": participant.current_age,
        "target_retirement_age": participant.retirement_age_target,
        "projected_monthly_income": participant.projected_monthly_income,
        "readiness_score": participant.readiness_score,
        "vested_percent": participant.vested_percent,
        "current_allocation": [
            {"fund": "Vanguard 500 Index (VFIAX)", "percentage": 50},
            {"fund": "Fidelity Contrafund (FCNTX)", "percentage": 25},
            {"fund": "PIMCO Total Return (PTTRX)", "percentage": 15},
            {"fund": "American Funds Europacific (RERGX)", "percentage": 10}
        ],
        "beneficiaries": [
            {"name": "David Chen", "relationship": "Spouse", "share": 100}
        ]
    }

@router.post("/participant/update-contribution")
def update_contribution(contribution_percent: float, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    participant = db.query(Participant).filter(Participant.user_id == current_user.id).first()
    if participant:
        participant.contribution_percent = contribution_percent
        # Recalculate projected monthly income
        base_income = 6850.0
        diff = (contribution_percent - 9.0) * 240.0
        participant.projected_monthly_income = max(3500.0, base_income + diff)
        participant.readiness_score = min(99, max(60, int(84 + (contribution_percent - 9.0) * 2.5)))
        db.commit()
    
    log_audit_event(db, action="UPDATE_CONTRIBUTION_RATE", user=current_user, details=f"Changed deferral rate to {contribution_percent}%")
    return {"message": "Contribution rate updated successfully", "new_rate": contribution_percent}

@router.get("/education/modules")
def get_education_modules():
    return [
        {
            "id": 1,
            "title": "The Power of Compound Growth & Early Dollar Matching",
            "category": "Retirement Basics",
            "read_time": "4 min read",
            "summary": "Understand how capturing 100% of your employer 4.5% match represents an immediate risk-free 100% ROI on your capital.",
            "content": "When you contribute to your 401(k), your employer matches dollar-for-dollar up to 4.5% of your annual salary. For a $120,000 salary, contributing 4.5% means $5,400 from you and an additional $5,400 from your employer—doubling your money before investment returns even compound."
        },
        {
            "id": 2,
            "title": "Asset Allocation: Stocks, Bonds, and Market Cycles",
            "category": "Investing Fundamentals",
            "read_time": "6 min read",
            "summary": "How target-date diversification shields late-career balances while maximizing early compounding velocity.",
            "content": "A balanced portfolio automatically reallocates between growth equities and stabilizing fixed income. As you approach your retirement horizon, the glidepath shifts defensively to lock in accumulated gains."
        },
        {
            "id": 3,
            "title": "Navigating Market Volatility & The Dollar-Cost Averaging Advantage",
            "category": "Market Psychology",
            "read_time": "5 min read",
            "summary": "Why regular payroll contributions turn market pullbacks into high-yield buying opportunities.",
            "content": "By investing a fixed percentage every pay cycle, you acquire more fund units when valuations drop and fewer when valuations surge, systematically driving down your average cost per share over multi-year horizons."
        },
        {
            "id": 4,
            "title": "Understanding Pre-Tax Traditional vs. Roth 401(k)",
            "category": "Tax Efficiency",
            "read_time": "5 min read",
            "summary": "Evaluating whether current tax deductions or future tax-free retirement distributions serve you best.",
            "content": "Traditional 401(k) contributions lower your adjusted gross income today, while Roth 401(k) contributions are made after-tax but grow and distribute 100% tax-free during retirement."
        },
        {
            "id": 5,
            "title": "Social Security Optimization & Replacement Ratios",
            "category": "Retirement Strategy",
            "read_time": "7 min read",
            "summary": "Bridging the gap between age 62 and 70 to maximize guaranteed inflation-indexed benefits by up to 77%.",
            "content": "Delaying Social Security claims beyond Full Retirement Age (FRA) accrues Delayed Retirement Credits of 8% per year until age 70, providing a powerful hedge against longevity."
        },
        {
            "id": 6,
            "title": "Catch-Up Contributions for Ages 50+",
            "category": "Retirement Strategy",
            "read_time": "3 min read",
            "summary": "Utilizing SECURE 2.0 catch-up limits to accelerate retirement savings during peak earnings years.",
            "content": "Participants aged 50 and older can contribute an additional $7,500 catch-up in 2026, allowing significant acceleration of tax-sheltered capital prior to retirement transition."
        },
        {
            "id": 7,
            "title": "Healthcare Costs & Health Savings Accounts (HSA) in Retirement",
            "category": "Healthcare Planning",
            "read_time": "6 min read",
            "summary": "Using triple-tax-advantaged HSAs as stealth retirement investment vehicles for medical expenses.",
            "content": "HSA contributions are tax-deductible, grow tax-free, and withdraw tax-free for qualified medical expenses, effectively acting as an unmatched supplementary healthcare retirement fund."
        }
    ]
