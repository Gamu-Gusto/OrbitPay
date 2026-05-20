import os
import io
import json
import base64
import smtplib
import uvicorn
from calendar import monthrange
from datetime import date, datetime, timedelta
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional, Tuple
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Body, Query, UploadFile, File, Form
from sqlalchemy import text
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from db import Base, engine, get_db, SessionLocal
from orm_models import Company, Employee, User, Role, UserRole, AccountantAssignment, UserCompany, EmployeeUser, PayrollRecord, LeaveBalance, RefreshToken, AuditEvent, LeaveRequest, EmployeeDocument, BankingChangeRequest
from models import PayrollInput, PayslipData, ReversePayrollInput, ReversePayrollResult, EmployeeDetails, CompanyDetails
from schemas import (
    CompanyCreate,
    CompanyUpdate,
    CompanyRead,
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeRead,
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    LogoutRequest,
    UserRead,
    AccountantAssignRequest,
    ClientAdminAssignRequest,
    EmployeeLinkRequest,
    LeaveBalanceCreate,
    LeaveBalanceUpdate,
    LeaveBalanceRead,
    BulkPayrollRequest,
    BulkPayrollResult,
    BulkPayrollEmployeeResult,
    PayrollApprovalRequest,
    EmployeeImportResult,
    LeaveRequestCreate,
    LeaveRequestReview,
    EmployeeDocumentRead,
    DocumentReviewRequest,
    BankingChangeCreate,
    BankingChangeRead,
    BankingChangeReviewRequest,
)
from auth import hash_password, verify_password, create_access_token, decode_token, create_refresh_token, hash_refresh_token, REFRESH_TOKEN_DAYS
from hr_reports import router as hr_reports_router
from utils import monthly_paye_from_gross, uif_employee, generate_payslip_pdf, gross_from_net_pay, calculate_sdl, calculate_leave_income

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
            ("payroll_records", "status",                    "TEXT DEFAULT 'approved'"),
            ("payroll_records", "approved_by",               "INTEGER"),
            ("payroll_records", "approved_at",               "TIMESTAMP"),
            ("payroll_records", "rejection_reason",          "TEXT"),
            ("payroll_records", "other_earnings_description","TEXT"),
            ("employees",       "bank_account_last4",        "TEXT"),
            ("employees",       "pension_fund_name",         "TEXT"),
            ("employees",       "medical_aid_scheme_name",   "TEXT"),
            # leave_requests approval columns
            ("leave_requests",  "reviewed_by",               "INTEGER"),
            ("leave_requests",  "reviewed_at",               "TIMESTAMP"),
            ("leave_requests",  "review_note",               "TEXT"),
        ]
        for table, col, col_type in cols:
            try:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
                conn.commit()
            except Exception:
                conn.rollback()  # Column already exists — safe to ignore


def log_audit(db: Session, user_id: Optional[int], action: str, entity_type: str = None, entity_id: int = None, payload: dict = None):
    """Write an audit event. Never raises — audit failures must not break business logic."""
    try:
        db.add(AuditEvent(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=json.dumps(payload) if payload else None
        ))
    except Exception:
        pass


# Seed roles if not present
def seed_roles():
    db = SessionLocal()
    try:
        existing = {r.name for r in db.query(Role).all()}
        for name in ["super_admin", "accountant", "client_admin", "employee"]:
            if name not in existing:
                db.add(Role(name=name))
        db.commit()
    except Exception as e:
        db.rollback()
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()
    Base.metadata.create_all(bind=engine)  # recreates any tables dropped by run_migrations
    seed_roles()
    yield

app = FastAPI(
    title="OrbitPay Payroll API",
    description="API for calculating payroll and generating payslips.",
    version="1.0.0",
    lifespan=lifespan,
)

# Register HR Reports router
app.include_router(
    hr_reports_router, 
    prefix="/api", 
    tags=["hr-reports"]
)

# Configure CORS to allow communication from the Vue.js frontend
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

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    try:
        token = credentials.credentials
        payload = decode_token(token)
        user_id = int(payload.get("sub"))
        roles = payload.get("roles", [])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Inactive user")
    user.role_names = roles
    return user

def require_roles(*allowed: str):
    def dep(user: User = Depends(get_current_user)):
        if not any(r in allowed for r in getattr(user, "role_names", [])):
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return dep

