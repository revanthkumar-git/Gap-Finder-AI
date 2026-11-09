# Nexqile - WealthAgent
> **A Modern Wealth Management & Financial Advisory Portal**  
> Institutional-grade private wealth architecture, multi-account custody, tax-alpha generation, and 401(k) retirement fiduciary oversight.

---

## 🏛️ Executive Summary

**Nexqile - WealthAgent** delivers a Bloomberg-level financial cockpit combined with modern SaaS usability. Engineered for high-net-worth individuals, fiduciary financial advisors, institutional plan sponsors, and 401(k) plan participants, the application replaces fragmented spreadsheets and legacy portals with a unified, real-time private wealth management platform.

### Core Architecture Pillars:
- **Role-Based Experience**: Dedicated cockpits for **Clients**, **Financial Advisors**, **Institutional Plan Sponsors**, **Retirement Participants**, and **Administrators**.
- **Algorithmic Tax Alpha**: Automated Tax-Loss Harvesting detection ($18,400 harvestable loss simulation), Roth conversion evaluator, and capital gain offset modeling.
- **Unified Custody & Holdings**: Multi-account aggregation (Taxable Brokerage, Rollover IRA, Executive Roth IRA, Family Trust) with real-time tax-lot accounting and CSV export.
- **Fiduciary Retirement Plans**: Institutional 401(k) sponsor oversight ($42.5M AUM, 1,240 participants, 88.4% participation rate) with automated non-discrimination ADP/ACP testing and Form 5500 filing verification.
- **Participant Journey**: Interactive contribution calculator with instant company match simulation, retirement readiness score, and 7 interactive financial literacy modules.
- **Advisor Workstation**: Practice management ($148.5M AUM), client dossier drilldown, and drift rebalancing engine.
- **Encrypted Document Vault**: SEC Rule 17a-4 compliant category-based storage with cryptographic signature verification.
- **Global Command Center**: Fuzzy search palette accessible anywhere via `Ctrl + K`.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 18, Vite 6, TypeScript 5.7, Tailwind CSS 3.4, Recharts, Lucide Icons |
| **Backend** | Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2.0 ORM, Uvicorn |
| **Database** | SQLite 3 (relational schema with `PRAGMA foreign_keys=ON`) |
| **Security** | JWT (HMAC-SHA256), Bcrypt adaptive hashing, Role-Based Access Control (RBAC), SEC Rule 17a-4 simulated audit trails |

---

## 🔑 Demo Access Credentials

The portal is pre-seeded with 5 distinct personas. You can use the **1-Click Demo Login** buttons on the login screen or enter the credentials below:

| Persona | Email | Password | Primary Cockpit Experience |
| :--- | :--- | :--- | :--- |
| **Client** | `client@nexqile.demo` | `Demo@123` | **Wealth Dashboard**: $2.84M Net Worth, Performance vs S&P 500, Holdings, Tax Harvesting, Goals |
| **Financial Advisor** | `advisor@nexqile.demo` | `Demo@123` | **Advisor Workstation**: $148.5M AUM, Client Dossiers, Tax-Aware Rebalancing Engine |
| **Plan Sponsor** | `sponsor@nexqile.demo` | `Demo@123` | **Sponsor Dashboard**: Apex 401(k) Plan ($42.5M), Fund Lineup, ADP/ACP Compliance, Form 5500 |
| **Participant** | `participant@nexqile.demo` | `Demo@123` | **Retirement Portal**: $248.5K Balance, Interactive Match Slider, 7 Education Modules |
| **Administrator** | `admin@nexqile.demo` | `Demo@123` | **Admin Console**: User Directory, RBAC Permissions, Immutable Audit Event Logs |

---

## 📂 Project Structure

