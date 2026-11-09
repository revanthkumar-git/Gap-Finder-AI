from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Client, Account, Holding, Goal
from app.auth import get_current_user, log_audit_event
from app.schemas import AccountResponse, HoldingResponse, GoalResponse, GoalCreate, GoalUpdate

router = APIRouter(prefix="/wealth", tags=["Wealth Management"])

@router.get("/accounts", response_model=List[AccountResponse])
def get_accounts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.user_id == current_user.id).first()
    if not client:
        client = db.query(Client).first()
    
    accounts = db.query(Account).filter(Account.client_id == client.id).all()
    res = []
    for a in accounts:
        count = db.query(Holding).filter(Holding.account_id == a.id).count()
        res.append(AccountResponse(
            id=a.id,
            client_id=a.client_id,
            account_number=a.account_number,
            account_name=a.account_name,
            account_type=a.account_type,
            institution=a.institution,
            balance=a.balance,
            cash_available=a.cash_available,
            currency=a.currency,
            holdings_count=count
        ))
    return res

@router.get("/holdings", response_model=List[HoldingResponse])
def get_holdings(
    account_id: Optional[int] = None,
    asset_class: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Holding)
    if account_id:
        query = query.filter(Holding.account_id == account_id)
    if asset_class and asset_class != "All":
        query = query.filter(Holding.asset_class == asset_class)
    if search:
        search_fmt = f"%{search}%"
        query = query.filter((Holding.symbol.ilike(search_fmt)) | (Holding.security_name.ilike(search_fmt)))
    
    return query.order_by(Holding.market_value.desc()).all()

@router.get("/portfolio")
def get_portfolio_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.user_id == current_user.id).first()
    if not client:
        client = db.query(Client).first()
    
    holdings = db.query(Holding).all()
    total_val = sum(h.market_value for h in holdings)
    total_cost = sum(h.cost_basis for h in holdings)
    total_gain = total_val - total_cost
    gain_pct = (total_gain / total_cost * 100) if total_cost > 0 else 0.0

    return {
        "portfolio_name": "Mercer Discretionary Core Growth Portfolio",
        "total_value": total_val,
        "cost_basis": total_cost,
        "unrealized_gain": total_gain,
        "unrealized_gain_percent": round(gain_pct, 2),
        "target_risk_score": 72,
        "sharpe_ratio": 1.84,
        "benchmark_comparison": {
            "sp500_ytd": 14.8,
            "portfolio_ytd": 16.4,
            "alpha": "+1.6%"
        },
        "sector_exposure": [
            {"sector": "Information Technology", "percentage": 34.2},
            {"sector": "Financials", "percentage": 16.5},
            {"sector": "Healthcare", "percentage": 14.1},
            {"sector": "Consumer Discretionary", "percentage": 12.8},
            {"sector": "Fixed Income / Gov / Muni", "percentage": 14.4},
            {"sector": "Real Estate", "percentage": 8.0}
        ],
        "geographic_exposure": [
            {"region": "North America", "percentage": 76.5},
            {"region": "Developed Europe", "percentage": 12.5},
            {"region": "Asia-Pacific", "percentage": 7.0},
            {"region": "Emerging Markets", "percentage": 4.0}
        ]
    }

# Goals Endpoints (CRUD)
@router.get("/goals", response_model=List[GoalResponse])
def get_goals(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.user_id == current_user.id).first()
    if not client:
        client = db.query(Client).first()

    goals = db.query(Goal).filter(Goal.client_id == client.id).all()
    res = []
    for g in goals:
        progress = round((g.current_amount / g.target_amount * 100), 1) if g.target_amount > 0 else 0
        res.append(GoalResponse(
            id=g.id,
            title=g.title,
            category=g.category,
            target_amount=g.target_amount,
            current_amount=g.current_amount,
            target_date=g.target_date,
            monthly_contribution=g.monthly_contribution,
            probability=g.probability,
            status=g.status,
            notes=g.notes,
            progress_percent=progress
        ))
    return res

