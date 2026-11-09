from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum
)
from sqlalchemy.orm import relationship
from app.database import Base

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # client, advisor, sponsor, participant, admin
    description = Column(String(255), nullable=True)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=False)
    avatar_url = Column(String(255), nullable=True)
    role_name = Column(String(50), nullable=False, default="client")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    client_profile = relationship("Client", back_populates="user", uselist=False)
    advisor_profile = relationship("Advisor", back_populates="user", uselist=False)
    participant_profile = relationship("Participant", back_populates="user", uselist=False)
    notifications = relationship("Notification", back_populates="user")
    tasks = relationship("Task", back_populates="user")

class Household(Base):
    __tablename__ = "households"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    total_net_worth = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    clients = relationship("Client", back_populates="household")

class Advisor(Base):
    __tablename__ = "advisors"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    title = Column(String(100), default="Senior Wealth Advisor")
    firm_name = Column(String(150), default="Nexqile Private Wealth Management")
    phone = Column(String(50), default="+1 (800) 555-0199")
    aum = Column(Float, default=148500000.0)
    
    user = relationship("User", back_populates="advisor_profile")
    clients = relationship("Client", back_populates="advisor")
    meetings = relationship("Meeting", back_populates="advisor")

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    advisor_id = Column(Integer, ForeignKey("advisors.id"), nullable=True)
    household_id = Column(Integer, ForeignKey("households.id"), nullable=True)
    risk_tolerance = Column(String(50), default="Moderate Aggressive")
    net_worth = Column(Float, default=2840500.0)
    invested_assets = Column(Float, default=2310200.0)
    cash_balance = Column(Float, default=184300.0)
    retirement_assets = Column(Float, default=1720000.0)
    ytd_return = Column(Float, default=8.42)
    tax_bracket = Column(String(50), default="35% Federal, 6.5% State")
    status = Column(String(50), default="Active")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="client_profile")
    advisor = relationship("Advisor", back_populates="clients")
    household = relationship("Household", back_populates="clients")
    accounts = relationship("Account", back_populates="client")
    portfolios = relationship("Portfolio", back_populates="client")
    goals = relationship("Goal", back_populates="client")
    estate_plan = relationship("EstatePlan", back_populates="client", uselist=False)

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    account_number = Column(String(50), unique=True, nullable=False)
    account_name = Column(String(100), nullable=False)
    account_type = Column(String(50), nullable=False)  # Taxable, Traditional IRA, Roth IRA, 401(k), Family Trust
    institution = Column(String(100), default="Nexqile Custody & Clearing")
    balance = Column(Float, default=0.0)
    cash_available = Column(Float, default=0.0)
    currency = Column(String(10), default="USD")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="accounts")
    holdings = relationship("Holding", back_populates="account")
    transactions = relationship("Transaction", back_populates="account")

class Portfolio(Base):
    __tablename__ = "portfolios"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    name = Column(String(100), nullable=False)
    total_value = Column(Float, default=0.0)
    cost_basis = Column(Float, default=0.0)
    unrealized_gain = Column(Float, default=0.0)
    target_risk_score = Column(Integer, default=72)
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="portfolios")

class Holding(Base):
    __tablename__ = "holdings"
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    symbol = Column(String(20), nullable=False)
    security_name = Column(String(150), nullable=False)
    asset_class = Column(String(50), nullable=False)  # Equities, Fixed Income, Alternatives, Real Estate, Cash
    sector = Column(String(100), nullable=True)
    quantity = Column(Float, nullable=False)
    cost_basis = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    market_value = Column(Float, nullable=False)
    unrealized_gain = Column(Float, nullable=False)
    unrealized_gain_percent = Column(Float, nullable=False)
    allocation_percent = Column(Float, default=0.0)
    dividend_yield = Column(Float, default=1.5)

    account = relationship("Account", back_populates="holdings")
    tax_lots = relationship("TaxLot", back_populates="holding")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    transaction_type = Column(String(50), nullable=False)  # Buy, Sell, Dividend, Deposit, Withdrawal
    symbol = Column(String(20), nullable=True)
    description = Column(String(255), nullable=False)
    quantity = Column(Float, default=0.0)
    price = Column(Float, default=0.0)
    amount = Column(Float, nullable=False)

    account = relationship("Account", back_populates="transactions")

