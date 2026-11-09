from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Client, Account, Holding, Goal, Task, Meeting
from app.auth import get_current_user
from app.schemas import DashboardKPIs

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/kpis", response_model=DashboardKPIs)
def get_dashboard_kpis(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.user_id == current_user.id).first()
    
    # If advisor or admin or sponsor, fallback to primary client or aggregated demo values
    if not client:
        client = db.query(Client).first()
    
    net_worth = client.net_worth if client else 2840500.0
    invested = client.invested_assets if client else 2310200.0
    cash = client.cash_balance if client else 184300.0
    retirement = client.retirement_assets if client else 1720000.0
    ytd = client.ytd_return if client else 8.42

    return {
        "net_worth": net_worth,
        "invested_assets": invested,
        "cash_balance": cash,
        "retirement_assets": retirement,
        "ytd_return": ytd,
        "monthly_change_percent": 1.84,
        "monthly_change_value": 48250.0,
        "total_liabilities": 245000.0  # Mortgage on primary residence
    }

@router.get("/performance")
def get_performance_timeline(range: str = "1Y", current_user: User = Depends(get_current_user)):
    # Realistic high-resolution performance curves
    data_map = {
        "1M": [
            {"date": "Day 1", "portfolio": 2795000, "benchmark": 2795000},
            {"date": "Day 5", "portfolio": 2808000, "benchmark": 2801000},
            {"date": "Day 10", "portfolio": 2814000, "benchmark": 2806000},
            {"date": "Day 15", "portfolio": 2805000, "benchmark": 2799000},
            {"date": "Day 20", "portfolio": 2826000, "benchmark": 2812000},
            {"date": "Day 25", "portfolio": 2835000, "benchmark": 2819000},
            {"date": "Current", "portfolio": 2840500, "benchmark": 2824000},
        ],
        "3M": [
            {"date": "Jun W1", "portfolio": 2720000, "benchmark": 2720000},
            {"date": "Jun W3", "portfolio": 2745000, "benchmark": 2738000},
            {"date": "Jul W1", "portfolio": 2772000, "benchmark": 2755000},
            {"date": "Jul W3", "portfolio": 2798000, "benchmark": 2774000},
            {"date": "Aug W1", "portfolio": 2815000, "benchmark": 2792000},
            {"date": "Aug W3", "portfolio": 2831000, "benchmark": 2810000},
            {"date": "Current", "portfolio": 2840500, "benchmark": 2824000},
        ],
        "6M": [
            {"date": "Mar", "portfolio": 2620000, "benchmark": 2620000},
            {"date": "Apr", "portfolio": 2665000, "benchmark": 2650000},
            {"date": "May", "portfolio": 2690000, "benchmark": 2678000},
            {"date": "Jun", "portfolio": 2740000, "benchmark": 2720000},
            {"date": "Jul", "portfolio": 2795000, "benchmark": 2770000},
            {"date": "Aug", "portfolio": 2840500, "benchmark": 2824000},
        ],
        "1Y": [
            {"date": "Sep '25", "portfolio": 2480000, "benchmark": 2480000},
            {"date": "Nov '25", "portfolio": 2540000, "benchmark": 2520000},
            {"date": "Jan '26", "portfolio": 2610000, "benchmark": 2580000},
            {"date": "Mar '26", "portfolio": 2680000, "benchmark": 2640000},
            {"date": "May '26", "portfolio": 2735000, "benchmark": 2695000},
            {"date": "Jul '26", "portfolio": 2790000, "benchmark": 2760000},
            {"date": "Sep '26", "portfolio": 2840500, "benchmark": 2824000},
        ],
        "3Y": [
            {"date": "2023", "portfolio": 2100000, "benchmark": 2100000},
            {"date": "Mid '24", "portfolio": 2320000, "benchmark": 2280000},
            {"date": "End '24", "portfolio": 2490000, "benchmark": 2430000},
            {"date": "Mid '25", "portfolio": 2640000, "benchmark": 2570000},
            {"date": "2026", "portfolio": 2840500, "benchmark": 2824000},
        ],
        "ALL": [
            {"date": "2020", "portfolio": 1650000, "benchmark": 1650000},
            {"date": "2021", "portfolio": 1940000, "benchmark": 1910000},
            {"date": "2022", "portfolio": 1820000, "benchmark": 1780000},
            {"date": "2023", "portfolio": 2150000, "benchmark": 2100000},
            {"date": "2024", "portfolio": 2480000, "benchmark": 2410000},
            {"date": "2025", "portfolio": 2690000, "benchmark": 2620000},
            {"date": "2026", "portfolio": 2840500, "benchmark": 2824000},
        ]
    }
    return data_map.get(range.upper(), data_map["1Y"])

@router.get("/allocation")
def get_asset_allocation(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [
        {"name": "Equities (US & Global)", "value": 1420250, "percentage": 50.0, "color": "#2C6457"},       # Refined Spruce
        {"name": "Fixed Income & Muni", "value": 568100, "percentage": 20.0, "color": "#3B506D"},          # Slate Navy
        {"name": "Real Estate / REITs", "value": 340860, "percentage": 12.0, "color": "#A47844"},          # Warm Sand
        {"name": "Alternative Assets", "value": 326990, "percentage": 11.5, "color": "#6B5B82"},           # Muted Plum
        {"name": "Cash & Liquidity", "value": 184300, "percentage": 6.5, "color": "#4E8B78"}               # Muted Eucalyptus
    ]

@router.get("/cashflow")
def get_cashflow_trend():
    return [
        {"month": "Apr", "income": 42500, "expenses": 18200, "savings": 24300},
        {"month": "May", "income": 44100, "expenses": 19600, "savings": 24500},
        {"month": "Jun", "income": 58200, "expenses": 23400, "savings": 34800},
        {"month": "Jul", "income": 43800, "expenses": 17900, "savings": 25900},
        {"month": "Aug", "income": 45000, "expenses": 21100, "savings": 23900},
        {"month": "Sep", "income": 46200, "expenses": 18500, "savings": 27700},
    ]

@router.get("/risk-profile")
def get_risk_profile():
    return {
        "risk_score": 72,
        "category": "Growth / Moderate Aggressive",
        "volatility_std": 12.4,
        "sharpe_ratio": 1.84,
        "beta": 0.94,
        "max_drawdown": -9.8,
        "benchmark_beta": 1.00
    }

@router.get("/upcoming-actions")
def get_upcoming_actions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [
        {
            "id": 1,
            "title": "Execute $18.4K Tax-Loss Harvesting",
            "category": "Tax Optimization",
            "due_date": "Sep 08, 2026",
            "priority": "High",
            "status": "Recommended",
            "icon": "TrendingDown"
        },
        {
            "id": 2,
            "title": "Q3 Strategic Review with Eleanor Vance, CFA",
            "category": "Advisor Meeting",
            "due_date": "Sep 12, 2026",
            "priority": "Medium",
            "status": "Confirmed",
            "icon": "Calendar"
        },
        {
            "id": 3,
            "title": "Sign Revocable Living Trust Addendum",
            "category": "Estate Planning",
            "due_date": "Sep 16, 2026",
            "priority": "Urgent",
            "status": "Signature Required",
            "icon": "FileText"
        },
        {
            "id": 4,
            "title": "Annual 401(k) Catch-Up Review & Matching",
            "category": "Retirement Plan",
            "due_date": "Oct 01, 2026",
            "priority": "Medium",
            "status": "Scheduled",
            "icon": "Award"
        }
    ]