```
├── backend/
│   ├── app/
│   │   ├── config.py              # Application settings, JWT secret, and database URL
│   │   ├── database.py            # SQLite engine, sessionmaker, foreign key pragma
│   │   ├── models.py              # Relational models (Users, Clients, Holdings, Plans, etc.)
│   │   ├── schemas.py             # Pydantic validation and serialization schemas
│   │   ├── auth.py                # Bcrypt hashing, JWT generation, and RBAC dependencies
│   │   ├── seed.py                # Database population with realistic wealth data
│   │   ├── main.py                # FastAPI app initialization and CORS middleware
│   │   └── routers/
│   │       ├── auth_router.py          # /api/auth (login, logout, me, demo credentials)
│   │       ├── dashboard_router.py     # /api/dashboard (KPIs, performance, allocation, cashflow)
│   │       ├── wealth_router.py        # /api/wealth (accounts, holdings, goals CRUD, scenarios)
│   │       ├── tax_estate_router.py    # /api/tax-estate (tax summary, harvest execution, trusts)
│   │       ├── retirement_router.py    # /api/retirement (sponsor plan, fund lineup, participant)
│   │       ├── advisor_router.py       # /api/advisor (metrics, clients directory, rebalancer)
│   │       ├── communication_router.py # /api/comm (messages, meetings, tasks)
│   │       ├── documents_router.py     # /api/documents (categorized vault, upload, download)
│   │       ├── reports_router.py       # /api/reports (fiduciary reports generator and preview)
│   │       └── admin_router.py         # /api/admin (user management, audit event logs)
│   ├── run_backend.py             # Entrypoint to run FastAPI server on port 8000
│   └── wealthagent.db             # Local SQLite relational database
│
├── frontend/
│   ├── src/
│   │   ├── api/                   # API client with JWT injection and typed endpoints
│   │   ├── context/               # AuthContext, ThemeContext, NotificationContext (Toaster)
│   │   ├── types/                 # TypeScript domain interfaces and schemas
│   │   ├── components/
│   │   │   ├── charts/            # PerformanceChart, AllocationDonut, CashflowBar, RiskGauge
│   │   │   ├── layout/            # Sidebar, Navbar, Shell, CommandPalette (Ctrl+K)
│   │   │   └── ui/                # StatCard, Badge, Modal
│   │   └── pages/
│   │       ├── auth/              # Split-screen LoginPage with 1-click persona quick login
│   │       ├── dashboard/         # Client Wealth Dashboard with KPI cards & interactive charts
│   │       ├── wealth/            # Holdings table, Accounts, Goals CRUD, and Scenarios
│   │       ├── tax/               # Tax-loss harvesting, RMD, Estate trusts, Philanthropy
│   │       ├── retirement/        # Institutional Sponsor dashboard, funds, and compliance
│   │       ├── participant/       # Retirement journey, contribution slider, education center
│   │       ├── advisor/           # Practice workstation, client dossier, rebalance engine
│   │       ├── communication/     # Encrypted messages, meetings calendar, tasks checklist
│   │       ├── documents/         # Encrypted document vault with category filter and search
│   │       ├── reports/           # Fiduciary report generator with PDF/printable export
│   │       ├── admin/             # System console, user directory, immutable audit trail
│   │       └── settings/          # Profile settings, alert toggles, light/dark theme switch
│   ├── index.html
│   ├── vite.config.ts             # Vite configuration with proxy to port 8000
│   └── tailwind.config.js         # Custom wealth-management color palette and dark mode
└── README.md
```

---

## 🚀 Installation & Setup

### Prerequisites
- **Python 3.10+** (Tested on Python 3.13)
- **Node.js 18+** (Tested on Node.js 24)

---

### Step 1: Install Python Backend Dependencies
```bash
pip install fastapi uvicorn sqlalchemy pydantic pyjwt bcrypt python-multipart
```

### Step 2: Initialize & Seed SQLite Database
```bash
python -m app.seed
# (Run from within the backend/ directory)
```
*Creates `backend/wealthagent.db` and populates all accounts, portfolios, holdings, tax lots, retirement plans, documents, and audit trails.*

### Step 3: Start FastAPI Backend Server
```bash
python backend/run_backend.py
```
*The REST API will be live at `http://127.0.0.1:8000` (Interactive Swagger docs at `http://127.0.0.1:8000/docs`).*

### Step 4: Install Frontend Dependencies & Start Dev Server
In a separate terminal:
```bash
cd frontend
npm install --legacy-peer-deps
npm run dev
```
*The frontend will launch at `http://localhost:5173/`.*

---

## 📊 Feature Walkthrough

### 1. Client Cockpit (`client@nexqile.demo`)
- Consolidated net worth ($2.84M) across 4 custody accounts.
- Performance chart with benchmark comparison against the S&P 500 over 1M, 3M, 6M, 1Y, 3Y, and All-time intervals.
- Donut asset allocation breakdown (Equities 50%, Fixed Income 20%, Real Estate 12%, Alternatives 11.5%, Cash 6.5%).
- Tax-Loss Harvesting trigger identifying $18,400 in unrealized losses to offset taxable capital gains.

### 2. Advisor Workstation (`advisor@nexqile.demo`)
- Practice management dashboard tracking $148.5M AUM and $1.18M revenue.
- Comprehensive client directory with instant dossier drilldown into accounts, holdings, and goals.
- Algorithmic portfolio drift rebalancer with tax-aware trade generation and custodian OMS order simulation.

### 3. Institutional Plan Sponsor (`sponsor@nexqile.demo`)
- 401(k) Plan oversight ($42.5M AUM, 1,240 participants, 88.4% participation rate).
- Fiduciary fund lineup with Morningstar star ratings and expense ratios.
- Automated compliance monitoring: Form 5500 filing verification, Top-Heavy test, and ADP/ACP non-discrimination test results.

### 4. Participant Journey (`participant@nexqile.demo`)
- Retirement balance ($248.5K) and retirement readiness score (84/100).
- Interactive contribution slider allowing adjustments from 1% to 20% with real-time recalculation of company match dollars and projected retirement income.
- 7 research-backed financial literacy modules with reading modal views.

### 5. Administration & Audit (`admin@nexqile.demo`)
- User management directory with real-time role adjustment and account status toggling.
- Cryptographically immutable audit log tracking logins, trades, and report exports with IP address telemetry.

---

## 🛡️ Security & Disclosures

*Disclaimer: This application is a technology demonstration prototype for wealth-management workflows and does not constitute registered investment advice or fiduciary legal counsel.*

- Password hashing is enforced via **Bcrypt** with salt generation.
- Session authorization uses **JSON Web Tokens (JWT)** passed via HTTP `Authorization: Bearer` headers.
- All database operations are parameterized using **SQLAlchemy ORM** to eliminate SQL injection vulnerabilities.
- Audit trails record user actions with immutable timestamps and client IP addresses.