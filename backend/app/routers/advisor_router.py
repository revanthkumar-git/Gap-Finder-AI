from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Advisor, Client, Household, Account, Holding, Goal, Task, Meeting
from app.auth import get_current_user, log_audit_event
from app.schemas import ClientSummary

router = APIRouter(prefix="/advisor", tags=["Advisor Workstation"])

@router.get("/metrics")
def get_advisor_metrics(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    advisor = db.query(Advisor).first()
    clients_count = db.query(Client).count()
    open_tasks = db.query(Task).filter(Task.status != "Completed").count()
    meetings_count = db.query(Meeting).count()

    return {
        "total_aum": 148500000.0,
        "active_clients": clients_count,
        "households_managed": 34,
        "trailing_12m_revenue": 1188000.0,  # 80 bps blended fee
        "open_tasks": open_tasks,
        "meetings_scheduled": meetings_count,
        "pending_rebalance_approvals": 3,
        "avg_client_tenure_years": 6.8
    }

@router.get("/clients", response_model=List[ClientSummary])
def get_clients(
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    clients = db.query(Client).all()
    res = []
    for c in clients:
        u = db.query(User).filter(User.id == c.user_id).first()
        hh = db.query(Household).filter(Household.id == c.household_id).first() if c.household_id else None
        tasks_count = db.query(Task).filter(Task.user_id == u.id, Task.status != "Completed").count() if u else 0

        name = u.full_name if u else "Valued Client"
        email = u.email if u else "client@example.com"
        hh_name = hh.name if hh else "Independent Account"

        if search and search.lower() not in name.lower() and search.lower() not in email.lower():
            continue
        if status_filter and status_filter != "All" and c.status != status_filter:
            continue

        res.append(ClientSummary(
            id=c.id,
            name=name,
            email=email,
            household_name=hh_name,
            aum=c.net_worth,
            risk_tolerance=c.risk_tolerance,
            ytd_return=c.ytd_return,
            status=c.status,
            last_contact="Sep 02, 2026",
            open_tasks=tasks_count
        ))
    return res

@router.get("/clients/{client_id}")
def get_client_profile(client_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    user = db.query(User).filter(User.id == client.user_id).first()
    accounts = db.query(Account).filter(Account.client_id == client.id).all()
    goals = db.query(Goal).filter(Goal.client_id == client.id).all()
    tasks = db.query(Task).filter(Task.user_id == user.id).all() if user else []

    accounts_data = []
    for a in accounts:
        h_list = db.query(Holding).filter(Holding.account_id == a.id).all()
        accounts_data.append({
            "id": a.id,
            "name": a.account_name,
            "type": a.account_type,
            "account_number": a.account_number,
            "balance": a.balance,
            "cash": a.cash_available,
            "holdings": [
                {
                    "symbol": h.symbol,
                    "name": h.security_name,
                    "market_value": h.market_value,
                    "gain_loss": h.unrealized_gain,
                    "allocation_percent": h.allocation_percent
                } for h in h_list
            ]
        })

    return {
        "id": client.id,
        "name": user.full_name if user else "Alexander Mercer",
        "email": user.email if user else "client@nexqile.demo",
        "net_worth": client.net_worth,
        "invested_assets": client.invested_assets,
        "cash_balance": client.cash_balance,
        "retirement_assets": client.retirement_assets,
        "risk_tolerance": client.risk_tolerance,
        "tax_bracket": client.tax_bracket,
        "ytd_return": client.ytd_return,
        "status": client.status,
        "accounts": accounts_data,
        "goals": [
            {
                "id": g.id,
                "title": g.title,
                "target_amount": g.target_amount,
                "current_amount": g.current_amount,
                "probability": g.probability,
                "status": g.status
            } for g in goals
        ],
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "priority": t.priority,
                "status": t.status,
                "due_date": t.due_date
            } for t in tasks
        ]
    }

@router.get("/rebalancing/drift")
def get_rebalancing_drift(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {
        "portfolio_target_model": "Global Multi-Asset Growth Model 70/20/10",
        "total_portfolio_value": 2840500.0,
        "overall_drift_status": "Rebalance Recommended (Drift > 3.0%)",
        "asset_classes": [
            {"name": "Large-Cap Equities", "current_pct": 54.2, "target_pct": 50.0, "drift_pct": 4.2, "action": "Trim", "proposed_trade": "-$119,300"},
            {"name": "Fixed Income / Muni", "current_pct": 17.1, "target_pct": 20.0, "drift_pct": -2.9, "action": "Add", "proposed_trade": "+$82,375"},
            {"name": "Real Estate / REITs", "current_pct": 12.0, "target_pct": 10.0, "drift_pct": 2.0, "action": "Trim", "proposed_pct": "-$56,810"},
            {"name": "Alternative Assets", "current_pct": 10.2, "target_pct": 15.0, "drift_pct": -4.8, "action": "Add", "proposed_trade": "+$136,344"},
            {"name": "Cash & Liquidity", "current_pct": 6.5, "target_pct": 5.0, "drift_pct": 1.5, "action": "Hold", "proposed_trade": "$0"}
        ],
        "tax_aware_impact": {
            "estimated_capital_gain_generated": 12400.0,
            "tax_loss_offset_available": 18400.0,
            "net_taxable_realization": "$0.00 (Fully offset with harvested losses!)",
            "recommended_execution_speed": "Batch Overnight Settlement"
        }
    }

@router.post("/rebalancing/execute")
def execute_rebalance(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    log_audit_event(db, action="EXECUTE_REBALANCE", user=current_user, details="Advisor initiated tax-aware rebalancing for client portfolio")
    return {
        "status": "Submitted",
        "order_ids": ["ORD-2026-8910", "ORD-2026-8911", "ORD-2026-8912"],
        "message": "Tax-aware rebalance trades successfully routed to Nexqile Custody & Clearing OMS.",
        "settlement_date": "T+1 (Tomorrow 4:00 PM EST)"
    }