class Goal(Base):
    __tablename__ = "goals"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    title = Column(String(150), nullable=False)
    category = Column(String(50), nullable=False)  # Retirement, Education, Home, Legacy, Emergency
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0)
    target_date = Column(String(20), nullable=False)
    monthly_contribution = Column(Float, default=0.0)
    probability = Column(Float, default=85.0)
    status = Column(String(50), default="On Track")  # On Track, Ahead, Behind, Critical
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="goals")

class TaxLot(Base):
    __tablename__ = "tax_lots"
    id = Column(Integer, primary_key=True, index=True)
    holding_id = Column(Integer, ForeignKey("holdings.id"), nullable=False)
    purchase_date = Column(DateTime, nullable=False)
    quantity = Column(Float, nullable=False)
    cost_basis_per_share = Column(Float, nullable=False)
    term = Column(String(20), default="Long")  # Short, Long
    unrealized_gain_loss = Column(Float, default=0.0)
    is_harvest_candidate = Column(Boolean, default=False)

    holding = relationship("Holding", back_populates="tax_lots")

class TaxOpportunity(Base):
    __tablename__ = "tax_opportunities"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    opportunity_type = Column(String(100), nullable=False)  # Tax-loss harvesting, Roth Conversion, RMD Optimization, Asset Location
    description = Column(Text, nullable=False)
    potential_savings = Column(Float, default=0.0)
    status = Column(String(50), default="Recommended")
    priority = Column(String(20), default="High")
    created_at = Column(DateTime, default=datetime.utcnow)

class EstatePlan(Base):
    __tablename__ = "estate_plans"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), unique=True, nullable=False)
    estimated_gross_estate = Column(Float, default=4500000.0)
    has_will = Column(Boolean, default=True)
    has_healthcare_directive = Column(Boolean, default=True)
    has_poa = Column(Boolean, default=True)
    last_reviewed = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="Active")

    client = relationship("Client", back_populates="estate_plan")
    beneficiaries = relationship("Beneficiary", back_populates="estate_plan")
    trusts = relationship("Trust", back_populates="estate_plan")

class Beneficiary(Base):
    __tablename__ = "beneficiaries"
    id = Column(Integer, primary_key=True, index=True)
    estate_plan_id = Column(Integer, ForeignKey("estate_plans.id"), nullable=False)
    full_name = Column(String(150), nullable=False)
    relationship_type = Column(String(50), nullable=False)  # Spouse, Child, Sibling, Charity
    allocation_percentage = Column(Float, nullable=False)
    is_primary = Column(Boolean, default=True)

    estate_plan = relationship("EstatePlan", back_populates="beneficiaries")

class Trust(Base):
    __tablename__ = "trusts"
    id = Column(Integer, primary_key=True, index=True)
    estate_plan_id = Column(Integer, ForeignKey("estate_plans.id"), nullable=False)
    trust_name = Column(String(150), nullable=False)
    trust_type = Column(String(100), nullable=False)  # Revocable Living Trust, Irrevocable Life Insurance Trust, Charitable Remainder
    trustee_name = Column(String(150), nullable=False)
    assets_funded = Column(Float, default=0.0)
    status = Column(String(50), default="Fully Funded")

    estate_plan = relationship("EstatePlan", back_populates="trusts")

# Institutional Retirement Plans
class RetirementPlan(Base):
    __tablename__ = "retirement_plans"
    id = Column(Integer, primary_key=True, index=True)
    plan_name = Column(String(150), nullable=False)  # e.g., Apex Global Technologies 401(k) Profit Sharing Plan
    sponsor_name = Column(String(150), nullable=False)
    plan_number = Column(String(20), default="001")
    total_plan_assets = Column(Float, default=42500000.0)
    active_participants = Column(Integer, default=1240)
    participation_rate = Column(Float, default=88.4)
    avg_contribution_rate = Column(Float, default=7.2)
    employer_match_rate = Column(Float, default=4.5)
    plan_health_score = Column(Integer, default=92)
    compliance_status = Column(String(50), default="Compliant")
    created_at = Column(DateTime, default=datetime.utcnow)

    participants = relationship("Participant", back_populates="retirement_plan")
    investment_options = relationship("InvestmentOption", back_populates="retirement_plan")