@app.post("/calculate-payroll", response_model=PayslipData)
async def calculate_payroll(input_data: PayrollInput, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Authorization checks for provided company/employee
    roles = getattr(user, "role_names", [])
    if input_data.company_id:
        get_company(input_data.company_id, db, user)
    if input_data.employee_id:
        emp_obj = db.get(Employee, input_data.employee_id)
        if not emp_obj:
            raise HTTPException(status_code=404, detail="Employee not found")
        if input_data.company_id and emp_obj.company_id != input_data.company_id:
            raise HTTPException(status_code=400, detail="Employee does not belong to the specified company")
        if "employee" in roles:
            link = db.query(EmployeeUser).filter_by(user_id=user.id, employee_id=emp_obj.id).first()
            if not link:
                raise HTTPException(status_code=403, detail="Forbidden")
        else:
            get_company(emp_obj.company_id, db, user)
    # Extract data from input
    basic_pay = input_data.basic_pay
    other_earnings = input_data.other_earnings
    pension = input_data.pension
    medical = input_data.medical

    # Calculate leave income if leave days are taken
    leave_income_details = None
    leave_income = 0.0
    if input_data.leave_days_taken > 0:
        annual_salary = basic_pay * 12  # Convert monthly to annual for calculation
        leave_income_details = calculate_leave_income(
            annual_salary=annual_salary,
            leave_days_taken=input_data.leave_days_taken,
            total_leave_days_available=input_data.total_leave_days_available
        )
        leave_income = leave_income_details['leave_income']

    # Calculate total remuneration for SDL (includes basic pay, other earnings, and leave income)
    total_remuneration = basic_pay + other_earnings + leave_income
    
    # Calculate SDL
    sdl_details = calculate_sdl(
        total_remuneration=total_remuneration,
        annual_payroll=input_data.annual_payroll,
        excluded_amounts=input_data.excluded_amounts
    )
    sdl_amount = sdl_details['sdl_amount']

    # Standard payroll calculations
    total_earnings = basic_pay + other_earnings + leave_income
    paye = monthly_paye_from_gross(total_earnings)
    uif = uif_employee(total_earnings)
    total_deductions = (
        pension + medical + (input_data.union_fees or 0.0) + (input_data.other_deductions or 0.0) + paye + uif
    )
    net_pay = total_earnings - total_deductions

    # Prepare earnings and deductions lists for PayslipData
    _earn_desc = input_data.other_earnings_description or "Other Earnings"
    earnings_list: List[Tuple[str, float]] = [("Basic Pay", basic_pay)]
    if other_earnings:
        earnings_list.append((_earn_desc, other_earnings))
    if leave_income > 0:
        earnings_list.append(("Leave Income", leave_income))
    
    deductions_list: List[Tuple[str, float]] = [
        ("PAYE", paye),
        ("UIF", uif),
        ("Pension", pension),
        ("Medical Aid", medical),
    ]
    if (input_data.union_fees or 0.0) > 0:
        deductions_list.append(("Union Fees", input_data.union_fees))
    if (input_data.other_deductions or 0.0) > 0:
        deductions_list.append(("Other Deductions", input_data.other_deductions))

    # Save payroll record to database if company_id is provided
    if input_data.company_id:
        try:
            # Calculate payrun period from pay_period_end
            payrun_month = input_data.period_end.month
            payrun_year = input_data.period_end.year
            payrun_period = f"{payrun_year}-{payrun_month:02d}"
            
            payroll_record = PayrollRecord(
                company_id=input_data.company_id,
                employee_id=input_data.employee_id,
                payrun_month=payrun_month,
                payrun_year=payrun_year,
                payrun_period=payrun_period,
                employee_name=f"{input_data.employee.first_names} {input_data.employee.last_name}",
                employee_id_no=input_data.employee.id_no,
                pay_period_start=input_data.period_start,
                pay_period_end=input_data.period_end,
                basic_pay=basic_pay,
                other_earnings=other_earnings,
                other_earnings_description=_earn_desc,
                leave_income=leave_income,
                total_earnings=total_earnings,
                paye=paye,
                uif_employee=uif,
                uif_employer=uif,
                sdl=sdl_amount,
                pension=pension,
                medical=medical,
                total_deductions=total_deductions,
                net_pay=net_pay,
                created_by=user.id
            )
            db.add(payroll_record)
            db.commit()
        except Exception:
            db.rollback()

    # Create PayslipData object
    payslip_data = PayslipData(
        employee=input_data.employee,
        company=input_data.company,
        period_start=input_data.period_start,
        period_end=input_data.period_end,
        payment_date=input_data.payment_date,
        earnings=earnings_list,
        total_earnings=total_earnings,
        deductions=deductions_list,
        total_deductions=total_deductions,
        net_pay=net_pay,
        paye=paye,
        uif=uif,
        sdl=sdl_amount,
        leave_income=leave_income,
        sdl_details=sdl_details,
        leave_income_details=leave_income_details,
    )
    return payslip_data

@app.post("/calculate-reverse-payroll", response_model=ReversePayrollResult)
async def calculate_reverse_payroll(input_data: ReversePayrollInput, user: User = Depends(get_current_user)):
    """
    Calculate gross salary from desired net pay.
    This is useful when companies want to pay employees a specific net amount.
    Note: SDL and leave income calculations are simplified in reverse mode since we're working backwards from net pay.
    """
    try:
        # Calculate leave income if leave days are taken
        leave_income_details = None
        leave_income = 0.0
        if input_data.leave_days_taken > 0:
            # For reverse calculation, we'll estimate annual salary from target net pay
            # This is an approximation since we don't know the exact gross yet
            estimated_annual_salary = input_data.target_net_pay * 12 * 1.4  # Rough estimate
            leave_income_details = calculate_leave_income(
                annual_salary=estimated_annual_salary,
                leave_days_taken=input_data.leave_days_taken,
                total_leave_days_available=input_data.total_leave_days_available
            )
            leave_income = leave_income_details['leave_income']

        # Calculate the gross salary needed to achieve the target net pay
        # Note: This doesn't account for SDL in the reverse calculation as it would create circular dependency
        calculated_gross_pay = gross_from_net_pay(
            target_net_pay=input_data.target_net_pay,
            pension=input_data.pension,
            medical=input_data.medical
        )
        
        # Now calculate all the details using the calculated gross pay
        total_earnings = calculated_gross_pay + input_data.other_earnings + leave_income
        
        # Calculate SDL based on total remuneration
        total_remuneration = calculated_gross_pay + input_data.other_earnings + leave_income
        sdl_details = calculate_sdl(
            total_remuneration=total_remuneration,
            annual_payroll=input_data.annual_payroll,
            excluded_amounts=input_data.excluded_amounts
        )
        sdl_amount = sdl_details['sdl_amount']
        
        paye = monthly_paye_from_gross(total_earnings)
        uif = uif_employee(total_earnings)
        total_deductions = (
            input_data.pension + input_data.medical + (input_data.union_fees or 0.0) + (input_data.other_deductions or 0.0) + paye + uif
        )
        net_pay = total_earnings - total_deductions
        
        # Prepare earnings and deductions lists
        _earn_desc_rev = input_data.other_earnings_description or "Other Earnings"
        earnings_list: List[Tuple[str, float]] = [("Basic Pay", calculated_gross_pay)]
        if input_data.other_earnings:
            earnings_list.append((_earn_desc_rev, input_data.other_earnings))
        if leave_income > 0:
            earnings_list.append(("Leave Income", leave_income))
            
        deductions_list: List[Tuple[str, float]] = [
            ("PAYE", paye),
            ("UIF", uif),
            ("Pension", input_data.pension),
            ("Medical Aid", input_data.medical),
        ]
        if (input_data.union_fees or 0.0) > 0:
            deductions_list.append(("Union Fees", input_data.union_fees))
        if (input_data.other_deductions or 0.0) > 0:
            deductions_list.append(("Other Deductions", input_data.other_deductions))
        
        # Create result object
        result = ReversePayrollResult(
            employee=input_data.employee,
            company=input_data.company,
            period_start=input_data.period_start,
            period_end=input_data.period_end,
            payment_date=input_data.payment_date,
            calculated_gross_pay=calculated_gross_pay,
            other_earnings=input_data.other_earnings,
            pension=input_data.pension,
            medical=input_data.medical,
            earnings=earnings_list,
            total_earnings=total_earnings,
            deductions=deductions_list,
            total_deductions=total_deductions,
            net_pay=net_pay,
            paye=paye,
            uif=uif,
            sdl=sdl_amount,
            uif_employer=uif,
            leave_income=leave_income,
            sdl_details=sdl_details,
            leave_income_details=leave_income_details,
        )
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in reverse calculation: {str(e)}")

@app.post("/generate-payslip")
async def generate_payslip(payslip_data: PayslipData, user: User = Depends(get_current_user)):
    try:
        pdf_bytes = generate_payslip_pdf(payslip_data.model_dump())
        return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", headers={
            "Content-Disposition": "attachment; filename=payslip.pdf"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {e}")


# ------------------ Auth ------------------
@app.post("/auth/register", response_model=UserRead)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    try:
        role_name = (req.role or "").strip().lower()
        if role_name not in ["super_admin", "accountant", "client_admin", "employee"]:
            raise HTTPException(status_code=400, detail="Invalid role")

        existing_user = db.query(User).filter(User.email == req.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        password_hash = hash_password(req.password)

        # Create user
        user = User(
            email=req.email, 
            password_hash=password_hash, 
            first_name=req.first_name, 
            last_name=req.last_name
        )
        db.add(user)
        db.flush()  # Get the user ID
        
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            raise HTTPException(status_code=400, detail="Invalid role")
        
        # Assign role
        db.add(UserRole(user_id=user.id, role_id=role.id))
        
        # Handle company and employee assignments
        if req.company_id and role_name in ("client_admin", "employee"):
            db.add(UserCompany(user_id=user.id, company_id=req.company_id))
        if req.employee_id and role_name == "employee":
            db.add(EmployeeUser(user_id=user.id, employee_id=req.employee_id))
        
        db.commit()
        return UserRead(
            id=user.id, 
            email=user.email, 
            first_name=user.first_name, 
            last_name=user.last_name, 
            is_active=user.is_active, 
            roles=[role_name]
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@app.post("/auth/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.email == req.email).first()

        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not user.is_active:
            raise HTTPException(status_code=401, detail="Account is inactive")

        if not verify_password(req.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        roles = [db.get(Role, ur.role_id).name for ur in user.roles]
        company_ids = []
        if "accountant" in roles:
            company_ids = [a.company_id for a in db.query(AccountantAssignment).filter_by(accountant_user_id=user.id).all()]
        token = create_access_token(str(user.id), roles, company_ids)
        raw_refresh, refresh_hash = create_refresh_token()
        db.add(RefreshToken(
            token_hash=refresh_hash,
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_DAYS)
        ))
        log_audit(db, user.id, "user.login", "user", user.id)
        db.commit()

        return TokenResponse(
            access_token=token,
            refresh_token=raw_refresh,
            user=UserRead(
                id=user.id,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                is_active=user.is_active,
                roles=roles,
                assigned_company_ids=company_ids
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@app.get("/auth/me", response_model=UserRead)
def get_current_user_info(user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserRead(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        roles=getattr(user, 'role_names', [])
    )

@app.post("/auth/logout")
def logout(body: Optional[LogoutRequest] = Body(default=None), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if body and body.refresh_token:
        token_hash = hash_refresh_token(body.refresh_token)
        rt = db.query(RefreshToken).filter_by(token_hash=token_hash, user_id=user.id).first()
        if rt:
            rt.revoked = True
            db.commit()
    return {"ok": True}


@app.post("/auth/refresh", response_model=TokenResponse)
def refresh_access_token(body: RefreshRequest, db: Session = Depends(get_db)):
    token_hash = hash_refresh_token(body.refresh_token)
    rt = db.query(RefreshToken).filter_by(token_hash=token_hash).first()
    if not rt or rt.revoked or rt.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    user = db.get(User, rt.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    # Rotate: revoke old, issue new pair
    rt.revoked = True
    roles = [db.get(Role, ur.role_id).name for ur in user.roles]
    company_ids = []
    if "accountant" in roles:
        company_ids = [a.company_id for a in db.query(AccountantAssignment).filter_by(accountant_user_id=user.id).all()]
    new_access = create_access_token(str(user.id), roles, company_ids)
    raw_refresh, refresh_hash = create_refresh_token()
    db.add(RefreshToken(
        token_hash=refresh_hash,
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_DAYS)
    ))
    db.commit()
    return TokenResponse(
        access_token=new_access,
        refresh_token=raw_refresh,
        user=UserRead(id=user.id, email=user.email, first_name=user.first_name, last_name=user.last_name, is_active=user.is_active, roles=roles, assigned_company_ids=company_ids)
    )

# ------------------ Users Management (Super Admin only) ------------------
@app.get("/users", response_model=list[UserRead])
def list_users(
    role: str = None, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    user: User = Depends(require_roles("super_admin"))
):
    """List users, optionally filtered by role"""
    query = db.query(User)
    
    if role:
        # Filter by role
        role_obj = db.query(Role).filter(Role.name == role).first()
        if role_obj:
            query = query.join(UserRole).filter(UserRole.role_id == role_obj.id)
        else:
            return []  # Role not found
    
    users = query.offset(skip).limit(limit).all()
    
    # Add roles to each user
    result = []
    for user_obj in users:
        user_roles = [db.get(Role, ur.role_id).name for ur in user_obj.roles]
        result.append(UserRead(
            id=user_obj.id,
            email=user_obj.email,
            first_name=user_obj.first_name,
            last_name=user_obj.last_name,
            is_active=user_obj.is_active,
            roles=user_roles
        ))
    
    return result


@app.get("/users/accountants", response_model=list[UserRead])
def list_accountants(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    user: User = Depends(require_roles("super_admin"))
):
    """List all accountant users"""
    return list_users(role="accountant", skip=skip, limit=limit, db=db, user=user)


@app.get("/users/client-admins", response_model=list[UserRead])
def list_client_admins(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    user: User = Depends(require_roles("super_admin"))
):
    """List all client admin users"""
    return list_users(role="client_admin", skip=skip, limit=limit, db=db, user=user)


@app.get("/users/employees", response_model=list[UserRead])
def list_employee_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    user: User = Depends(require_roles("super_admin"))
):
    """List all employee users"""
    return list_users(role="employee", skip=skip, limit=limit, db=db, user=user)


# ------------------ Assignment APIs (Super Admin) ------------------
@app.post("/assignments/accountant")
def assign_accountant(body: AccountantAssignRequest, db: Session = Depends(get_db), user: User = Depends(require_roles("super_admin"))):
    if not db.get(User, body.accountant_user_id) or not db.get(Company, body.company_id):
        raise HTTPException(status_code=400, detail="Invalid ids")
    db.add(AccountantAssignment(accountant_user_id=body.accountant_user_id, company_id=body.company_id))
    db.commit()
    return {"ok": True}


@app.post("/assignments/client-admin")
def assign_client_admin(body: ClientAdminAssignRequest, db: Session = Depends(get_db), user: User = Depends(require_roles("super_admin"))):
    if not db.get(User, body.user_id) or not db.get(Company, body.company_id):
        raise HTTPException(status_code=400, detail="Invalid ids")
    db.add(UserCompany(user_id=body.user_id, company_id=body.company_id))
    db.commit()
    return {"ok": True}


@app.post("/assignments/employee-link")
def link_employee(body: EmployeeLinkRequest, db: Session = Depends(get_db), user: User = Depends(require_roles("super_admin"))):
    if not db.get(User, body.user_id) or not db.get(Employee, body.employee_id):
        raise HTTPException(status_code=400, detail="Invalid ids")
    db.add(EmployeeUser(user_id=body.user_id, employee_id=body.employee_id))
    db.commit()
    return {"ok": True}


# ------------------ Companies CRUD ------------------
@app.post("/companies", response_model=CompanyRead)
def create_company(company_in: CompanyCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("super_admin", "accountant"))):
    try:
        company = Company(**company_in.model_dump(exclude_unset=True))
        db.add(company)
        db.commit()
        db.refresh(company)
        return company
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create company: {str(e)}")


@app.get("/companies", response_model=list[CompanyRead])
def list_companies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: User = Depends(require_roles("super_admin", "accountant"))):
    try:
        q = db.query(Company)
        roles = getattr(user, "role_names", [])
        if "super_admin" not in roles:
            allowed_company_ids = set()
            if "accountant" in roles:
                allowed_company_ids |= {a.company_id for a in db.query(AccountantAssignment).filter_by(accountant_user_id=user.id)}
            # TODO: remove client_admin scope after data migration is confirmed
            if "client_admin" in roles:
                allowed_company_ids |= {uc.company_id for uc in db.query(UserCompany).filter_by(user_id=user.id)}
            if not allowed_company_ids:
                return []
            q = q.filter(Company.id.in_(allowed_company_ids))
        return list(q.offset(skip).limit(limit).all())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list companies: {str(e)}")


@app.get("/companies/{company_id}", response_model=CompanyRead)
def get_company(company_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("super_admin", "accountant"))):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    roles = getattr(user, "role_names", [])
    if "super_admin" not in roles:
        allowed = False
        if "accountant" in roles and db.query(AccountantAssignment).filter_by(accountant_user_id=user.id, company_id=company_id).first():
            allowed = True
        # TODO: remove client_admin scope after data migration is confirmed
        if "client_admin" in roles and db.query(UserCompany).filter_by(user_id=user.id, company_id=company_id).first():
            allowed = True
        if not allowed:
            raise HTTPException(status_code=403, detail="Forbidden")
    return company


@app.put("/companies/{company_id}", response_model=CompanyRead)
def update_company(company_id: int, company_in: CompanyUpdate, db: Session = Depends(get_db), user: User = Depends(require_roles("super_admin", "accountant"))):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    # scope check as above
    get_company(company_id, db, user)  # will raise if not allowed
    for k, v in company_in.model_dump(exclude_unset=True).items():
        setattr(company, k, v)
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@app.delete("/companies/{company_id}", status_code=204)
def delete_company(company_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("super_admin"))):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    db.delete(company)
    db.commit()
    return None


# ------------------ Employees CRUD ------------------
@app.post("/companies/{company_id}/employees", response_model=EmployeeRead)
def create_employee(company_id: int, employee_in: EmployeeCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("super_admin", "accountant"))):
    if not db.get(Company, company_id):
        raise HTTPException(status_code=404, detail="Company not found")
    get_company(company_id, db, user)
    employee = Employee(company_id=company_id, **employee_in.model_dump(exclude_unset=True))
    db.add(employee)
    db.flush()
    log_audit(db, user.id, "employee.create", "employee", employee.id, {"name": f"{employee.first_names} {employee.last_name}", "company_id": company_id})
    db.commit()
    db.refresh(employee)
    return employee


@app.get("/companies/{company_id}/employees", response_model=list[EmployeeRead])
def list_employees(company_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: User = Depends(require_roles("super_admin", "accountant"))):
    if not db.get(Company, company_id):
        raise HTTPException(status_code=404, detail="Company not found")
    get_company(company_id, db, user)
    return list(db.query(Employee).filter(Employee.company_id == company_id).offset(skip).limit(limit).all())


@app.get("/employees/{employee_id}", response_model=EmployeeRead)
def get_employee(employee_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("super_admin", "accountant", "client_admin", "employee"))):
    employee = db.get(Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    roles = getattr(user, "role_names", [])
    if "super_admin" in roles:
        return employee
    if "employee" in roles:
        link = db.query(EmployeeUser).filter_by(user_id=user.id, employee_id=employee_id).first()
        if not link:
            raise HTTPException(status_code=403, detail="Forbidden")
        return employee
    # accountant/client_admin scope via company
    get_company(employee.company_id, db, user)
    return employee


@app.put("/employees/{employee_id}", response_model=EmployeeRead)
def update_employee(employee_id: int, employee_in: EmployeeUpdate, db: Session = Depends(get_db), user: User = Depends(require_roles("super_admin", "accountant"))):
    employee = db.get(Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    get_company(employee.company_id, db, user)
    changes = employee_in.model_dump(exclude_unset=True)
    for k, v in changes.items():
        setattr(employee, k, v)
    db.add(employee)
    log_audit(db, user.id, "employee.update", "employee", employee_id, {"fields_changed": list(changes.keys())})
    db.commit()
    db.refresh(employee)
    return employee


@app.delete("/employees/{employee_id}", status_code=204)
def delete_employee(employee_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("super_admin", "accountant"))):
    employee = db.get(Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    get_company(employee.company_id, db, user)
    log_audit(db, user.id, "employee.delete", "employee", employee_id, {"name": f"{employee.first_names} {employee.last_name}"})
    db.delete(employee)
    db.commit()
    return None


# ------------------ Payroll Preview from Employee ------------------
@app.get("/companies/{company_id}/employees/{employee_id}/payroll-preview", response_model=PayslipData)
def preview_payroll_from_employee(company_id: int, employee_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    get_company(company_id, db, user)
    employee = db.get(Employee, employee_id)
    if not employee or employee.company_id != company_id:
        raise HTTPException(status_code=404, detail="Employee not found for this company")

    today = date.today()
    start_day = date(today.year, today.month, 1)
    end_day = date(today.year, today.month, monthrange(today.year, today.month)[1])

    emp_details = EmployeeDetails(
        first_names=employee.first_names,
        last_name=employee.last_name,
        id_no=employee.id_no or "",
        employee_no=employee.employee_no or "",
        position=employee.position or "",
        tax_ref=employee.tax_ref or "",
        emp_date=employee.emp_date or start_day,
        bank_account_last4=employee.bank_account_last4 or None,
        pension_fund_name=employee.pension_fund_name or None,
        medical_aid_scheme_name=employee.medical_aid_scheme_name or None,
    )

    comp_details = CompanyDetails(
        company_name=company.name,
        company_reg_no=company.registration_number or "",
        company_address=company.address or "",
        uif_ref=company.uif_reference or "",
        phone=company.phone or "",
        email=company.email or "",
        run=f"{today.year}-{today.month:02d}"
    )

    # Map salary fields
    basic_pay = float(getattr(employee, 'basic_salary', 0.0) or 0.0)
    other_earnings = float((getattr(employee, 'housing_allowance', 0.0) or 0.0) + (getattr(employee, 'transport_allowance', 0.0) or 0.0) + (getattr(employee, 'meal_allowance', 0.0) or 0.0) + (getattr(employee, 'other_allowances', 0.0) or 0.0))
    pension = float(getattr(employee, 'pension_contribution', 0.0) or 0.0)
    medical = float(getattr(employee, 'medical_aid', 0.0) or 0.0)
    union_fees = float(getattr(employee, 'union_fees', 0.0) or 0.0)
    other_deductions = float(getattr(employee, 'other_deductions', 0.0) or 0.0)

    # Calculate
    total_earnings = basic_pay + other_earnings
    paye = monthly_paye_from_gross(total_earnings)
    uif = uif_employee(total_earnings)
    # SDL
    total_remuneration = total_earnings
    sdl_details = calculate_sdl(total_remuneration=total_remuneration, annual_payroll=0.0, excluded_amounts=0.0)
    sdl_amount = sdl_details['sdl_amount']
    total_deductions = pension + medical + union_fees + other_deductions + paye + uif
    net_pay = total_earnings - total_deductions

    earnings_list: List[Tuple[str, float]] = [("Basic Pay", basic_pay)]
    if other_earnings:
        earnings_list.append(("Allowances", other_earnings))
    deductions_list: List[Tuple[str, float]] = [("PAYE", paye), ("UIF", uif)]
    
    if pension:
        deductions_list.append(("Pension", pension))
    if medical:
        deductions_list.append(("Medical Aid", medical))
    if union_fees:
        deductions_list.append(("Union Fees", union_fees))
    if other_deductions:
        deductions_list.append(("Other Deductions", other_deductions))

    preview = PayslipData(
        employee=emp_details,
        company=comp_details,
        period_start=start_day,
        period_end=end_day,
        payment_date=today,
        earnings=earnings_list,
        total_earnings=total_earnings,
        deductions=deductions_list,
        total_deductions=total_deductions,
        net_pay=net_pay,
        paye=paye,
        uif=uif,
        sdl=sdl_amount,
        leave_income=0.0,
        sdl_details=sdl_details,
        leave_income_details=None,
    )
    return preview


# ------------------ Bulk Payroll ------------------
@app.post("/companies/{company_id}/payroll/bulk", response_model=BulkPayrollResult)
def bulk_payroll_run(
    company_id: int,
    body: BulkPayrollRequest,
    user: User = Depends(require_roles("super_admin", "accountant")),
    db: Session = Depends(get_db)
):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    get_company(company_id, db, user)

    active_employees = db.query(Employee).filter(
        Employee.company_id == company_id,
        Employee.is_active == True
    ).all()

    if not active_employees:
        raise HTTPException(status_code=400, detail="No active employees found for this company")

    _, last_day = monthrange(body.year, body.month)
    period_start = date(body.year, body.month, 1)
    period_end = date(body.year, body.month, last_day)
    period = f"{body.year}-{body.month:02d}"

    results: List[BulkPayrollEmployeeResult] = []
    for emp in active_employees:
        try:
            basic_pay = float(emp.basic_salary or 0.0)
            other_earn = float(
                (emp.housing_allowance or 0.0) + (emp.transport_allowance or 0.0) +
                (emp.meal_allowance or 0.0) + (emp.other_allowances or 0.0)
            )
            pension = float(emp.pension_contribution or 0.0)
            medical = float(emp.medical_aid or 0.0)
            union_fees = float(emp.union_fees or 0.0)
            other_ded = float(emp.other_deductions or 0.0)

            total_earnings = basic_pay + other_earn
            paye = monthly_paye_from_gross(total_earnings)
            uif = uif_employee(total_earnings)
            sdl_details = calculate_sdl(total_remuneration=total_earnings, annual_payroll=0.0, excluded_amounts=0.0)
            sdl_amount = sdl_details['sdl_amount']
            total_deductions = pension + medical + union_fees + other_ded + paye + uif
            net_pay = total_earnings - total_deductions

            db.add(PayrollRecord(
                company_id=company_id,
                employee_id=emp.id,
                payrun_month=body.month,
                payrun_year=body.year,
                payrun_period=period,
                employee_name=f"{emp.first_names} {emp.last_name}",
                employee_id_no=emp.id_no,
                pay_period_start=period_start,
                pay_period_end=period_end,
                basic_pay=basic_pay,
                other_earnings=other_earn,
                leave_income=0.0,
                total_earnings=total_earnings,
                paye=paye,
                uif_employee=uif,
                uif_employer=uif,
                sdl=sdl_amount,
                pension=pension,
                medical=medical,
                total_deductions=total_deductions,
                net_pay=net_pay,
                created_by=user.id,
                status="draft"
            ))
            results.append(BulkPayrollEmployeeResult(
                employee_id=emp.id,
                employee_name=f"{emp.first_names} {emp.last_name}",
                basic_pay=basic_pay,
                total_earnings=total_earnings,
                total_deductions=total_deductions,
                net_pay=net_pay,
                status="success"
            ))
        except Exception as e:
            results.append(BulkPayrollEmployeeResult(
                employee_id=emp.id,
                employee_name=f"{emp.first_names} {emp.last_name}",
                basic_pay=0.0, total_earnings=0.0, total_deductions=0.0, net_pay=0.0,
                status="error", error=str(e)
            ))

    try:
        successful = [r for r in results if r.status == "success"]
        log_audit(db, user.id, "payroll.bulk_run", "company", company_id, {
            "period": period, "total": len(results), "successful": len(successful)
        })
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save payroll records")

    return BulkPayrollResult(
        company_id=company_id,
        period=period,
        total_employees=len(results),
        successful=len(successful),
        failed=len(results) - len(successful),
        total_net_pay=sum(r.net_pay for r in successful),
        employees=results
    )


# ------------------ Payslip Email Distribution ------------------
@app.post("/companies/{company_id}/payroll/send-payslips")
def send_payslips(
    company_id: int,
    body: BulkPayrollRequest,
    user: User = Depends(require_roles("super_admin", "accountant")),
    db: Session = Depends(get_db)
):
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")
    smtp_from = os.environ.get("SMTP_FROM", smtp_user)

    if not smtp_host or not smtp_user:
        raise HTTPException(
            status_code=503,
            detail="Email not configured. Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM in environment variables."
        )

    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    get_company(company_id, db, user)

    period = f"{body.year}-{body.month:02d}"
    records = db.query(PayrollRecord).filter(
        PayrollRecord.company_id == company_id,
        PayrollRecord.payrun_period == period
    ).all()

    if not records:
        raise HTTPException(status_code=404, detail=f"No payroll records found for period {period}")

    sent, failed, errors = 0, 0, []

    for record in records:
        try:
            if not record.employee_id:
                errors.append(f"{record.employee_name}: No employee record linked")
                failed += 1
                continue

            link = db.query(EmployeeUser).filter_by(employee_id=record.employee_id).first()
            if not link:
                errors.append(f"{record.employee_name}: No linked user account — skipped")
                failed += 1
                continue

            linked_user = db.get(User, link.user_id)
            if not linked_user:
                errors.append(f"{record.employee_name}: Linked user not found")
                failed += 1
                continue

            emp = db.get(Employee, record.employee_id)
            emp_details = EmployeeDetails(
                first_names=emp.first_names if emp else record.employee_name,
                last_name=emp.last_name if emp else "",
                id_no=record.employee_id_no or "",
                employee_no=(emp.employee_no if emp else "") or "",
                position=(emp.position if emp else "") or "",
                tax_ref=(emp.tax_ref if emp else "") or "",
                emp_date=(emp.emp_date if emp else record.pay_period_start) or record.pay_period_start,
                bank_account_last4=(emp.bank_account_last4 if emp else None),
                pension_fund_name=(emp.pension_fund_name if emp else None),
                medical_aid_scheme_name=(emp.medical_aid_scheme_name if emp else None),
            )
            comp_details = CompanyDetails(
                company_name=company.name,
                company_reg_no=company.registration_number or "",
                company_address=company.address or "",
                uif_ref=company.uif_reference or "",
                phone=company.phone or "",
                email=company.email or "",
                run=period
            )
            _desc = record.other_earnings_description or "Other Earnings"
            earnings_list = [("Basic Pay", record.basic_pay)]
            if record.other_earnings:
                earnings_list.append((_desc, record.other_earnings))
            if record.leave_income:
                earnings_list.append(("Leave Income", record.leave_income))
            deductions_list = [("PAYE", record.paye), ("UIF", record.uif_employee), ("Pension", record.pension), ("Medical Aid", record.medical)]

            payslip = PayslipData(
                employee=emp_details, company=comp_details,
                period_start=record.pay_period_start, period_end=record.pay_period_end,
                payment_date=record.pay_period_end,
                earnings=earnings_list, total_earnings=record.total_earnings,
                deductions=deductions_list, total_deductions=record.total_deductions,
                net_pay=record.net_pay, paye=record.paye, uif=record.uif_employee,
                sdl=record.sdl, leave_income=record.leave_income,
                sdl_details={"sdl_amount": record.sdl, "sdl_applicable": True, "annual_payroll": 0, "annual_threshold": 500000, "rate": 0.01},
                leave_income_details=None,
            )
            pdf_bytes = generate_payslip_pdf(payslip.model_dump())

            msg = MIMEMultipart()
            msg['From'] = smtp_from
            msg['To'] = linked_user.email
            msg['Subject'] = f"Payslip {period} — {company.name}"
            msg.attach(MIMEText(
                f"Dear {linked_user.first_name or record.employee_name},\n\n"
                f"Please find your payslip for {period} attached.\n"
                f"Net Pay: R{record.net_pay:,.2f}\n\nRegards,\n{company.name}",
                'plain'
            ))
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(pdf_bytes)
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename=payslip_{period}.pdf')
            msg.attach(part)

            with smtplib.SMTP(smtp_host, smtp_port) as srv:
                srv.starttls()
                srv.login(smtp_user, smtp_pass)
                srv.send_message(msg)
            sent += 1
        except Exception as e:
            errors.append(f"{record.employee_name}: {str(e)}")
            failed += 1

    return {"period": period, "sent": sent, "failed": failed, "errors": errors}


# ------------------ Leave Balances ------------------
@app.get("/employees/{employee_id}/leave-balances", response_model=list[LeaveBalanceRead])
def list_leave_balances(
    employee_id: int,
    year: Optional[int] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    emp = db.get(Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    get_employee(employee_id, db, user)
    q = db.query(LeaveBalance).filter(LeaveBalance.employee_id == employee_id)
    if year:
        q = q.filter(LeaveBalance.year == year)
    return [
        LeaveBalanceRead(
            id=b.id, employee_id=b.employee_id, leave_type=b.leave_type,
            year=b.year, days_allocated=b.days_allocated, days_taken=b.days_taken,
            days_remaining=max(b.days_allocated - b.days_taken, 0.0)
        ) for b in q.all()
    ]


@app.post("/employees/{employee_id}/leave-balances", response_model=LeaveBalanceRead)
def create_leave_balance(
    employee_id: int,
    body: LeaveBalanceCreate,
    user: User = Depends(require_roles("super_admin", "accountant")),
    db: Session = Depends(get_db)
):
    emp = db.get(Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    get_company(emp.company_id, db, user)
    lb = LeaveBalance(
        employee_id=employee_id,
        leave_type=body.leave_type,
        year=body.year,
        days_allocated=body.days_allocated,
        days_taken=body.days_taken
    )
    db.add(lb)
    db.commit()
    db.refresh(lb)
    return LeaveBalanceRead(
        id=lb.id, employee_id=lb.employee_id, leave_type=lb.leave_type,
        year=lb.year, days_allocated=lb.days_allocated, days_taken=lb.days_taken,
        days_remaining=max(lb.days_allocated - lb.days_taken, 0.0)
    )


@app.put("/employees/{employee_id}/leave-balances/{balance_id}", response_model=LeaveBalanceRead)
def update_leave_balance(
    employee_id: int,
    balance_id: int,
    body: LeaveBalanceUpdate,
    user: User = Depends(require_roles("super_admin", "accountant")),
    db: Session = Depends(get_db)
):
    emp = db.get(Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    get_company(emp.company_id, db, user)
    lb = db.query(LeaveBalance).filter(LeaveBalance.id == balance_id, LeaveBalance.employee_id == employee_id).first()
    if not lb:
        raise HTTPException(status_code=404, detail="Leave balance not found")
    if body.days_allocated is not None:
        lb.days_allocated = body.days_allocated
    if body.days_taken is not None:
        lb.days_taken = body.days_taken
    db.commit()
    db.refresh(lb)
    return LeaveBalanceRead(
        id=lb.id, employee_id=lb.employee_id, leave_type=lb.leave_type,
        year=lb.year, days_allocated=lb.days_allocated, days_taken=lb.days_taken,
        days_remaining=max(lb.days_allocated - lb.days_taken, 0.0)
    )


@app.delete("/employees/{employee_id}/leave-balances/{balance_id}", status_code=204)
def delete_leave_balance(
    employee_id: int,
    balance_id: int,
    user: User = Depends(require_roles("super_admin", "accountant")),
    db: Session = Depends(get_db)
):
    emp = db.get(Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    get_company(emp.company_id, db, user)
    lb = db.query(LeaveBalance).filter(LeaveBalance.id == balance_id, LeaveBalance.employee_id == employee_id).first()
    if not lb:
        raise HTTPException(status_code=404, detail="Leave balance not found")
    db.delete(lb)
    db.commit()
    return None


# ------------------ Dashboard ------------------
@app.get("/dashboard/stats")
def get_dashboard_stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    roles = getattr(user, "role_names", [])

    if "super_admin" in roles:
        company_ids = [c.id for c in db.query(Company).all()]
    else:
        cids = set()
        if "accountant" in roles:
            cids |= {a.company_id for a in db.query(AccountantAssignment).filter_by(accountant_user_id=user.id).all()}
        # TODO: remove client_admin scope after data migration is confirmed
        if "client_admin" in roles:
            cids |= {uc.company_id for uc in db.query(UserCompany).filter_by(user_id=user.id).all()}
        company_ids = list(cids)

    all_employees = db.query(Employee).filter(Employee.company_id.in_(company_ids)).all() if company_ids else []
    active_count = sum(1 for e in all_employees if e.is_active)

    alerts = []
    for emp in all_employees:
        if not emp.is_active:
            continue
        missing = []
        if not emp.id_no:
            missing.append("ID number")
        if not emp.bank_name or not emp.account_number:
            missing.append("banking details")
        if not emp.tax_number and not emp.tax_ref:
            missing.append("tax reference")
        if missing:
            alerts.append({
                "employee_id": emp.id,
                "employee_name": f"{emp.first_names} {emp.last_name}",
                "company_id": emp.company_id,
                "missing": missing
            })

    today = date.today()
    month_records = db.query(PayrollRecord).filter(
        PayrollRecord.company_id.in_(company_ids),
        PayrollRecord.payrun_year == today.year,
        PayrollRecord.payrun_month == today.month
    ).all() if company_ids else []

    pending_count = db.query(PayrollRecord).filter(
        PayrollRecord.company_id.in_(company_ids),
        PayrollRecord.status == "submitted"
    ).count() if company_ids else 0

    recent_activity = []
    if "super_admin" in roles or "accountant" in roles or "client_admin" in roles:
        events = db.query(AuditEvent).order_by(AuditEvent.timestamp.desc()).limit(8).all()
        for e in events:
            event_user = db.get(User, e.user_id) if e.user_id else None
            recent_activity.append({
                "id": e.id,
                "action": e.action,
                "entity_type": e.entity_type,
                "entity_id": e.entity_id,
                "user_name": f"{event_user.first_name or ''} {event_user.last_name or ''}".strip() if event_user else "System",
                "timestamp": e.timestamp.isoformat()
            })

    pending_leave = 0
    pending_documents = 0
    pending_banking = 0
    if "super_admin" in roles:
        pending_leave = db.query(LeaveRequest).filter(LeaveRequest.status == "pending").count()
        pending_documents = db.query(EmployeeDocument).filter(EmployeeDocument.status == "pending").count()
        pending_banking = db.query(BankingChangeRequest).filter(BankingChangeRequest.status == "pending").count()

    return {
        "companies": len(company_ids),
        "employees": {"total": len(all_employees), "active": active_count, "inactive": len(all_employees) - active_count},
        "current_month": {
            "period": f"{today.year}-{today.month:02d}",
            "records": len(month_records),
            "total_net_pay": round(sum(r.net_pay for r in month_records), 2),
            "employees_processed": len({r.employee_id for r in month_records if r.employee_id})
        },
        "pending_approvals": pending_count,
        "pending_leave": pending_leave,
        "pending_documents": pending_documents,
        "pending_banking": pending_banking,
        "alerts": alerts[:15],
        "recent_activity": recent_activity
    }


# ------------------ Payroll Approval Workflow ------------------
@app.post("/companies/{company_id}/payroll/submit")
def submit_payroll(
    company_id: int,
    body: PayrollApprovalRequest,
    user: User = Depends(require_roles("super_admin", "accountant")),
    db: Session = Depends(get_db)
):
    get_company(company_id, db, user)
    period = f"{body.year}-{body.month:02d}"
    records = db.query(PayrollRecord).filter(
        PayrollRecord.company_id == company_id,
        PayrollRecord.payrun_period == period,
        PayrollRecord.status == "draft"
    ).all()
    if not records:
        raise HTTPException(status_code=404, detail=f"No draft payroll records found for {period}")
    for r in records:
        r.status = "submitted"
    log_audit(db, user.id, "payroll.submit", "company", company_id, {"period": period, "records": len(records)})
    db.commit()
    return {"ok": True, "submitted": len(records), "period": period}


@app.post("/companies/{company_id}/payroll/approve")
def approve_payroll(
    company_id: int,
    body: PayrollApprovalRequest,
    user: User = Depends(require_roles("super_admin")),
    db: Session = Depends(get_db)
):
    get_company(company_id, db, user)
    period = f"{body.year}-{body.month:02d}"
    records = db.query(PayrollRecord).filter(
        PayrollRecord.company_id == company_id,
        PayrollRecord.payrun_period == period,
        PayrollRecord.status == "submitted"
    ).all()
    if not records:
        raise HTTPException(status_code=404, detail=f"No submitted payroll records found for {period}")
    now = datetime.utcnow()
    for r in records:
        r.status = "approved"
        r.approved_by = user.id
        r.approved_at = now
    log_audit(db, user.id, "payroll.approve", "company", company_id, {"period": period, "records": len(records)})
    db.commit()
    return {"ok": True, "approved": len(records), "period": period}


@app.post("/companies/{company_id}/payroll/reject")
def reject_payroll(
    company_id: int,
    body: PayrollApprovalRequest,
    user: User = Depends(require_roles("super_admin")),
    db: Session = Depends(get_db)
):
    get_company(company_id, db, user)
    period = f"{body.year}-{body.month:02d}"
    records = db.query(PayrollRecord).filter(
        PayrollRecord.company_id == company_id,
        PayrollRecord.payrun_period == period,
        PayrollRecord.status == "submitted"
    ).all()
    if not records:
        raise HTTPException(status_code=404, detail=f"No submitted payroll records found for {period}")
    for r in records:
        r.status = "rejected"
        r.rejection_reason = body.reason or "No reason given"
    log_audit(db, user.id, "payroll.reject", "company", company_id, {"period": period, "reason": body.reason})
    db.commit()
    return {"ok": True, "rejected": len(records), "period": period}


@app.get("/companies/{company_id}/payroll/status")
def get_payroll_period_status(
    company_id: int,
    year: int = Query(...),
    month: int = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    get_company(company_id, db, user)
    period = f"{year}-{month:02d}"
    records = db.query(PayrollRecord).filter(
        PayrollRecord.company_id == company_id,
        PayrollRecord.payrun_period == period
    ).all()
    if not records:
        return {"period": period, "status": "none", "count": 0}
    statuses = {r.status for r in records}
    dominant = "draft" if "draft" in statuses else ("submitted" if "submitted" in statuses else ("rejected" if "rejected" in statuses else "approved"))
    return {
        "period": period,
        "status": dominant,
        "count": len(records),
        "total_net_pay": round(sum(r.net_pay for r in records), 2),
        "approved_at": next((r.approved_at.isoformat() for r in records if r.approved_at), None),
        "rejection_reason": next((r.rejection_reason for r in records if r.rejection_reason), None)
    }


# ------------------ Employee CSV Import ------------------
@app.post("/companies/{company_id}/employees/import", response_model=EmployeeImportResult)
def import_employees(
    company_id: int,
    employees_data: List[EmployeeCreate],
    user: User = Depends(require_roles("super_admin", "accountant")),
    db: Session = Depends(get_db)
):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    get_company(company_id, db, user)

    created = 0
    errors: List[str] = []
    for i, emp_data in enumerate(employees_data):
        try:
            emp = Employee(company_id=company_id, **emp_data.model_dump())
            db.add(emp)
            created += 1
        except Exception as e:
            errors.append(f"Row {i + 1} ({emp_data.first_names} {emp_data.last_name}): {str(e)}")

    try:
        log_audit(db, user.id, "employee.import", "company", company_id, {"created": created, "failed": len(errors)})
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

    return EmployeeImportResult(created=created, failed=len(errors), errors=errors)


# ------------------ Audit Log ------------------
@app.get("/audit")
def list_audit_events(
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    action: Optional[str] = Query(None),
    user: User = Depends(require_roles("super_admin", "accountant")),
    db: Session = Depends(get_db)
):
    q = db.query(AuditEvent).order_by(AuditEvent.timestamp.desc())
    if action:
        q = q.filter(AuditEvent.action == action)
    total = q.count()
    events = q.offset(offset).limit(limit).all()

    result = []
    for e in events:
        event_user = db.get(User, e.user_id) if e.user_id else None
        result.append({
            "id": e.id,
            "action": e.action,
            "entity_type": e.entity_type,
            "entity_id": e.entity_id,
            "payload": e.payload,
            "user_name": f"{event_user.first_name or ''} {event_user.last_name or ''}".strip() if event_user else "System",
            "user_email": event_user.email if event_user else None,
            "timestamp": e.timestamp.isoformat()
        })
    return {"total": total, "events": result}


# ------------------ Employee Self-Service ------------------

@app.get("/me/profile")
def get_my_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    roles = getattr(user, "role_names", [])
    employee = None
    company = None
    if "employee" in roles:
        link = db.query(EmployeeUser).filter_by(user_id=user.id).first()
        if link:
            employee = db.get(Employee, link.employee_id)
            if employee:
                company = db.get(Company, employee.company_id)
    return {
        "user": {
            "id": user.id, "email": user.email,
            "first_name": user.first_name, "last_name": user.last_name, "roles": roles
        },
        "employee": {
            "id": employee.id,
            "first_names": employee.first_names,
            "last_name": employee.last_name,
            "position": employee.position,
            "employee_no": employee.employee_no,
            "emp_date": employee.emp_date.isoformat() if employee.emp_date else None,
            "basic_salary": employee.basic_salary,
            "bank_name": employee.bank_name,
            "account_number": employee.account_number,
            "company_id": employee.company_id,
            "company_name": company.name if company else None,
        } if employee else None
    }


@app.get("/me/payslips")
def get_my_payslips(
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    link = db.query(EmployeeUser).filter_by(user_id=user.id).first()
    if not link:
        return {"total": 0, "payslips": []}
    q = db.query(PayrollRecord).filter(
        PayrollRecord.employee_id == link.employee_id
    ).order_by(PayrollRecord.payrun_year.desc(), PayrollRecord.payrun_month.desc())
    total = q.count()
    records = q.offset(offset).limit(limit).all()
    company = db.get(Company, records[0].company_id) if records else None
    return {
        "total": total,
        "payslips": [{
            "id": r.id,
            "period": r.payrun_period,
            "year": r.payrun_year,
            "month": r.payrun_month,
            "pay_period_start": r.pay_period_start.isoformat(),
            "pay_period_end": r.pay_period_end.isoformat(),
            "basic_pay": r.basic_pay,
            "total_earnings": r.total_earnings,
            "total_deductions": r.total_deductions,
            "net_pay": r.net_pay,
            "status": r.status or "approved",
            "company_name": company.name if company else "",
        } for r in records]
    }


@app.get("/me/leave")
def get_my_leave(
    year: Optional[int] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    link = db.query(EmployeeUser).filter_by(user_id=user.id).first()
    if not link:
        return {"employee_id": None, "year": year or date.today().year, "balances": [], "requests": []}
    curr_year = year or date.today().year
    balances = db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == link.employee_id,
        LeaveBalance.year == curr_year
    ).all()
    requests = db.query(LeaveRequest).filter(
        LeaveRequest.employee_id == link.employee_id
    ).order_by(LeaveRequest.created_at.desc()).limit(30).all()
    return {
        "employee_id": link.employee_id,
        "year": curr_year,
        "balances": [{
            "id": b.id, "leave_type": b.leave_type,
            "days_allocated": b.days_allocated, "days_taken": b.days_taken,
            "days_remaining": round(max(b.days_allocated - b.days_taken, 0.0), 1)
        } for b in balances],
        "requests": [{
            "id": r.id, "leave_type": r.leave_type,
            "start_date": r.start_date.isoformat(), "end_date": r.end_date.isoformat(),
            "days_requested": r.days_requested, "reason": r.reason,
            "status": r.status, "review_note": r.review_note,
            "created_at": r.created_at.isoformat()
        } for r in requests]
    }


@app.post("/me/leave/request")
def submit_leave_request(
    body: LeaveRequestCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    link = db.query(EmployeeUser).filter_by(user_id=user.id).first()
    if not link:
        raise HTTPException(status_code=400, detail="No employee profile linked to your account")
    delta = (body.end_date - body.start_date).days + 1
    if delta <= 0:
        raise HTTPException(status_code=400, detail="End date must be on or after start date")
    req = LeaveRequest(
        employee_id=link.employee_id,
        leave_type=body.leave_type,
        start_date=body.start_date,
        end_date=body.end_date,
        days_requested=float(delta),
        reason=body.reason,
        status="pending"
    )
    db.add(req)
    log_audit(db, user.id, "leave.request", "employee", link.employee_id, {"type": body.leave_type, "days": delta})
    db.commit()
    db.refresh(req)
    return {"ok": True, "id": req.id, "days_requested": req.days_requested}


@app.get("/companies/{company_id}/leave/requests")
def list_company_leave_requests(
    company_id: int,
    status: Optional[str] = Query(None),
    user: User = Depends(require_roles("super_admin", "accountant")),
    db: Session = Depends(get_db)
):
    get_company(company_id, db, user)
    emp_ids = [e.id for e in db.query(Employee).filter(Employee.company_id == company_id).all()]
    if not emp_ids:
        return []
    q = db.query(LeaveRequest).filter(LeaveRequest.employee_id.in_(emp_ids))
    if status:
        q = q.filter(LeaveRequest.status == status)
    q = q.order_by(LeaveRequest.created_at.desc())
    result = []
    for r in q.all():
        emp = db.get(Employee, r.employee_id)
        result.append({
            "id": r.id, "employee_id": r.employee_id,
            "employee_name": f"{emp.first_names} {emp.last_name}" if emp else f"Employee #{r.employee_id}",
            "leave_type": r.leave_type,
            "start_date": r.start_date.isoformat(), "end_date": r.end_date.isoformat(),
            "days_requested": r.days_requested, "reason": r.reason,
            "status": r.status, "review_note": r.review_note,
            "created_at": r.created_at.isoformat()
        })
    return result


@app.put("/leave/requests/{request_id}/review")
def review_leave_request(
    request_id: int,
    body: LeaveRequestReview,
    user: User = Depends(require_roles("super_admin")),
    db: Session = Depends(get_db)
):
    req = db.get(LeaveRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Leave request not found")
    emp = db.get(Employee, req.employee_id)
    if emp:
        get_company(emp.company_id, db, user)
    req.status = "approved" if body.approved else "rejected"
    req.reviewed_by = user.id
    req.reviewed_at = datetime.utcnow()
    req.review_note = body.note
    if body.approved:
        balance = db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == req.employee_id,
            LeaveBalance.leave_type == req.leave_type,
            LeaveBalance.year == req.start_date.year
        ).first()
        if balance:
            balance.days_taken = min(balance.days_allocated, balance.days_taken + req.days_requested)
    log_audit(db, user.id, "leave.review", "employee", req.employee_id, {"request_id": request_id, "status": req.status})
    db.commit()
    return {"ok": True, "status": req.status}


@app.get("/payroll-records/{record_id}/payslip")
def download_payslip_by_record(
    record_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.get(PayrollRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    roles = getattr(user, "role_names", [])
    if "employee" in roles and not any(r in roles for r in ("super_admin", "accountant", "client_admin")):
        link = db.query(EmployeeUser).filter_by(user_id=user.id).first()
        if not link or link.employee_id != record.employee_id:
            raise HTTPException(status_code=403, detail="Forbidden")
    else:
        get_company(record.company_id, db, user)
    company = db.get(Company, record.company_id)
    emp = db.get(Employee, record.employee_id) if record.employee_id else None
    name_parts = record.employee_name.split(" ", 1)
    emp_details = EmployeeDetails(
        first_names=emp.first_names if emp else name_parts[0],
        last_name=emp.last_name if emp else (name_parts[1] if len(name_parts) > 1 else ""),
        id_no=record.employee_id_no or "",
        employee_no=(emp.employee_no if emp else "") or "",
        position=(emp.position if emp else "") or "",
        tax_ref=(emp.tax_ref if emp else "") or "",
        emp_date=(emp.emp_date if emp else record.pay_period_start) or record.pay_period_start,
        bank_account_last4=(emp.bank_account_last4 if emp else None),
        pension_fund_name=(emp.pension_fund_name if emp else None),
        medical_aid_scheme_name=(emp.medical_aid_scheme_name if emp else None),
    )
    comp_details = CompanyDetails(
        company_name=company.name if company else "",
        company_reg_no=(company.registration_number if company else "") or "",
        company_address=(company.address if company else "") or "",
        uif_ref=(company.uif_reference if company else "") or "",
        phone=(company.phone if company else "") or "",
        email=(company.email if company else "") or "",
        run=record.payrun_period
    )
    _desc = record.other_earnings_description or "Other Earnings"
    earnings_list = [("Basic Pay", record.basic_pay)]
    if record.other_earnings:
        earnings_list.append((_desc, record.other_earnings))
    if record.leave_income:
        earnings_list.append(("Leave Income", record.leave_income))
    deductions_list = [("PAYE", record.paye), ("UIF", record.uif_employee)]
    if record.pension:
        deductions_list.append(("Pension", record.pension))
    if record.medical:
        deductions_list.append(("Medical Aid", record.medical))
    payslip = PayslipData(
        employee=emp_details, company=comp_details,
        period_start=record.pay_period_start, period_end=record.pay_period_end,
        payment_date=record.pay_period_end,
        earnings=earnings_list, total_earnings=record.total_earnings,
        deductions=deductions_list, total_deductions=record.total_deductions,
        net_pay=record.net_pay, paye=record.paye, uif=record.uif_employee,
        sdl=record.sdl, leave_income=record.leave_income or 0.0,
        sdl_details={"sdl_amount": record.sdl, "sdl_applicable": True, "annual_payroll": 0, "annual_threshold": 500000, "rate": 0.01},
        leave_income_details=None,
    )
    pdf_bytes = generate_payslip_pdf(payslip.model_dump())
    return StreamingResponse(
        io.BytesIO(pdf_bytes), media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="payslip_{record.payrun_period}.pdf"'}
    )


# ------------------ Reports & Analytics ------------------

@app.get("/reports/payroll-summary")
def payroll_summary(
    company_id: int = Query(...),
    year: int = Query(...),
    month: Optional[int] = Query(None),
    user: User = Depends(require_roles("super_admin", "accountant")),
    db: Session = Depends(get_db)
):
    get_company(company_id, db, user)
    company = db.get(Company, company_id)
    q = db.query(PayrollRecord).filter(
        PayrollRecord.company_id == company_id,
        PayrollRecord.payrun_year == year
    )
    if month:
        q = q.filter(PayrollRecord.payrun_month == month)
    records = q.order_by(PayrollRecord.payrun_month, PayrollRecord.employee_name).all()
    return {
        "company_id": company_id,
        "company_name": company.name,
        "year": year, "month": month,
        "record_count": len(records),
        "totals": {
            "total_earnings": round(sum(r.total_earnings for r in records), 2),
            "paye": round(sum(r.paye for r in records), 2),
            "uif_employee": round(sum(r.uif_employee for r in records), 2),
            "uif_employer": round(sum(r.uif_employer for r in records), 2),
            "sdl": round(sum(r.sdl for r in records), 2),
            "pension": round(sum(r.pension for r in records), 2),
            "medical": round(sum(r.medical for r in records), 2),
            "total_deductions": round(sum(r.total_deductions for r in records), 2),
            "net_pay": round(sum(r.net_pay for r in records), 2),
        },
        "records": [{
            "id": r.id, "period": r.payrun_period, "month": r.payrun_month,
            "employee_name": r.employee_name, "employee_id_no": r.employee_id_no,
            "basic_pay": r.basic_pay, "other_earnings": r.other_earnings,
            "total_earnings": r.total_earnings,
            "paye": r.paye, "uif_employee": r.uif_employee, "uif_employer": r.uif_employer,
            "sdl": r.sdl, "pension": r.pension, "medical": r.medical,
            "total_deductions": r.total_deductions, "net_pay": r.net_pay,
            "status": r.status or "approved",
        } for r in records]
    }


@app.get("/reports/analytics")
def payroll_analytics(
    company_id: int = Query(...),
    year: int = Query(...),
    user: User = Depends(require_roles("super_admin", "accountant")),
    db: Session = Depends(get_db)
):
    get_company(company_id, db, user)
    all_records = db.query(PayrollRecord).filter(
        PayrollRecord.company_id == company_id,
        PayrollRecord.payrun_year == year
    ).all()
    monthly = []
    for m in range(1, 13):
        recs = [r for r in all_records if r.payrun_month == m]
        monthly.append({
            "month": m,
            "employee_count": len({r.employee_id for r in recs if r.employee_id}),
            "total_gross": round(sum(r.total_earnings for r in recs), 2),
            "total_net": round(sum(r.net_pay for r in recs), 2),
            "total_paye": round(sum(r.paye for r in recs), 2),
            "total_sdl": round(sum(r.sdl for r in recs), 2),
        })
    from collections import defaultdict
    earner_map: dict = defaultdict(float)
    for r in all_records:
        earner_map[r.employee_name] += r.net_pay
    top_earners = sorted(earner_map.items(), key=lambda x: x[1], reverse=True)[:10]
    return {
        "company_id": company_id, "year": year,
        "monthly_trend": monthly,
        "ytd": {
            "total_gross": round(sum(r.total_earnings for r in all_records), 2),
            "total_net": round(sum(r.net_pay for r in all_records), 2),
            "total_paye": round(sum(r.paye for r in all_records), 2),
            "total_uif": round(sum(r.uif_employee for r in all_records), 2),
            "total_sdl": round(sum(r.sdl for r in all_records), 2),
        },
        "top_earners": [{"name": n, "net_pay": round(v, 2)} for n, v in top_earners]
    }


@app.get("/reports/export")
def export_payroll_csv(
    company_id: int = Query(...),
    year: int = Query(...),
    month: Optional[int] = Query(None),
    user: User = Depends(require_roles("super_admin", "accountant")),
    db: Session = Depends(get_db)
):
    import csv as csv_mod
    get_company(company_id, db, user)
    company = db.get(Company, company_id)
    q = db.query(PayrollRecord).filter(
        PayrollRecord.company_id == company_id,
        PayrollRecord.payrun_year == year
    )
    if month:
        q = q.filter(PayrollRecord.payrun_month == month)
    records = q.order_by(PayrollRecord.payrun_month, PayrollRecord.employee_name).all()
    output = io.StringIO()
    writer = csv_mod.writer(output)
    writer.writerow([
        "Period", "Employee Name", "ID Number",
        "Basic Pay", "Other Earnings", "Total Earnings",
        "PAYE", "UIF (Employee)", "UIF (Employer)", "SDL", "Pension", "Medical Aid",
        "Total Deductions", "Net Pay", "Status"
    ])
    for r in records:
        writer.writerow([
            r.payrun_period, r.employee_name, r.employee_id_no or "",
            r.basic_pay, r.other_earnings, r.total_earnings,
            r.paye, r.uif_employee, r.uif_employer, r.sdl, r.pension, r.medical,
            r.total_deductions, r.net_pay, r.status or "approved"
        ])
    output.seek(0)
    period_str = f"{year}-{month:02d}" if month else str(year)
    safe_name = (company.name if company else "payroll").replace(" ", "_")
    filename = f"payroll_{safe_name}_{period_str}.csv"
    return StreamingResponse(
        io.BytesIO(output.read().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# ------------------ Statutory Compliance (Priority 2) ------------------

@app.get("/compliance/emp201")
def emp201_report(
    company_id: int = Query(...),
    year: int = Query(...),
    month: int = Query(...),
    user: User = Depends(require_roles("super_admin", "accountant")),
    db: Session = Depends(get_db)
):
    """EMP201 monthly PAYE/UIF/SDL declaration summary for SARS."""
    get_company(company_id, db, user)
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    records = db.query(PayrollRecord).filter(
        PayrollRecord.company_id == company_id,
        PayrollRecord.payrun_year == year,
        PayrollRecord.payrun_month == month,
    ).all()

    total_paye = round(sum(r.paye for r in records), 2)
    total_uif_employee = round(sum(r.uif_employee for r in records), 2)
    total_uif_employer = round(sum(r.uif_employer for r in records), 2)
    total_uif = round(total_uif_employee + total_uif_employer, 2)
    total_sdl = round(sum(r.sdl for r in records), 2)
    total_remuneration = round(sum(r.total_earnings for r in records), 2)
    total_net = round(sum(r.net_pay for r in records), 2)
    employee_count = len({r.employee_id for r in records if r.employee_id})

    import calendar
    month_name = calendar.month_name[month]

    return {
        "period": f"{year}-{month:02d}",
        "month_name": month_name,
        "year": year,
        "month": month,
        "company": {
            "id": company.id,
            "name": company.name,
            "registration_number": company.registration_number or "",
            "uif_reference": company.uif_reference or "",
            "address": company.address or "",
        },
        "employee_count": employee_count,
        "total_remuneration": total_remuneration,
        "paye": total_paye,
        "uif_employee": total_uif_employee,
        "uif_employer": total_uif_employer,
        "uif_total": total_uif,
        "sdl": total_sdl,
        "total_liability": round(total_paye + total_uif + total_sdl, 2),
        "total_net_pay": total_net,
        "record_count": len(records),
    }


@app.get("/compliance/emp201/download")
def emp201_download(
    company_id: int = Query(...),
    year: int = Query(...),
    month: int = Query(...),
    user: User = Depends(require_roles("super_admin", "accountant")),
    db: Session = Depends(get_db)
):
    """Download EMP201 summary as CSV."""
    import csv as csv_mod, calendar
    data = emp201_report(company_id=company_id, year=year, month=month, user=user, db=db)
    output = io.StringIO()
    w = csv_mod.writer(output)
    w.writerow(["EMP201 Monthly Employer Declaration"])
    w.writerow(["Company", data["company"]["name"]])
    w.writerow(["Registration Number", data["company"]["registration_number"]])
    w.writerow(["UIF Reference", data["company"]["uif_reference"]])
    w.writerow(["Period", data["period"]])
    w.writerow(["Employees", data["employee_count"]])
    w.writerow([])
    w.writerow(["Description", "Amount (ZAR)"])
    w.writerow(["Total Remuneration", f"{data['total_remuneration']:.2f}"])
    w.writerow(["PAYE (Code 4102)", f"{data['paye']:.2f}"])
    w.writerow(["UIF — Employee (Code 4142)", f"{data['uif_employee']:.2f}"])
    w.writerow(["UIF — Employer", f"{data['uif_employer']:.2f}"])
    w.writerow(["SDL (Code 4149)", f"{data['sdl']:.2f}"])
    w.writerow(["Total Monthly Liability", f"{data['total_liability']:.2f}"])
    output.seek(0)
    safe = data["company"]["name"].replace(" ", "_")
    return StreamingResponse(
        io.BytesIO(output.read().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="EMP201_{safe}_{data["period"]}.csv"'}
    )


@app.get("/compliance/irp5/download")
def irp5_download(
    company_id: int = Query(...),
    year: int = Query(...),
    user: User = Depends(require_roles("super_admin", "accountant")),
    db: Session = Depends(get_db)
):
    """IRP5/IT3(a) annual employee tax certificates — CSV download."""
    import csv as csv_mod
    get_company(company_id, db, user)
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    records = db.query(PayrollRecord).filter(
        PayrollRecord.company_id == company_id,
        PayrollRecord.payrun_year == year,
    ).all()

    # Aggregate per employee across all months
    from collections import defaultdict
    emp_totals: dict = defaultdict(lambda: {
        "name": "", "id_no": "", "tax_ref": "",
        "code_3601": 0.0, "code_3605": 0.0, "code_4102": 0.0,
        "code_4142_emp": 0.0, "code_4142_er": 0.0, "code_4115": 0.0,
        "net_pay": 0.0, "months": 0
    })
    for r in records:
        emp = db.get(Employee, r.employee_id) if r.employee_id else None
        key = r.employee_id or r.employee_name
        d = emp_totals[key]
        d["name"] = r.employee_name
        d["id_no"] = r.employee_id_no or (emp.id_no if emp else "") or ""
        d["tax_ref"] = (emp.tax_ref or emp.tax_number if emp else "") or ""
        d["code_3601"] += r.basic_pay          # Basic salary
        d["code_3605"] += r.other_earnings     # Other income
        d["code_4102"] += r.paye               # PAYE deducted
        d["code_4142_emp"] += r.uif_employee   # UIF employee
        d["code_4142_er"] += r.uif_employer    # UIF employer
        d["code_4115"] += r.pension            # Pension
        d["net_pay"] += r.net_pay
        d["months"] += 1

    output = io.StringIO()
    w = csv_mod.writer(output)
    w.writerow([
        "Employer", company.name,
        "Registration No.", company.registration_number or "",
        "Tax Year", year
    ])
    w.writerow([])
    w.writerow([
        "Employee Name", "ID Number", "Tax Reference",
        "Code 3601 — Basic Salary", "Code 3605 — Other Income",
        "Total Remuneration",
        "Code 4102 — PAYE", "Code 4142 — UIF (Employee)",
        "UIF (Employer)", "Code 4115 — Pension", "Net Pay",
        "Months Worked"
    ])
    for d in emp_totals.values():
        total_rem = round(d["code_3601"] + d["code_3605"], 2)
        w.writerow([
            d["name"], d["id_no"], d["tax_ref"],
            f"{d['code_3601']:.2f}", f"{d['code_3605']:.2f}",
            f"{total_rem:.2f}",
            f"{d['code_4102']:.2f}", f"{d['code_4142_emp']:.2f}",
            f"{d['code_4142_er']:.2f}", f"{d['code_4115']:.2f}",
            f"{d['net_pay']:.2f}", d["months"]
        ])

    output.seek(0)
    safe = company.name.replace(" ", "_")
    return StreamingResponse(
        io.BytesIO(output.read().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="IRP5_{safe}_{year}.csv"'}
    )


@app.get("/compliance/irp5/preview")
def irp5_preview(
    company_id: int = Query(...),
    year: int = Query(...),
    user: User = Depends(require_roles("super_admin", "accountant")),
    db: Session = Depends(get_db)
):
    """IRP5 per-employee summary (JSON for frontend display)."""
    get_company(company_id, db, user)
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    records = db.query(PayrollRecord).filter(
        PayrollRecord.company_id == company_id,
        PayrollRecord.payrun_year == year,
    ).all()

    from collections import defaultdict
    emp_totals: dict = defaultdict(lambda: {
        "name": "", "id_no": "", "tax_ref": "",
        "basic_salary": 0.0, "other_income": 0.0,
        "paye": 0.0, "uif_employee": 0.0, "uif_employer": 0.0,
        "pension": 0.0, "net_pay": 0.0, "months": 0
    })
    for r in records:
        emp = db.get(Employee, r.employee_id) if r.employee_id else None
        key = r.employee_id or r.employee_name
        d = emp_totals[key]
        d["name"] = r.employee_name
        d["id_no"] = r.employee_id_no or (emp.id_no if emp else "") or ""
        d["tax_ref"] = (emp.tax_ref or emp.tax_number if emp else "") or ""
        d["basic_salary"] += r.basic_pay
        d["other_income"] += r.other_earnings
        d["paye"] += r.paye
        d["uif_employee"] += r.uif_employee
        d["uif_employer"] += r.uif_employer
        d["pension"] += r.pension
        d["net_pay"] += r.net_pay
        d["months"] += 1

    employees = []
    for d in emp_totals.values():
        total_rem = round(d["basic_salary"] + d["other_income"], 2)
        employees.append({
            "name": d["name"], "id_no": d["id_no"], "tax_ref": d["tax_ref"],
            "basic_salary": round(d["basic_salary"], 2),
            "other_income": round(d["other_income"], 2),
            "total_remuneration": total_rem,
            "paye": round(d["paye"], 2),
            "uif_employee": round(d["uif_employee"], 2),
            "uif_employer": round(d["uif_employer"], 2),
            "pension": round(d["pension"], 2),
            "net_pay": round(d["net_pay"], 2),
            "months": d["months"],
        })

    return {
        "company_id": company_id, "company_name": company.name,
        "year": year, "employee_count": len(employees),
        "totals": {
            "total_remuneration": round(sum(e["total_remuneration"] for e in employees), 2),
            "paye": round(sum(e["paye"] for e in employees), 2),
            "uif_employee": round(sum(e["uif_employee"] for e in employees), 2),
            "uif_employer": round(sum(e["uif_employer"] for e in employees), 2),
            "pension": round(sum(e["pension"] for e in employees), 2),
            "net_pay": round(sum(e["net_pay"] for e in employees), 2),
        },
        "employees": employees,
    }


@app.get("/compliance/ui19/download")
def ui19_download(
    company_id: int = Query(...),
    year: int = Query(...),
    month: int = Query(...),
    user: User = Depends(require_roles("super_admin", "accountant")),
    db: Session = Depends(get_db)
):
    """UI-19 UIF monthly declaration CSV for Department of Labour portal upload."""
    import csv as csv_mod
    get_company(company_id, db, user)
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    records = db.query(PayrollRecord).filter(
        PayrollRecord.company_id == company_id,
        PayrollRecord.payrun_year == year,
        PayrollRecord.payrun_month == month,
    ).all()

    output = io.StringIO()
    w = csv_mod.writer(output)
    # UI-19 header block
    w.writerow(["UI-19 UIF Monthly Declaration"])
    w.writerow(["Employer Name", company.name])
    w.writerow(["UIF Reference Number", company.uif_reference or ""])
    w.writerow(["Registration Number", company.registration_number or ""])
    w.writerow(["Declaration Period", f"{year}-{month:02d}"])
    w.writerow([])
    w.writerow([
        "Employee Name", "ID Number", "Income Type",
        "Gross Remuneration", "UIF Employee Contribution",
        "UIF Employer Contribution", "Total UIF"
    ])
    for r in records:
        emp = db.get(Employee, r.employee_id) if r.employee_id else None
        income_type = (emp.salary_type.capitalize() if emp and emp.salary_type else "Monthly")
        uif_total = round(r.uif_employee + r.uif_employer, 2)
        w.writerow([
            r.employee_name,
            r.employee_id_no or (emp.id_no if emp else "") or "",
            income_type,
            f"{r.total_earnings:.2f}",
            f"{r.uif_employee:.2f}",
            f"{r.uif_employer:.2f}",
            f"{uif_total:.2f}",
        ])
    # Totals row
    w.writerow([])
    w.writerow([
        "TOTALS", "", "",
        f"{round(sum(r.total_earnings for r in records), 2):.2f}",
        f"{round(sum(r.uif_employee for r in records), 2):.2f}",
        f"{round(sum(r.uif_employer for r in records), 2):.2f}",
        f"{round(sum(r.uif_employee + r.uif_employer for r in records), 2):.2f}",
    ])

    output.seek(0)
    safe = company.name.replace(" ", "_")
    return StreamingResponse(
        io.BytesIO(output.read().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="UI19_{safe}_{year}-{month:02d}.csv"'}
    )


@app.get("/compliance/eft/download")
def eft_download(
    company_id: int = Query(...),
    year: int = Query(...),
    month: int = Query(...),
    user: User = Depends(require_roles("super_admin", "accountant")),
    db: Session = Depends(get_db)
):
    """EFT batch payment file — net salaries for bank upload."""
    import csv as csv_mod
    get_company(company_id, db, user)
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    records = db.query(PayrollRecord).filter(
        PayrollRecord.company_id == company_id,
        PayrollRecord.payrun_year == year,
        PayrollRecord.payrun_month == month,
    ).all()

    if not records:
        raise HTTPException(status_code=404, detail=f"No payroll records for {year}-{month:02d}")

    output = io.StringIO()
    w = csv_mod.writer(output)
    w.writerow([
        "Account Name", "Bank Name", "Account Number", "Branch Code",
        "Account Type", "Amount", "Reference", "Payment Date"
    ])
    import calendar as cal_mod
    _, last_day = cal_mod.monthrange(year, month)
    pay_date = date(year, month, last_day).isoformat()
    period = f"{year}-{month:02d}"

    for r in records:
        emp = db.get(Employee, r.employee_id) if r.employee_id else None
        account_name = r.employee_name
        bank_name = (emp.bank_name if emp else "") or ""
        account_number = (emp.account_number if emp else "") or ""
        branch_code = (emp.branch_code if emp else "") or ""
        account_type = (emp.account_type if emp else "") or "Current"
        reference = f"Salary {period}"
        w.writerow([
            account_name, bank_name, account_number, branch_code,
            account_type, f"{r.net_pay:.2f}", reference, pay_date
        ])

    output.seek(0)
    safe = company.name.replace(" ", "_")
    return StreamingResponse(
        io.BytesIO(output.read().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="EFT_{safe}_{period}.csv"'}
    )


# ------------------ Leave Approvals (super_admin) ------------------

@app.get("/leave/pending")
def get_pending_leave_requests(
    user: User = Depends(require_roles("super_admin")),
    db: Session = Depends(get_db)
):
    """All pending leave requests across all companies."""
    requests = db.query(LeaveRequest).filter(LeaveRequest.status == "pending").order_by(LeaveRequest.created_at.asc()).all()
    result = []
    for r in requests:
        emp = db.get(Employee, r.employee_id)
        company = db.get(Company, emp.company_id) if emp else None
        result.append({
            "id": r.id,
            "employee_id": r.employee_id,
            "employee_name": f"{emp.first_names} {emp.last_name}" if emp else f"Employee #{r.employee_id}",
            "company_name": company.name if company else "—",
            "leave_type": r.leave_type,
            "start_date": r.start_date.isoformat(),
            "end_date": r.end_date.isoformat(),
            "days_requested": r.days_requested,
            "reason": r.reason,
            "created_at": r.created_at.isoformat(),
            "status": r.status,
        })
    return result


# ------------------ Employee Documents ------------------

@app.post("/me/documents")
async def upload_my_document(
    document_type: str = Form(...),
    description: str = Form(""),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    link = db.query(EmployeeUser).filter_by(user_id=user.id).first()
    if not link:
        raise HTTPException(status_code=400, detail="No employee profile linked to your account")
    raw = await file.read()
    if len(raw) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5 MB)")
    encoded = base64.b64encode(raw).decode()
    doc = EmployeeDocument(
        employee_id=link.employee_id,
        uploaded_by=user.id,
        document_type=document_type,
        description=description or None,
        file_name=file.filename or "document",
        file_data=encoded,
        file_size=len(raw),
        status="pending"
    )
    db.add(doc)
    log_audit(db, user.id, "document.upload", "employee", link.employee_id, {"type": document_type, "file": file.filename})
    db.commit()
    db.refresh(doc)
    return {"ok": True, "id": doc.id, "status": doc.status}


@app.get("/me/documents")
def get_my_documents(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    link = db.query(EmployeeUser).filter_by(user_id=user.id).first()
    if not link:
        return []
    docs = db.query(EmployeeDocument).filter(EmployeeDocument.employee_id == link.employee_id).order_by(EmployeeDocument.uploaded_at.desc()).all()
    return [{
        "id": d.id, "document_type": d.document_type, "description": d.description,
        "file_name": d.file_name, "file_size": d.file_size, "status": d.status,
        "rejection_reason": d.rejection_reason,
        "uploaded_at": d.uploaded_at.isoformat()
    } for d in docs]


@app.get("/me/documents/{doc_id}/download")
def download_my_document(doc_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    link = db.query(EmployeeUser).filter_by(user_id=user.id).first()
    if not link:
        raise HTTPException(status_code=403, detail="Forbidden")
    doc = db.get(EmployeeDocument, doc_id)
    if not doc or doc.employee_id != link.employee_id:
        raise HTTPException(status_code=404, detail="Document not found")
    raw = base64.b64decode(doc.file_data)
    return StreamingResponse(
        io.BytesIO(raw), media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{doc.file_name}"'}
    )


@app.get("/documents/pending")
def get_pending_documents(user: User = Depends(require_roles("super_admin")), db: Session = Depends(get_db)):
    docs = db.query(EmployeeDocument).filter(EmployeeDocument.status == "pending").order_by(EmployeeDocument.uploaded_at.asc()).all()
    result = []
    for d in docs:
        emp = db.get(Employee, d.employee_id)
        company = db.get(Company, emp.company_id) if emp else None
        result.append({
            "id": d.id,
            "employee_id": d.employee_id,
            "employee_name": f"{emp.first_names} {emp.last_name}" if emp else f"Employee #{d.employee_id}",
            "company_name": company.name if company else "—",
            "document_type": d.document_type,
            "description": d.description,
            "file_name": d.file_name,
            "file_size": d.file_size,
            "uploaded_at": d.uploaded_at.isoformat(),
            "status": d.status,
        })
    return result


@app.get("/documents/{doc_id}/download")
def download_document_admin(doc_id: int, user: User = Depends(require_roles("super_admin")), db: Session = Depends(get_db)):
    doc = db.get(EmployeeDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    raw = base64.b64decode(doc.file_data)
    return StreamingResponse(
        io.BytesIO(raw), media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{doc.file_name}"'}
    )


@app.patch("/documents/{doc_id}/review")
def review_document(
    doc_id: int,
    body: DocumentReviewRequest,
    user: User = Depends(require_roles("super_admin")),
    db: Session = Depends(get_db)
):
    doc = db.get(EmployeeDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if body.status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="status must be 'approved' or 'rejected'")
    doc.status = body.status
    doc.reviewed_by = user.id
    doc.reviewed_at = datetime.utcnow()
    doc.rejection_reason = body.reason if body.status == "rejected" else None
    log_audit(db, user.id, f"document.{body.status}", "employee", doc.employee_id, {"doc_id": doc_id, "reason": body.reason})
    db.commit()
    return {"ok": True, "status": doc.status}


# ------------------ Banking Change Requests ------------------

@app.post("/banking-changes")
def submit_banking_change(
    body: BankingChangeCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    link = db.query(EmployeeUser).filter_by(user_id=user.id).first()
    if not link:
        raise HTTPException(status_code=400, detail="No employee profile linked to your account")
    existing = db.query(BankingChangeRequest).filter_by(employee_id=link.employee_id, status="pending").first()
    if existing:
        raise HTTPException(status_code=400, detail="You already have a pending banking change request")
    req = BankingChangeRequest(
        employee_id=link.employee_id,
        requested_by=user.id,
        new_bank_name=body.new_bank_name,
        new_account_number=body.new_account_number,
        new_account_type=body.new_account_type,
        new_branch_code=body.new_branch_code,
        status="pending"
    )
    db.add(req)
    log_audit(db, user.id, "banking_change.request", "employee", link.employee_id, {"bank": body.new_bank_name})
    db.commit()
    db.refresh(req)
    return {"ok": True, "id": req.id}


@app.get("/banking-changes/my")
def get_my_banking_changes(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    link = db.query(EmployeeUser).filter_by(user_id=user.id).first()
    if not link:
        return []
    reqs = db.query(BankingChangeRequest).filter_by(employee_id=link.employee_id).order_by(BankingChangeRequest.requested_at.desc()).all()
    return [{
        "id": r.id, "new_bank_name": r.new_bank_name, "new_account_number": r.new_account_number,
        "new_account_type": r.new_account_type, "new_branch_code": r.new_branch_code,
        "status": r.status, "requested_at": r.requested_at.isoformat(),
        "rejection_reason": r.rejection_reason
    } for r in reqs]


@app.get("/banking-changes/pending")
def get_pending_banking_changes(user: User = Depends(require_roles("super_admin")), db: Session = Depends(get_db)):
    reqs = db.query(BankingChangeRequest).filter_by(status="pending").order_by(BankingChangeRequest.requested_at.asc()).all()
    result = []
    for r in reqs:
        emp = db.get(Employee, r.employee_id)
        company = db.get(Company, emp.company_id) if emp else None
        result.append({
            "id": r.id,
            "employee_id": r.employee_id,
            "employee_name": f"{emp.first_names} {emp.last_name}" if emp else f"Employee #{r.employee_id}",
            "company_name": company.name if company else "—",
            "current_bank_name": emp.bank_name if emp else None,
            "current_account_number": emp.account_number if emp else None,
            "current_account_type": emp.account_type if emp else None,
            "current_branch_code": emp.branch_code if emp else None,
            "new_bank_name": r.new_bank_name,
            "new_account_number": r.new_account_number,
            "new_account_type": r.new_account_type,
            "new_branch_code": r.new_branch_code,
            "status": r.status,
            "requested_at": r.requested_at.isoformat(),
        })
    return result


@app.patch("/banking-changes/{req_id}/review")
def review_banking_change(
    req_id: int,
    body: BankingChangeReviewRequest,
    user: User = Depends(require_roles("super_admin")),
    db: Session = Depends(get_db)
):
    req = db.get(BankingChangeRequest, req_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if body.status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="status must be 'approved' or 'rejected'")
    req.status = body.status
    req.reviewed_by = user.id
    req.reviewed_at = datetime.utcnow()
    req.rejection_reason = body.reason if body.status == "rejected" else None
    if body.status == "approved":
        emp = db.get(Employee, req.employee_id)
        if emp:
            emp.bank_name = req.new_bank_name or emp.bank_name
            emp.account_number = req.new_account_number or emp.account_number
            emp.account_type = req.new_account_type or emp.account_type
            emp.branch_code = req.new_branch_code or emp.branch_code
            if req.new_account_number and len(req.new_account_number) >= 4:
                emp.bank_account_last4 = req.new_account_number[-4:]
    log_audit(db, user.id, f"banking_change.{body.status}", "employee", req.employee_id, {"req_id": req_id, "reason": body.reason})
    db.commit()
    return {"ok": True, "status": req.status}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)

