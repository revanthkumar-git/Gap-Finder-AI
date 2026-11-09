from datetime import datetime, timedelta
from app.database import SessionLocal, engine, Base
from app.models import (
    Role, User, Household, Advisor, Client, Account, Portfolio, Holding,
    Transaction, Goal, TaxLot, TaxOpportunity, EstatePlan, Beneficiary,
    Trust, RetirementPlan, Participant, InvestmentOption, Document,
    Message, Meeting, Task, Notification, Report, AuditEvent
)
from app.auth import hash_password

def seed_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    print("[*] Creating Roles...")
    roles = [
        Role(name="client", description="Individual Private Wealth Client"),
        Role(name="advisor", description="Senior Wealth Advisor & Portfolio Manager"),
        Role(name="sponsor", description="Institutional Retirement Plan Sponsor"),
        Role(name="participant", description="Retirement Plan Participant"),
        Role(name="admin", description="System Administrator & Compliance Officer")
    ]
    db.add_all(roles)
    db.commit()

    print("[*] Creating Users & Passwords...")
    demo_pass = hash_password("Demo@123")

    # 1. Client User
    client_user = User(
        email="client@nexqile.demo",
        hashed_password=demo_pass,
        full_name="Alexander Mercer",
        avatar_url="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80",
        role_name="client",
        is_active=True
    )
    # 2. Advisor User
    advisor_user = User(
        email="advisor@nexqile.demo",
        hashed_password=demo_pass,
        full_name="Eleanor Vance, CFP®, CFA",
        avatar_url="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80",
        role_name="advisor",
        is_active=True
    )
    # 3. Sponsor User
    sponsor_user = User(
        email="sponsor@nexqile.demo",
        hashed_password=demo_pass,
        full_name="Marcus Sterling",
        avatar_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80",
        role_name="sponsor",
        is_active=True
    )
    # 4. Admin User
    admin_user = User(
        email="admin@nexqile.demo",
        hashed_password=demo_pass,
        full_name="David Chen",
        avatar_url="https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&auto=format&fit=crop&q=80",
        role_name="admin",
        is_active=True
    )
    # 5. Participant User
    participant_user = User(
        email="participant@nexqile.demo",
        hashed_password=demo_pass,
        full_name="Sophia Chen",
        avatar_url="https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150&auto=format&fit=crop&q=80",
        role_name="participant",
        is_active=True
    )

    # Extra Clients for Advisor View
    extra_clients = [
        User(email="robert.sterling@example.com", hashed_password=demo_pass, full_name="Robert & Clara Sterling", role_name="client"),
        User(email="jonathan.vance@example.com", hashed_password=demo_pass, full_name="Jonathan Vance", role_name="client"),
        User(email="evelyn.hayes@example.com", hashed_password=demo_pass, full_name="Evelyn & Arthur Hayes", role_name="client"),
        User(email="daniel.thorne@example.com", hashed_password=demo_pass, full_name="Daniel K. Thorne", role_name="client"),
    ]

    db.add_all([client_user, advisor_user, sponsor_user, admin_user, participant_user] + extra_clients)
    db.commit()

    print("[*] Creating Advisor Profile...")
    advisor_profile = Advisor(
        user_id=advisor_user.id,
        title="Managing Director & Principal Advisor",
        firm_name="Nexqile Private Wealth Management Group",
        phone="+1 (212) 555-0199",
        aum=148500000.0
    )
    db.add(advisor_profile)
    db.commit()

    print("[*] Creating Household & Primary Client Profile...")
    mercer_household = Household(
        name="The Mercer Family Household",
        total_net_worth=2840500.0
    )
    db.add(mercer_household)
    db.commit()

    primary_client = Client(
        user_id=client_user.id,
        advisor_id=advisor_profile.id,
        household_id=mercer_household.id,
        risk_tolerance="Growth / Moderate Aggressive",
        net_worth=2840500.0,
        invested_assets=2310200.0,
        cash_balance=184300.0,
        retirement_assets=1720000.0,
        ytd_return=8.42,
        tax_bracket="35% Federal, 6.5% State",
        status="Active"
    )
    db.add(primary_client)

    # Add other clients to Advisor list
    clients_data = [
        (extra_clients[0].id, "The Sterling Estate", 4200000.0, "Conservative Growth", 7.15, "Active"),
        (extra_clients[1].id, "Vance Private Assets", 1850000.0, "Aggressive Growth", 11.20, "Active"),
        (extra_clients[2].id, "Hayes Family Trust", 3400000.0, "Moderate Balanced", 6.80, "Review Pending"),
        (extra_clients[3].id, "Thorne Holdings", 6100000.0, "Growth", 9.40, "Active")
    ]
    for uid, hname, nw, risk, ret, stat in clients_data:
        hh = Household(name=hname, total_net_worth=nw)
        db.add(hh)
        db.commit()
        c = Client(
            user_id=uid,
            advisor_id=advisor_profile.id,
            household_id=hh.id,
            risk_tolerance=risk,
            net_worth=nw,
            invested_assets=nw * 0.85,
            cash_balance=nw * 0.08,
            retirement_assets=nw * 0.45,
            ytd_return=ret,
            status=stat
        )
        db.add(c)
    db.commit()

    print("[*] Creating Accounts for Primary Client...")
    acct1 = Account(
        client_id=primary_client.id,
        account_number="NX-849201",
        account_name="Premier Taxable Brokerage",
        account_type="Taxable Brokerage",
        institution="Nexqile Custody & Clearing",
        balance=1125900.0,
        cash_available=62000.0
    )
    acct2 = Account(
        client_id=primary_client.id,
        account_number="NX-339104",
        account_name="Rollover Traditional IRA",
        account_type="Traditional IRA",
        institution="Nexqile Custody & Clearing",
        balance=895300.0,
        cash_available=24500.0
    )
    acct3 = Account(
        client_id=primary_client.id,
        account_number="NX-552918",
        account_name="Executive Roth IRA",
        account_type="Roth IRA",
        institution="Nexqile Custody & Clearing",
        balance=425000.0,
        cash_available=15800.0
    )
    acct4 = Account(
        client_id=primary_client.id,
        account_number="NX-771029",
        account_name="Mercer Revocable Family Trust",
        account_type="Family Trust",
        institution="Nexqile Custody & Clearing",
        balance=394300.0,
        cash_available=82000.0
    )
    db.add_all([acct1, acct2, acct3, acct4])
    db.commit()

    print("[*] Creating Holdings...")
    holdings_data = [
        # acct1: Taxable
        (acct1.id, "VOO", "Vanguard S&P 500 ETF", "Equities", "Large Blend", 850, 420.0, 512.80, 1.45),
        (acct1.id, "AAPL", "Apple Inc.", "Equities", "Information Technology", 320, 145.20, 224.50, 0.52),
        (acct1.id, "MSFT", "Microsoft Corporation", "Equities", "Information Technology", 280, 310.0, 448.20, 0.72),
        (acct1.id, "NVDA", "NVIDIA Corporation", "Equities", "Semiconductors", 350, 54.20, 128.40, 0.08),
        (acct1.id, "BND", "Vanguard Total Bond Market ETF", "Fixed Income", "Intermediate Bond", 1200, 75.50, 72.40, 3.80), # loss candidate
        (acct1.id, "IWM", "iShares Russell 2000 ETF", "Equities", "Small Cap", 450, 226.0, 218.40, 1.25), # loss candidate
        # acct2: IRA
        (acct2.id, "QQQ", "Invesco QQQ Trust", "Equities", "Large Growth", 600, 380.0, 478.60, 0.60),
        (acct2.id, "AMZN", "Amazon.com Inc.", "Equities", "Consumer Discretionary", 410, 132.0, 186.20, 0.0),
        (acct2.id, "JNJ", "Johnson & Johnson", "Equities", "Healthcare", 320, 155.0, 162.10, 3.10),
        (acct2.id, "AGG", "iShares Core US Aggregate Bond", "Fixed Income", "Broad Fixed Income", 1500, 101.50, 98.20, 3.90),
        # acct3: Roth IRA
        (acct3.id, "GOOGL", "Alphabet Inc. Class A", "Equities", "Communication Services", 260, 130.0, 178.50, 0.45),
        (acct3.id, "PLD", "Prologis Inc.", "Real Estate", "Industrial REIT", 450, 118.0, 122.30, 3.20),
        (acct3.id, "VXUS", "Vanguard Total International Stock ETF", "Equities", "International", 800, 58.0, 64.30, 2.85),
        # acct4: Trust
        (acct4.id, "MUB", "iShares National Muni Bond ETF", "Fixed Income", "Municipal Bonds", 900, 107.0, 108.50, 3.40),
        (acct4.id, "BRK.B", "Berkshire Hathaway Inc. Class B", "Equities", "Financials", 250, 360.0, 445.0, 0.0),
    ]

    total_port_val = 0.0
    for aid, sym, name, aclass, sec, qty, basis, price, div in holdings_data:
        mval = qty * price
        cost = qty * basis
        gain = mval - cost
        gain_pct = ((price - basis) / basis) * 100
        total_port_val += mval

        h = Holding(
            account_id=aid,
            symbol=sym,
            security_name=name,
            asset_class=aclass,
            sector=sec,
            quantity=qty,
            cost_basis=cost,
            current_price=price,
            market_value=mval,
            unrealized_gain=gain,
            unrealized_gain_percent=round(gain_pct, 2),
            allocation_percent=0.0,  # updated later
            dividend_yield=div
        )
        db.add(h)
        db.commit()

        # Add Tax Lots
        tl = TaxLot(
            holding_id=h.id,
            purchase_date=datetime.utcnow() - timedelta(days=400 if gain > 0 else 180),
            quantity=qty,
            cost_basis_per_share=basis,
            term="Long" if gain > 0 else "Short",
            unrealized_gain_loss=gain,
            is_harvest_candidate=(gain < 0)
        )
        db.add(tl)

    # Recalculate allocation %
    all_holdings = db.query(Holding).all()
    for h in all_holdings:
        h.allocation_percent = round((h.market_value / total_port_val) * 100, 2)
    db.commit()

    print("[*] Creating Goals...")
    goals = [
        Goal(
            client_id=primary_client.id,
            title="Retirement Wealth Target 2035",
            category="Retirement",
            target_amount=4500000.0,
            current_amount=1720000.0,
            target_date="2035-12-31",
            monthly_contribution=4500.0,
            probability=88.0,
            status="Ahead",
            notes="Assumes 7.5% annual nominal growth with tax-advantaged rebalancing."
        ),
        Goal(
            client_id=primary_client.id,
            title="Ivy League College Endowment Fund",
            category="Education",
            target_amount=400000.0,
            current_amount=265000.0,
            target_date="2029-08-31",
            monthly_contribution=1200.0,
            probability=92.0,
            status="On Track",
            notes="529 Educational Plan funded with automated index strategy."
        ),
        Goal(
            client_id=primary_client.id,
            title="Aspen Mountain Retreat Purchase",
            category="Home",
            target_amount=750000.0,
            current_amount=420000.0,
            target_date="2027-06-30",
            monthly_contribution=2500.0,
            probability=78.0,
            status="On Track",
            notes="Targeting 30% down payment on secondary luxury real estate."
        ),
        Goal(
            client_id=primary_client.id,
            title="Mercer Philanthropic Legacy Endowment",
            category="Legacy",
            target_amount=1000000.0,
            current_amount=380000.0,
            target_date="2040-01-01",
            monthly_contribution=1000.0,
            probability=84.0,
            status="On Track",
            notes="Funding structured Donor-Advised Fund (DAF) and climate research grants."
        ),
    ]
    db.add_all(goals)
    db.commit()

    print("[*] Creating Tax Opportunities & Estate...")
    tax_opps = [
        TaxOpportunity(
            client_id=primary_client.id,
            opportunity_type="Tax-Loss Harvesting",
            description="Harvest $18,400 in unrealized losses in Fixed Income (BND) & Small Cap (IWM) to offset taxable capital gains.",
            potential_savings=6440.0,
            status="Recommended",
            priority="High"
        ),
        TaxOpportunity(
            client_id=primary_client.id,
            opportunity_type="Partial Roth Conversion",
            description="Convert $45,000 from Traditional IRA into Roth IRA in the current bracket before projected 2027 tax changes.",
            potential_savings=14200.0,
            status="Under Review",
            priority="Medium"
        ),
        TaxOpportunity(
            client_id=primary_client.id,
            opportunity_type="Appreciated Asset Donation",
            description="Donate $25,000 of high-gain NVDA shares directly to Mercer DAF, bypassing capital gains taxes completely.",
            potential_savings=8750.0,
            status="Recommended",
            priority="High"
        )
    ]
    db.add_all(tax_opps)

    estate_plan = EstatePlan(
        client_id=primary_client.id,
        estimated_gross_estate=4850000.0,
        has_will=True,
        has_healthcare_directive=True,
        has_poa=True,
        last_reviewed=datetime.utcnow() - timedelta(days=45),
        status="Active"
    )
    db.add(estate_plan)
    db.commit()

    beneficiaries = [
        Beneficiary(estate_plan_id=estate_plan.id, full_name="Clara Mercer", relationship_type="Spouse", allocation_percentage=50.0, is_primary=True),
        Beneficiary(estate_plan_id=estate_plan.id, full_name="Lucas Mercer", relationship_type="Child", allocation_percentage=25.0, is_primary=True),
        Beneficiary(estate_plan_id=estate_plan.id, full_name="Maya Mercer", relationship_type="Child", allocation_percentage=25.0, is_primary=True)
    ]
    trusts = [
        Trust(estate_plan_id=estate_plan.id, trust_name="The Mercer Revocable Living Trust", trust_type="Revocable Living Trust", trustee_name="Alexander Mercer & Clara Mercer", assets_funded=2400000.0, status="Fully Funded"),
        Trust(estate_plan_id=estate_plan.id, trust_name="Mercer Family Dynastic Irrevocable Trust", trust_type="Irrevocable Generation-Skipping", trustee_name="Nexqile Private Trust Co.", assets_funded=1200000.0, status="Active")
    ]
    db.add_all(beneficiaries + trusts)
    db.commit()

    print("[*] Creating Institutional Retirement Plan & Participant...")
    ret_plan = RetirementPlan(
        plan_name="Apex Global Technologies 401(k) Profit Sharing Plan",
        sponsor_name="Apex Global Technologies Inc.",
        plan_number="001",
        total_plan_assets=42500000.0,
        active_participants=1240,
        participation_rate=88.4,
        avg_contribution_rate=7.2,
        employer_match_rate=4.5,
        plan_health_score=92,
        compliance_status="Compliant (Passed ADP/ACP & Top-Heavy Tests)"
    )
    db.add(ret_plan)
    db.commit()

    funds = [
        InvestmentOption(retirement_plan_id=ret_plan.id, fund_name="Vanguard 500 Index Admiral (VFIAX)", ticker="VFIAX", asset_category="Large Cap Blend", expense_ratio=0.04, one_year_return=24.5, five_year_return=14.2, morningstar_rating=5, total_assets_allocated=14200000.0),
        InvestmentOption(retirement_plan_id=ret_plan.id, fund_name="Fidelity Contrafund (FCNTX)", ticker="FCNTX", asset_category="Large Cap Growth", expense_ratio=0.39, one_year_return=28.1, five_year_return=15.8, morningstar_rating=5, total_assets_allocated=9800000.0),
        InvestmentOption(retirement_plan_id=ret_plan.id, fund_name="PIMCO Total Return Institutional (PTTRX)", ticker="PTTRX", asset_category="Core Bond", expense_ratio=0.46, one_year_return=5.8, five_year_return=2.4, morningstar_rating=4, total_assets_allocated=6400000.0),
        InvestmentOption(retirement_plan_id=ret_plan.id, fund_name="Vanguard Target Retirement 2050 (VFIFX)", ticker="VFIFX", asset_category="Target Date", expense_ratio=0.08, one_year_return=18.4, five_year_return=10.9, morningstar_rating=4, total_assets_allocated=7200000.0),
        InvestmentOption(retirement_plan_id=ret_plan.id, fund_name="American Funds Europacific Growth (RERGX)", ticker="RERGX", asset_category="International Equity", expense_ratio=0.47, one_year_return=12.2, five_year_return=7.6, morningstar_rating=4, total_assets_allocated=4900000.0),
    ]
    db.add_all(funds)

    participant_profile = Participant(
        user_id=participant_user.id,
        retirement_plan_id=ret_plan.id,
        current_balance=248500.0,
        contribution_percent=9.0,
        employer_match_percent=4.5,
        ytd_return_percent=7.85,
        retirement_age_target=65,
        current_age=38,
        projected_monthly_income=6850.0,
        readiness_score=84,
        vested_percent=100.0
    )
    db.add(participant_profile)
    db.commit()

    print("[*] Creating Documents, Meetings, Tasks, Messages, Notifications...")
    docs = [
        Document(client_id=primary_client.id, title="Q2 2026 Comprehensive Wealth Performance Report", category="Statements", file_type="PDF", file_size="2.4 MB", upload_date=datetime.utcnow() - timedelta(days=12), status="Verified"),
        Document(client_id=primary_client.id, title="2025 Consolidated Form 1099-Composite Tax Package", category="Tax Documents", file_type="PDF", file_size="1.8 MB", upload_date=datetime.utcnow() - timedelta(days=60), status="Verified"),
        Document(client_id=primary_client.id, title="Mercer Revocable Living Trust Agreement (Executed)", category="Estate Documents", file_type="PDF", file_size="4.2 MB", upload_date=datetime.utcnow() - timedelta(days=180), status="Verified"),
        Document(client_id=primary_client.id, title="Investment Policy Statement (IPS) 2026 Edition", category="Agreements", file_type="PDF", file_size="850 KB", upload_date=datetime.utcnow() - timedelta(days=90), status="Verified"),
        Document(client_id=primary_client.id, title="Apex Global 401(k) Plan Fiduciary & Benchmark Review", category="Plan Documents", file_type="PDF", file_size="5.1 MB", upload_date=datetime.utcnow() - timedelta(days=30), status="Verified"),
    ]
    db.add_all(docs)

    meetings = [
        Meeting(
            advisor_id=advisor_profile.id,
            client_id=primary_client.id,
            title="Q3 Strategic Wealth Review & Tax-Loss Harvesting",
            meeting_date=datetime.utcnow() + timedelta(days=4, hours=2),
            duration_minutes=60,
            location="Nexqile Private Client Suite (or Encrypted Video)",
            status="Confirmed",
            agenda="1. Portfolio performance vs benchmark\n2. Execution of $18.4K tax-loss harvesting\n3. Review Roth conversion window\n4. Real estate allocation update",
            prep_notes="Review BND and IWM lots; client interested in Aspen retreat financing strategy."
        ),
        Meeting(
            advisor_id=advisor_profile.id,
            client_id=primary_client.id,
            title="Estate & Philanthropy Advisory Session",
            meeting_date=datetime.utcnow() + timedelta(days=18),
            duration_minutes=45,
            location="Encrypted Video Conference",
            status="Confirmed",
            agenda="Review DAF allocation and irrevocable trust beneficiary distributions.",
            prep_notes="Coordinate with trust attorney for Clara & children distribution schedules."
        )
    ]
    db.add_all(meetings)

    tasks = [
        Task(user_id=client_user.id, title="Review Tax-Loss Harvesting proposal ($18,400)", description="Approve suggested trade sequence in taxable brokerage to lock in capital loss offsets.", due_date=datetime.utcnow() + timedelta(days=5), priority="High", status="Pending", category="Tax"),
        Task(user_id=client_user.id, title="Confirm Trust Beneficiary Designation signature", description="DocuSign amendment for the Mercer Revocable Trust addendum.", due_date=datetime.utcnow() + timedelta(days=12), priority="Medium", status="Pending", category="Estate"),
        Task(user_id=client_user.id, title="Review Q2 Quarterly Performance Statement", description="Inspect asset allocation drift and sector exposure in dashboard.", due_date=datetime.utcnow() - timedelta(days=2), priority="Low", status="Completed", category="Portfolio"),
        Task(user_id=advisor_user.id, title="Execute rebalance order for Sterling Estate", description="Rebalance equity allocation back within 2% band of IPS target.", due_date=datetime.utcnow() + timedelta(days=2), priority="Urgent", status="Pending", category="Portfolio"),
        Task(user_id=advisor_user.id, title="Prepare Apex Technologies 401(k) committee deck", description="Compile quarterly investment option performance and fee disclosures.", due_date=datetime.utcnow() + timedelta(days=7), priority="High", status="In Progress", category="Compliance")
    ]
    db.add_all(tasks)

    messages = [
        Message(
            sender_id=advisor_user.id,
            recipient_id=client_user.id,
            subject="Q3 Tax-Loss Harvesting & Portfolio Drift Opportunity",
            body="Good morning Alex, I ran our algorithmic tax scan this morning. We have identified an optimal opportunity to harvest approximately $18,400 in unrealized losses within your taxable brokerage account without changing your target asset allocation. Take a look at the Tax & Estate section and we can finalize this during our session next Tuesday.",
            is_read=False,
            created_at=datetime.utcnow() - timedelta(hours=3)
        ),
        Message(
            sender_id=client_user.id,
            recipient_id=advisor_user.id,
            subject="Re: Aspen Mountain Retreat Financing",
            body="Thanks Eleanor. We also want to review whether liquidating part of the taxable account vs borrowing against the portfolio (Securities-Backed Line of Credit) makes more tax sense for the down payment.",
            is_read=True,
            created_at=datetime.utcnow() - timedelta(days=1)
        )
    ]
    db.add_all(messages)

    notifications = [
        Notification(user_id=client_user.id, title="Tax-Loss Harvesting Identified", message="Potential tax savings of $6,440 found across Fixed Income & Small Cap holdings.", category="Tax", is_read=False, action_url="/tax"),
        Notification(user_id=client_user.id, title="Advisor Meeting Confirmed", message="Q3 Strategic Wealth Review with Eleanor Vance on Tuesday at 2:00 PM.", category="Meetings", is_read=False, action_url="/messages"),
        Notification(user_id=client_user.id, title="Dividend Received: $1,245.00", message="Quarterly dividend posted from Vanguard S&P 500 ETF (VOO).", category="Portfolio", is_read=True, action_url="/wealth/holdings"),
        Notification(user_id=sponsor_user.id, title="Annual 401(k) Compliance Passed", message="Apex Global Technologies successfully passed non-discrimination ADP/ACP testing.", category="Retirement", is_read=False, action_url="/retirement"),
        Notification(user_id=participant_user.id, title="Employer Match Maximized", message="Your 9.0% contribution fully secures the 4.5% company match ($5,400/yr).", category="Retirement", is_read=False, action_url="/participant")
    ]
    db.add_all(notifications)

    reports = [
        Report(title="Executive Wealth Summary Q3 2026", report_type="Wealth Summary", period="Q3 2026", file_format="PDF", status="Ready", summary="Comprehensive asset distribution, net worth velocity, and tax efficiency overview."),
        Report(title="Comprehensive Portfolio Performance & Attribution", report_type="Portfolio Performance", period="Trailing 12 Months", file_format="PDF", status="Ready", summary="Alpha generation, Sharpe ratio (1.82), sector allocation vs S&P 500 benchmark."),
        Report(title="Tax Optimization & Loss-Harvesting Strategy", report_type="Tax Summary", period="Tax Year 2026", file_format="PDF", status="Ready", summary="Detailed lot-by-lot analysis of short and long-term capital gains and loss harvesting opportunities."),
        Report(title="Apex 401(k) Plan Fiduciary & Health Audit", report_type="Plan Health", period="FY 2026", file_format="PDF", status="Ready", summary="Benchmarking analysis on participation rates (88.4%), fee compression, and fiduciary compliance.")
    ]
    db.add_all(reports)

    audit_events = [
        AuditEvent(user_id=client_user.id, user_email="client@nexqile.demo", action="SYSTEM_INIT", entity_type="System", details="Database populated with production-quality demo assets and high-net-worth accounts."),
        AuditEvent(user_id=advisor_user.id, user_email="advisor@nexqile.demo", action="REBALANCE_SIMULATION", entity_type="Portfolio", details="Drift analysis evaluated for client household Alex Mercer."),
        AuditEvent(user_id=admin_user.user_id if hasattr(admin_user, 'user_id') else admin_user.id, user_email="admin@nexqile.demo", action="COMPLIANCE_VERIFY", entity_type="Audit", details="Cryptographic audit event system verified and active.")
    ]
    db.add_all(audit_events)

    db.commit()
    db.close()
    print("[SUCCESS] Nexqile - WealthAgent Database initialized and seeded successfully!")

if __name__ == "__main__":
    seed_database()
