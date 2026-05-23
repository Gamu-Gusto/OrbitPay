"""
Employee portal self-service endpoints.
All routes are scoped to the authenticated user's linked employee — the
client never supplies an employee_id. Any call without a linked employee
returns 403.
"""

import base64
import io
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session

from core.guards import get_current_user
from db import get_db
from orm_models import (
    Announcement,
    BankingChangeRequest,
    Company,
    EmergencyContact,
    Employee,
    EmployeeDocument,
    EmployeeTask,
    EmployeeUser,
    LeaveBalance,
    LeaveRequest,
    PayrollRecord,
    PolicyDocument,
    User,
)
from schemas import (
    EmergencyContactCreate,
    EmergencyContactRead,
    EmergencyContactUpdate,
    EmployeeProfileUpdate,
)

router = APIRouter(prefix="/portal", tags=["portal"])

# ── SA public holidays (hardcoded for 2025–2026) ──────────────────────────
# TODO: make data-driven (DB table) when Tier 2 features are built.
_SA_HOLIDAYS: list[tuple[date, str]] = [
    # 2025
    (date(2025, 1, 1),  "New Year's Day"),
    (date(2025, 3, 21), "Human Rights Day"),
    (date(2025, 4, 18), "Good Friday"),
    (date(2025, 4, 21), "Family Day"),
    (date(2025, 4, 27), "Freedom Day"),
    (date(2025, 5, 1),  "Workers' Day"),
    (date(2025, 6, 16), "Youth Day"),
    (date(2025, 8, 9),  "National Women's Day"),
    (date(2025, 9, 24), "Heritage Day"),
    (date(2025, 12, 16), "Day of Reconciliation"),
    (date(2025, 12, 25), "Christmas Day"),
    (date(2025, 12, 26), "Day of Goodwill"),
    # 2026
    (date(2026, 1, 1),  "New Year's Day"),
    (date(2026, 3, 23), "Human Rights Day (observed)"),   # 21 Mar is Saturday
    (date(2026, 4, 3),  "Good Friday"),
    (date(2026, 4, 6),  "Family Day"),
    (date(2026, 4, 27), "Freedom Day"),
    (date(2026, 5, 1),  "Workers' Day"),
    (date(2026, 6, 16), "Youth Day"),
    (date(2026, 8, 10), "National Women's Day (observed)"),  # 9 Aug is Sunday
    (date(2026, 9, 24), "Heritage Day"),
    (date(2026, 12, 16), "Day of Reconciliation"),
    (date(2026, 12, 25), "Christmas Day"),
    (date(2026, 12, 28), "Day of Goodwill (observed)"),   # 26 Dec is Saturday
]

_ALLOWED_PROFILE_PIC_TYPES = {"image/jpeg", "image/png", "image/jpg"}
_ALLOWED_POLICY_DOC_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


# ── Helpers ───────────────────────────────────────────────────────────────

def _require_employee(user: User, db: Session) -> Employee:
    """Return the Employee linked to this user; 403 if not linked."""
    link = db.query(EmployeeUser).filter_by(user_id=user.id).first()
    if not link:
        raise HTTPException(status_code=403, detail="No employee profile linked to your account")
    emp = db.get(Employee, link.employee_id)
    if not emp:
        raise HTTPException(status_code=403, detail="Employee record not found")
    return emp


def _upcoming_holidays(n: int = 3) -> list[dict]:
    today = date.today()
    future = sorted(
        [(d, name) for d, name in _SA_HOLIDAYS if d >= today],
        key=lambda x: x[0],
    )
    return [
        {"date": d.isoformat(), "name": name, "days_away": (d - today).days}
        for d, name in future[:n]
    ]


# ── Dashboard summary — single aggregation call ───────────────────────────

