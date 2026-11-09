from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, EmailStr

# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    user: "UserResponse"

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    user_id: Optional[int] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str
    role_name: Optional[str] = "client"

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role_name: str
    avatar_url: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True

# Dashboard KPIs
class DashboardKPIs(BaseModel):
    net_worth: float
    invested_assets: float
    cash_balance: float
    retirement_assets: float
    ytd_return: float
    monthly_change_percent: float
    monthly_change_value: float
    total_liabilities: float

class PerformancePoint(BaseModel):
    date: str
    portfolio: float
    benchmark: float

class AllocationItem(BaseModel):
    category: str
    value: float
    percentage: float
    color: str

class UpcomingAction(BaseModel):
    id: int
    title: str
    category: str
    due_date: str
    priority: str
    status: str

# Wealth & Holdings
class HoldingResponse(BaseModel):
    id: int
    account_id: int
    symbol: str
    security_name: str
    asset_class: str
    sector: Optional[str] = None
    quantity: float
    cost_basis: float
    current_price: float
    market_value: float
    unrealized_gain: float
    unrealized_gain_percent: float
    allocation_percent: float
    dividend_yield: float

    class Config:
        from_attributes = True

class AccountResponse(BaseModel):
    id: int
    client_id: int
    account_number: str
    account_name: str
    account_type: str
    institution: str
    balance: float
    cash_available: float
    currency: str
    holdings_count: int = 0

    class Config:
        from_attributes = True

class GoalCreate(BaseModel):
    title: str
    category: str
    target_amount: float
    current_amount: float = 0.0
    target_date: str
    monthly_contribution: float = 0.0
    notes: Optional[str] = None

class GoalUpdate(BaseModel):
    title: Optional[str] = None
    target_amount: Optional[float] = None
    current_amount: Optional[float] = None
    target_date: Optional[str] = None
    monthly_contribution: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class GoalResponse(BaseModel):
    id: int
    title: str
    category: str
    target_amount: float
    current_amount: float
    target_date: str
    monthly_contribution: float
    probability: float
    status: str
    notes: Optional[str] = None
    progress_percent: float = 0.0

    class Config:
        from_attributes = True

# Tax & Estate
class TaxOpportunityResponse(BaseModel):
    id: int
    opportunity_type: str
    description: str
    potential_savings: float
    status: str
    priority: str

    class Config:
        from_attributes = True

class BeneficiaryResponse(BaseModel):
    id: int
    full_name: str
    relationship_type: str
    allocation_percentage: float
    is_primary: bool

    class Config:
        from_attributes = True

class TrustResponse(BaseModel):
    id: int
    trust_name: str
    trust_type: str
    trustee_name: str
    assets_funded: float
    status: str

    class Config:
        from_attributes = True

# Retirement (Sponsor & Participant)
class RetirementPlanOverview(BaseModel):
    id: int
    plan_name: str
    sponsor_name: str
    plan_number: str
    total_plan_assets: float
    active_participants: int
    participation_rate: float
    avg_contribution_rate: float
    employer_match_rate: float
    plan_health_score: int
    compliance_status: str

class ParticipantResponse(BaseModel):
    id: int
    current_balance: float
    contribution_percent: float
    employer_match_percent: float
    ytd_return_percent: float
    retirement_age_target: int
    current_age: int
    projected_monthly_income: float
    readiness_score: int
    vested_percent: float

# Advisor
class ClientSummary(BaseModel):
    id: int
    name: str
    email: str
    household_name: Optional[str]
    aum: float
    risk_tolerance: str
    ytd_return: float
    status: str
    last_contact: str
    open_tasks: int

# Operations
class DocumentResponse(BaseModel):
    id: int
    title: str
    category: str
    file_type: str
    file_size: str
    upload_date: datetime
    status: str

    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    recipient_id: int
    subject: str
    body: str

class MessageResponse(BaseModel):
    id: int
    sender_id: int
    sender_name: str
    recipient_id: int
    subject: str
    body: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class MeetingResponse(BaseModel):
    id: int
    title: str
    advisor_name: str
    meeting_date: datetime
    duration_minutes: int
    location: str
    status: str
    agenda: Optional[str]
    prep_notes: Optional[str]

    class Config:
        from_attributes = True

class TaskUpdate(BaseModel):
    status: Optional[str] = None
    title: Optional[str] = None
    priority: Optional[str] = None

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    due_date: Optional[datetime]
    priority: str
    status: str
    category: str

    class Config:
        from_attributes = True

class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    category: str
    is_read: bool
    action_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class ReportResponse(BaseModel):
    id: int
    title: str
    report_type: str
    generated_date: datetime
    period: str
    file_format: str
    status: str
    summary: Optional[str]

    class Config:
        from_attributes = True

class AuditEventResponse(BaseModel):
    id: int
    user_email: Optional[str]
    action: str
    entity_type: Optional[str]
    entity_id: Optional[str]
    ip_address: str
    timestamp: datetime
    details: Optional[str]

    class Config:
        from_attributes = True