class Participant(Base):
    __tablename__ = "participants"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    retirement_plan_id = Column(Integer, ForeignKey("retirement_plans.id"), nullable=False)
    current_balance = Column(Float, default=248500.0)
    contribution_percent = Column(Float, default=9.0)
    employer_match_percent = Column(Float, default=4.5)
    ytd_return_percent = Column(Float, default=7.85)
    retirement_age_target = Column(Integer, default=65)
    current_age = Column(Integer, default=38)
    projected_monthly_income = Column(Float, default=6850.0)
    readiness_score = Column(Integer, default=84)
    vested_percent = Column(Float, default=100.0)

    user = relationship("User", back_populates="participant_profile")
    retirement_plan = relationship("RetirementPlan", back_populates="participants")

class InvestmentOption(Base):
    __tablename__ = "investment_options"
    id = Column(Integer, primary_key=True, index=True)
    retirement_plan_id = Column(Integer, ForeignKey("retirement_plans.id"), nullable=False)
    fund_name = Column(String(150), nullable=False)
    ticker = Column(String(20), nullable=False)
    asset_category = Column(String(100), nullable=False)
    expense_ratio = Column(Float, nullable=False)
    one_year_return = Column(Float, nullable=False)
    five_year_return = Column(Float, nullable=False)
    morningstar_rating = Column(Integer, default=4)
    total_assets_allocated = Column(Float, default=0.0)

    retirement_plan = relationship("RetirementPlan", back_populates="investment_options")

# Operations & Communications
class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    title = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False)  # Statements, Tax Documents, Estate Documents, Agreements, Reports, Plan Documents
    file_type = Column(String(20), default="PDF")
    file_size = Column(String(20), default="1.8 MB")
    upload_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="Verified")  # Verified, Pending Signature, Archived

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Meeting(Base):
    __tablename__ = "meetings"
    id = Column(Integer, primary_key=True, index=True)
    advisor_id = Column(Integer, ForeignKey("advisors.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    title = Column(String(200), nullable=False)
    meeting_date = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=45)
    location = Column(String(150), default="Video Conference (Encrypted)")
    status = Column(String(50), default="Confirmed")  # Confirmed, Pending, Completed
    agenda = Column(Text, nullable=True)
    prep_notes = Column(Text, nullable=True)

    advisor = relationship("Advisor", back_populates="meetings")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True)
    priority = Column(String(20), default="Medium")  # Low, Medium, High, Urgent
    status = Column(String(50), default="Pending")  # Pending, In Progress, Completed
    category = Column(String(50), default="General")  # Tax, Portfolio, Estate, Compliance
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="tasks")

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    category = Column(String(50), default="System")  # Portfolio, Tax, Retirement, Documents, Meetings, Tasks, System
    is_read = Column(Boolean, default=False)
    action_url = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")

class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    report_type = Column(String(100), nullable=False)  # Portfolio Performance, Wealth Summary, Tax Summary, Retirement Readiness, Plan Health
    generated_date = Column(DateTime, default=datetime.utcnow)
    period = Column(String(50), default="Q3 2026")
    file_format = Column(String(20), default="PDF")
    status = Column(String(50), default="Ready")
    summary = Column(Text, nullable=True)

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_email = Column(String(255), nullable=True)
    action = Column(String(100), nullable=False)  # LOGIN, VIEW_CLIENT, REBALANCE, EXPORT_REPORT, UPDATE_GOAL
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(String(50), nullable=True)
    ip_address = Column(String(50), default="127.0.0.1")
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(Text, nullable=True)
