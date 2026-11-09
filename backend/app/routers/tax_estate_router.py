from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Client, TaxOpportunity, EstatePlan, Beneficiary, Trust, TaxLot
from app.auth import get_current_user, log_audit_event
from app.schemas import TaxOpportunityResponse, BeneficiaryResponse, TrustResponse

router = APIRouter(prefix="/tax-estate", tags=["Tax, Estate & Philanthropy"])

@router.get("/tax-summary")
def get_tax_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.user_id == current_user.id).first()
    if not client:
        client = db.query(Client).first()

    return {
        "tax_year": 2026,
        "estimated_federal_tax": 86450.0,
        "estimated_state_tax": 16200.0,
        "taxable_interest_div": 34800.0,
        "realized_short_term_gains": 14200.0,
        "realized_long_term_gains": 52800.0,
        "harvestable_unrealized_losses": 18400.0,
        "potential_tax_savings": 6440.0,
        "rmd_status": {
            "is_applicable": False,
            "years_until_rmd": 12,
            "estimated_first_rmd": 74500.0
        },
        "roth_conversion_opportunity": {
            "recommended_amount": 45000.0,
            "current_effective_rate": "24.8%",
            "projected_future_rate": "32.0%",
            "net_lifetime_savings": 14200.0
        },
        "tax_deadlines": [
            {"date": "Sep 15, 2026", "item": "Q3 Estimated Federal & State Tax Payment", "status": "Upcoming"},
            {"date": "Oct 15, 2026", "item": "Form 1040 Extended Filing Deadline", "status": "Upcoming"},
            {"date": "Dec 31, 2026", "item": "Annual Tax-Loss Harvesting & Charitable Gifting Deadline", "status": "Scheduled"}
        ]
    }

@router.get("/tax-opportunities", response_model=List[TaxOpportunityResponse])
def get_tax_opportunities(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.user_id == current_user.id).first()
    if not client:
        client = db.query(Client).first()
    
    return db.query(TaxOpportunity).filter(TaxOpportunity.client_id == client.id).all()

@router.post("/execute-harvest")
def execute_tax_loss_harvest(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    log_audit_event(db, action="EXECUTE_TAX_HARVEST", user=current_user, details="Harvested $18,400 in tax losses across BND and IWM")
    return {
        "status": "Success",
        "message": "Harvest trade execution orders staged with custodian. Total capital loss realized: $18,400.",
        "estimated_tax_savings": "$6,440.00",
        "replacement_assets": "Swapped Vanguard Total Bond (BND) -> iShares Core US Aggregate (AGG) to maintain duration without wash-sale violation."
    }

@router.get("/estate-summary")
def get_estate_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.user_id == current_user.id).first()
    if not client:
        client = db.query(Client).first()

    estate = db.query(EstatePlan).filter(EstatePlan.client_id == client.id).first()
    beneficiaries = db.query(Beneficiary).filter(Beneficiary.estate_plan_id == estate.id).all() if estate else []
    trusts = db.query(Trust).filter(Trust.estate_plan_id == estate.id).all() if estate else []

    return {
        "estimated_gross_estate": estate.estimated_gross_estate if estate else 4850000.0,
        "federal_estate_exemption": 13610000.0,
        "taxable_estate_exposure": "$0 (Below Exemption Threshold)",
        "has_will": estate.has_will if estate else True,
        "has_healthcare_directive": estate.has_healthcare_directive if estate else True,
        "has_poa": estate.has_poa if estate else True,
        "last_reviewed": estate.last_reviewed if estate else "2026-07-20",
        "beneficiaries": [
            {
                "id": b.id,
                "full_name": b.full_name,
                "relationship_type": b.relationship_type,
                "allocation_percentage": b.allocation_percentage,
                "is_primary": b.is_primary
            } for b in beneficiaries
        ],
        "trusts": [
            {
                "id": t.id,
                "trust_name": t.trust_name,
                "trust_type": t.trust_type,
                "trustee_name": t.trustee_name,
                "assets_funded": t.assets_funded,
                "status": t.status
            } for t in trusts
        ]
    }

@router.get("/philanthropy")
def get_philanthropy_dashboard():
    return {
        "donor_advised_fund": {
            "fund_name": "The Mercer Family Giving Fund (DAF)",
            "custodian": "Nexqile Charitable Gift Trust",
            "current_balance": 385000.0,
            "ytd_contributions": 50000.0,
            "ytd_grants_distributed": 28000.0,
            "active_grants": [
                {"recipient": "Clean Oceans International Initiative", "amount": 10000.0, "status": "Disbursed", "date": "Jun 2026"},
                {"recipient": "St. Jude Children's Research Hospital", "amount": 10000.0, "status": "Disbursed", "date": "Apr 2026"},
                {"recipient": "Metropolitan Youth Arts Foundation", "amount": 8000.0, "status": "Disbursed", "date": "Feb 2026"}
            ]
        },
        "gifting_allowance_2026": {
            "annual_gift_exclusion_per_donee": 18000.0,
            "gifts_made_ytd": 36000.0,
            "remaining_annual_allowance": 72000.0
        }
    }