# TODO: cache this with Redis when budget allows
# Suggested TTL: 60s for leave balances, 300s for company-level aggregates
@router.get("/dashboard-summary")
def dashboard_summary(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _require_employee(user, db)
    company = db.get(Company, emp.company_id)
    today = date.today()

    # Leave balances (current year)
    balances = db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == emp.id,
        LeaveBalance.year == today.year,
    ).all()
    leave_balances = [
        {
            "id": b.id,
            "leave_type": b.leave_type,
            "days_allocated": b.days_allocated,
            "days_taken": b.days_taken,
            "days_remaining": round(max(b.days_allocated - b.days_taken, 0.0), 1),
        }
        for b in balances
    ]

    # Recent payslips (last 3, distributed only)
    payslip_rows = (
        db.query(PayrollRecord)
        .filter(PayrollRecord.employee_id == emp.id, PayrollRecord.distributed == True)
        .order_by(PayrollRecord.payrun_year.desc(), PayrollRecord.payrun_month.desc())
        .limit(3)
        .all()
    )
    recent_payslips = [
        {
            "id": r.id,
            "period": r.payrun_period,
            "net_pay": r.net_pay,
            "total_earnings": r.total_earnings,
            "total_deductions": r.total_deductions,
        }
        for r in payslip_rows
    ]

    # Pending counts
    pending_counts = {
        "leave": db.query(LeaveRequest).filter(
            LeaveRequest.employee_id == emp.id, LeaveRequest.status == "pending"
        ).count(),
        "documents": db.query(EmployeeDocument).filter(
            EmployeeDocument.employee_id == emp.id, EmployeeDocument.status == "pending"
        ).count(),
        "banking": db.query(BankingChangeRequest).filter(
            BankingChangeRequest.employee_id == emp.id, BankingChangeRequest.status == "pending"
        ).count(),
    }

    # Latest 3 active announcements for the employee's company
    ann_rows = (
        db.query(Announcement)
        .filter(
            Announcement.company_id == emp.company_id,
            Announcement.is_active == True,
        )
        .order_by(Announcement.created_at.desc())
        .limit(3)
        .all()
    )
    announcements = [
        {
            "id": a.id,
            "title": a.title,
            "body": a.body,
            "created_at": a.created_at.isoformat(),
        }
        for a in ann_rows
    ]

    # Pending (incomplete) tasks for this employee
    task_rows = (
        db.query(EmployeeTask)
        .filter(
            EmployeeTask.employee_id == emp.id,
            EmployeeTask.is_complete == False,
        )
        .order_by(EmployeeTask.created_at.asc())
        .all()
    )
    pending_tasks = [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "due_date": t.due_date.isoformat() if t.due_date else None,
        }
        for t in task_rows
    ]

    # Tenure
    years_employed = months_employed = None
    if emp.emp_date:
        delta_days = (today - emp.emp_date).days
        years_employed = delta_days // 365
        months_employed = (delta_days % 365) // 30

    return {
        "employee": {
            "id": emp.id,
            "first_names": emp.first_names,
            "last_name": emp.last_name,
            "position": emp.position,
            "employee_no": emp.employee_no,
            "department": emp.department,
            "reporting_manager": emp.reporting_manager,
            "emp_date": emp.emp_date.isoformat() if emp.emp_date else None,
            "years_employed": years_employed,
            "months_employed": months_employed,
            "company_name": company.name if company else None,
            "profile_picture_data": emp.profile_picture_data,
        },
        "leave_balances": leave_balances,
        "recent_payslips": recent_payslips,
        "pending_counts": pending_counts,
        "upcoming_holidays": _upcoming_holidays(3),
        "announcements": announcements,
        "pending_tasks": pending_tasks,
    }


# ── Payslips ──────────────────────────────────────────────────────────────