@router.post("/goals", response_model=GoalResponse)
def create_goal(goal_in: GoalCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.user_id == current_user.id).first()
    if not client:
        client = db.query(Client).first()

    g = Goal(
        client_id=client.id,
        title=goal_in.title,
        category=goal_in.category,
        target_amount=goal_in.target_amount,
        current_amount=goal_in.current_amount,
        target_date=goal_in.target_date,
        monthly_contribution=goal_in.monthly_contribution,
        probability=85.0,
        status="On Track",
        notes=goal_in.notes
    )
    db.add(g)
    db.commit()
    db.refresh(g)

    log_audit_event(db, action="CREATE_GOAL", user=current_user, entity_type="Goal", entity_id=str(g.id), details=f"Created goal {g.title}")

    progress = round((g.current_amount / g.target_amount * 100), 1) if g.target_amount > 0 else 0
    return GoalResponse(
        id=g.id,
        title=g.title,
        category=g.category,
        target_amount=g.target_amount,
        current_amount=g.current_amount,
        target_date=g.target_date,
        monthly_contribution=g.monthly_contribution,
        probability=g.probability,
        status=g.status,
        notes=g.notes,
        progress_percent=progress
    )

@router.put("/goals/{goal_id}", response_model=GoalResponse)
def update_goal(goal_id: int, goal_in: GoalUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    g = db.query(Goal).filter(Goal.id == goal_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Goal not found")

    if goal_in.title is not None:
        g.title = goal_in.title
    if goal_in.target_amount is not None:
        g.target_amount = goal_in.target_amount
    if goal_in.current_amount is not None:
        g.current_amount = goal_in.current_amount
    if goal_in.target_date is not None:
        g.target_date = goal_in.target_date
    if goal_in.monthly_contribution is not None:
        g.monthly_contribution = goal_in.monthly_contribution
    if goal_in.status is not None:
        g.status = goal_in.status
    if goal_in.notes is not None:
        g.notes = goal_in.notes

    db.commit()
    db.refresh(g)
    log_audit_event(db, action="UPDATE_GOAL", user=current_user, entity_type="Goal", entity_id=str(g.id), details=f"Updated goal {g.title}")

    progress = round((g.current_amount / g.target_amount * 100), 1) if g.target_amount > 0 else 0
    return GoalResponse(
        id=g.id,
        title=g.title,
        category=g.category,
        target_amount=g.target_amount,
        current_amount=g.current_amount,
        target_date=g.target_date,
        monthly_contribution=g.monthly_contribution,
        probability=g.probability,
        status=g.status,
        notes=g.notes,
        progress_percent=progress
    )

@router.delete("/goals/{goal_id}")
def delete_goal(goal_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    g = db.query(Goal).filter(Goal.id == goal_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    db.delete(g)
    db.commit()
    log_audit_event(db, action="DELETE_GOAL", user=current_user, entity_type="Goal", entity_id=str(goal_id))
    return {"message": "Goal deleted successfully"}

@router.get("/scenarios")
def get_scenario_comparisons():
    return {
        "scenarios": [
            {
                "id": "conservative",
                "name": "Scenario A: Capital Preservation & Defensive Income",
                "equity_allocation": 35,
                "fixed_income_allocation": 55,
                "alternatives_cash": 10,
                "expected_return": 5.2,
                "projected_portfolio_2035": 3650000,
                "success_probability": 94,
                "monthly_drawdown_risk": "Low (-4.8%)",
                "required_monthly_savings": 5800,
                "expected_retirement_age": 66
            },
            {
                "id": "balanced",
                "name": "Scenario B: Core Wealth Compounder (Current Baseline)",
                "equity_allocation": 60,
                "fixed_income_allocation": 30,
                "alternatives_cash": 10,
                "expected_return": 7.4,
                "projected_portfolio_2035": 4520000,
                "success_probability": 88,
                "monthly_drawdown_risk": "Moderate (-9.5%)",
                "required_monthly_savings": 4500,
                "expected_retirement_age": 64
            },
            {
                "id": "growth",
                "name": "Scenario C: Maximum Growth & Venture Tilt",
                "equity_allocation": 80,
                "fixed_income_allocation": 10,
                "alternatives_cash": 10,
                "expected_return": 9.6,
                "projected_portfolio_2035": 5680000,
                "success_probability": 76,
                "monthly_drawdown_risk": "Elevated (-16.2%)",
                "required_monthly_savings": 3200,
                "expected_retirement_age": 62
            }
        ]
    }
