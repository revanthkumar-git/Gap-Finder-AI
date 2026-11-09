import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.seed import seed_database
from app.routers import (
    auth_router,
    dashboard_router,
    wealth_router,
    tax_estate_router,
    retirement_router,
    advisor_router,
    communication_router,
    documents_router,
    reports_router,
    admin_router
)

# Ensure database exists
if not os.path.exists(settings.DB_PATH):
    seed_database()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Nexqile - WealthAgent Production API: Wealth Management & Financial Advisory Portal"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router.router, prefix=settings.API_V1_STR)
app.include_router(dashboard_router.router, prefix=settings.API_V1_STR)
app.include_router(wealth_router.router, prefix=settings.API_V1_STR)
app.include_router(tax_estate_router.router, prefix=settings.API_V1_STR)
app.include_router(retirement_router.router, prefix=settings.API_V1_STR)
app.include_router(advisor_router.router, prefix=settings.API_V1_STR)
app.include_router(communication_router.router, prefix=settings.API_V1_STR)
app.include_router(documents_router.router, prefix=settings.API_V1_STR)
app.include_router(reports_router.router, prefix=settings.API_V1_STR)
app.include_router(admin_router.router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "portal": "Nexqile - WealthAgent",
        "status": "Online",
        "version": settings.VERSION,
        "docs_url": "/docs"
    }