@router.get("/payslips")
def get_portal_payslips(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _require_employee(user, db)
    records = (
        db.query(PayrollRecord)
        .filter(PayrollRecord.employee_id == emp.id, PayrollRecord.distributed == True)
        .order_by(PayrollRecord.payrun_year.desc(), PayrollRecord.payrun_month.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "period": r.payrun_period,
            "year": r.payrun_year,
            "month": r.payrun_month,
            "basic_pay": r.basic_pay,
            "total_earnings": r.total_earnings,
            "total_deductions": r.total_deductions,
            "net_pay": r.net_pay,
            "published_at": r.distributed_at.isoformat() if r.distributed_at else None,
        }
        for r in records
    ]


# ── Tax documents ─────────────────────────────────────────────────────────

@router.get("/tax-documents")
def get_portal_tax_documents(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # IRP5/IT3(a) documents are currently generated on-demand by admins and
    # not stored per-employee. Return empty list with a stable contract.
    # TODO: link admin IRP5 generation to a tax_documents table per employee.
    _require_employee(user, db)
    return []


# ── Profile ───────────────────────────────────────────────────────────────

@router.get("/profile")
def get_portal_profile(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _require_employee(user, db)
    company = db.get(Company, emp.company_id)
    return {
        "id": emp.id,
        "first_names": emp.first_names,
        "last_name": emp.last_name,
        "employee_no": emp.employee_no,
        "position": emp.position,
        "department": emp.department,
        "employment_type": emp.employment_type,
        "reporting_manager": emp.reporting_manager,
        "emp_date": emp.emp_date.isoformat() if emp.emp_date else None,
        "id_no": emp.id_no,
        "tax_number": emp.tax_number,
        "tax_ref": emp.tax_ref,
        "date_of_birth": emp.date_of_birth.isoformat() if emp.date_of_birth else None,
        "phone": emp.phone,
        "personal_email": emp.personal_email,
        "address_street": emp.address_street,
        "address_city": emp.address_city,
        "address_province": emp.address_province,
        "address_postal_code": emp.address_postal_code,
        "bank_name": emp.bank_name,
        "account_type": emp.account_type,
        "branch_code": emp.branch_code,
        "bank_account_last4": emp.bank_account_last4,
        "company_name": company.name if company else None,
        "company_id": emp.company_id,
        "profile_picture_data": emp.profile_picture_data,
    }


# Fields that employees are NOT allowed to edit (admin-only)
_READONLY_FIELDS = {
    "id_no", "employee_no", "emp_date", "basic_salary", "position",
    "company_id", "department", "date_of_birth",
}


@router.patch("/profile")
def update_portal_profile(
    body: EmployeeProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _require_employee(user, db)
    changes = body.model_dump(exclude_unset=True)
    # Guard read-only fields — belt-and-suspenders on top of schema
    blocked = _READONLY_FIELDS & set(changes.keys())
    if blocked:
        raise HTTPException(status_code=403, detail=f"Fields not editable by employees: {blocked}")
    for k, v in changes.items():
        setattr(emp, k, v)
    db.commit()
    db.refresh(emp)
    return {"ok": True}


@router.post("/profile-picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _require_employee(user, db)
    content_type = file.content_type or ""
    if content_type not in _ALLOWED_PROFILE_PIC_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG and PNG files are accepted")
    raw = await file.read()
    if len(raw) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Profile picture must be under 2 MB")
    emp.profile_picture_data = base64.b64encode(raw).decode()
    db.commit()
    return {"ok": True}


# ── Emergency contacts ────────────────────────────────────────────────────

@router.get("/emergency-contacts", response_model=list[EmergencyContactRead])
def get_emergency_contacts(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _require_employee(user, db)
    contacts = (
        db.query(EmergencyContact)
        .filter(EmergencyContact.employee_id == emp.id)
        .order_by(EmergencyContact.is_primary.desc(), EmergencyContact.id.asc())
        .all()
    )
    return contacts


@router.post("/emergency-contacts", response_model=EmergencyContactRead)
def add_emergency_contact(
    body: EmergencyContactCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _require_employee(user, db)
    if body.is_primary:
        # Clear existing primary flag
        db.query(EmergencyContact).filter_by(employee_id=emp.id, is_primary=True).update({"is_primary": False})
    contact = EmergencyContact(
        employee_id=emp.id,
        full_name=body.full_name,
        relationship=body.relationship,
        phone=body.phone,
        email=body.email,
        is_primary=body.is_primary,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@router.patch("/emergency-contacts/{contact_id}", response_model=EmergencyContactRead)
def update_emergency_contact(
    contact_id: int,
    body: EmergencyContactUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _require_employee(user, db)
    contact = db.get(EmergencyContact, contact_id)
    if not contact or contact.employee_id != emp.id:
        raise HTTPException(status_code=404, detail="Contact not found")
    changes = body.model_dump(exclude_unset=True)
    if changes.get("is_primary"):
        db.query(EmergencyContact).filter_by(employee_id=emp.id, is_primary=True).update({"is_primary": False})
    for k, v in changes.items():
        setattr(contact, k, v)
    db.commit()
    db.refresh(contact)
    return contact


@router.delete("/emergency-contacts/{contact_id}", status_code=204)
def delete_emergency_contact(
    contact_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _require_employee(user, db)
    contact = db.get(EmergencyContact, contact_id)
    if not contact or contact.employee_id != emp.id:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.delete(contact)
    db.commit()
    return None


# ── Announcements (employee read) ─────────────────────────────────────────

@router.get("/announcements")
def get_portal_announcements(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _require_employee(user, db)
    items = (
        db.query(Announcement)
        .filter(
            Announcement.company_id == emp.company_id,
            Announcement.is_active == True,
        )
        .order_by(Announcement.created_at.desc())
        .limit(10)
        .all()
    )
    return JSONResponse(
        content=[
            {
                "id": a.id,
                "title": a.title,
                "body": a.body,
                "created_at": a.created_at.isoformat(),
            }
            for a in items
        ],
        headers={"Cache-Control": "public, max-age=300"},
    )


# ── Policy documents (employee read) ─────────────────────────────────────

@router.get("/policy-documents")
def get_portal_policy_documents(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _require_employee(user, db)
    docs = (
        db.query(PolicyDocument)
        .filter(
            PolicyDocument.company_id == emp.company_id,
            PolicyDocument.is_active == True,
        )
        .order_by(PolicyDocument.uploaded_at.desc())
        .all()
    )
    return JSONResponse(
        content=[
            {
                "id": d.id,
                "title": d.title,
                "description": d.description,
                "file_name": d.file_name,
                "file_size": d.file_size,
                "uploaded_at": d.uploaded_at.isoformat(),
            }
            for d in docs
        ],
        headers={"Cache-Control": "public, max-age=600"},
    )


@router.get("/policy-documents/{doc_id}/download")
def download_policy_document(
    doc_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _require_employee(user, db)
    doc = db.get(PolicyDocument, doc_id)
    if not doc or doc.company_id != emp.company_id or not doc.is_active:
        raise HTTPException(status_code=404, detail="Document not found")
    raw = base64.b64decode(doc.file_data)
    return StreamingResponse(
        io.BytesIO(raw),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{doc.file_name}"'},
    )


# ── Tasks ─────────────────────────────────────────────────────────────────

@router.get("/tasks")
def get_portal_tasks(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _require_employee(user, db)
    tasks = (
        db.query(EmployeeTask)
        .filter(EmployeeTask.employee_id == emp.id)
        .order_by(EmployeeTask.is_complete.asc(), EmployeeTask.created_at.asc())
        .all()
    )
    return [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "is_complete": t.is_complete,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
        }
        for t in tasks
    ]


@router.patch("/tasks/{task_id}/complete")
def complete_task(
    task_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _require_employee(user, db)
    task = db.get(EmployeeTask, task_id)
    if not task or task.employee_id != emp.id:
        raise HTTPException(status_code=404, detail="Task not found")
    task.is_complete = True
    task.completed_at = datetime.utcnow()
    db.commit()
    return {"ok": True}
