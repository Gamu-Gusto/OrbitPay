import os
import uvicorn
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from core.limiter import limiter
from db import Base, engine, SessionLocal
from orm_models import Role, SystemConfig

# Routers
from routers.auth import router as auth_router
from routers.users import router as users_router
from routers.companies import router as companies_router
from routers.employees import router as employees_router
from routers.payroll import router as payroll_router
from routers.leave import router as leave_router
from routers.documents import router as documents_router
from routers.banking import router as banking_router
from routers.reports import router as reports_router
from routers.audit_log import router as audit_log_router
from routers.self_service import router as self_service_router
from routers.registrations import router as registrations_router
from routers.setup import router as setup_router
from hr_reports import router as hr_reports_router


def run_migrations():
    """Idempotently fix schema mismatches and add new columns (no Alembic required)."""
    with engine.connect() as conn:
        # Drop refresh_tokens if it has the old jti column — create_all will recreate it
        try:
            result = conn.execute(text("PRAGMA table_info(refresh_tokens)"))
            existing_cols = {row[1] for row in result}
            if "jti" in existing_cols:
                conn.execute(text("DROP TABLE refresh_tokens"))
                conn.commit()
        except Exception:
            conn.rollback()

        # Add missing columns to existing tables
        cols = [
            ("payroll_records", "status",                               "TEXT DEFAULT 'approved'"),
            ("payroll_records", "approved_by",                          "INTEGER"),
            ("payroll_records", "approved_at",                          "TIMESTAMP"),
            ("payroll_records", "rejection_reason",                     "TEXT"),
            ("payroll_records", "other_earnings_description",           "TEXT"),
            ("employees",       "bank_account_last4",                   "TEXT"),
            ("employees",       "pension_fund_name",                    "TEXT"),
            ("employees",       "medical_aid_scheme_name",              "TEXT"),
            ("leave_requests",  "reviewed_by",                          "INTEGER"),
            ("leave_requests",  "reviewed_at",                          "TIMESTAMP"),
            ("leave_requests",  "review_note",                          "TEXT"),
            ("leave_requests",  "documentation_requested_reason",       "TEXT"),
            ("audit_events",    "company_id",                           "INTEGER"),
            ("audit_events",    "ip_address",                           "TEXT"),
            ("users",           "force_password_change",                "BOOLEAN DEFAULT FALSE"),
        ]
        for table, col, col_type in cols:
            try:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
                conn.commit()
            except Exception:
                conn.rollback()  # Column already exists — safe to ignore

        # Rename client_admin role to manager (idempotent)
        try:
            conn.execute(text("UPDATE roles SET name='manager' WHERE name='client_admin'"))
            conn.commit()
        except Exception:
            conn.rollback()


def seed_roles():
    db = SessionLocal()
    try:
        existing = {r.name for r in db.query(Role).all()}
        for name in ["super_admin", "accountant", "manager", "employee"]:
            if name not in existing:
                db.add(Role(name=name))
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def seed_system_config():
    db = SessionLocal()
    try:
        if not db.get(SystemConfig, "admin_setup_complete"):
            db.add(SystemConfig(key="admin_setup_complete", value="false"))
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()
    Base.metadata.create_all(bind=engine)
    seed_roles()
    seed_system_config()
    yield


app = FastAPI(
    title="OrbitPay Payroll API",
    description="API for calculating payroll and generating payslips.",
    version="1.0.0",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_allowed_origins = [
    "http://localhost:5173", "http://127.0.0.1:5173",
    "http://localhost:5174", "http://127.0.0.1:5174",
    "http://localhost:5179", "http://127.0.0.1:5179",
    "https://localhost:5173", "https://127.0.0.1:5173",
    "https://localhost:5174", "https://127.0.0.1:5174",
    "https://localhost:5179", "https://127.0.0.1:5179",
    "https://192.168.0.190:5173", "https://192.168.0.190:5174", "https://192.168.0.190:5179",
]
_frontend_url = os.environ.get("FRONTEND_URL", "")
if _frontend_url:
    _allowed_origins.append(_frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(companies_router)
app.include_router(employees_router)
app.include_router(payroll_router)
app.include_router(leave_router)
app.include_router(documents_router)
app.include_router(banking_router)
app.include_router(reports_router)
app.include_router(audit_log_router)
app.include_router(self_service_router)
app.include_router(registrations_router)
app.include_router(setup_router)
app.include_router(hr_reports_router, prefix="/api", tags=["hr-reports"])


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
