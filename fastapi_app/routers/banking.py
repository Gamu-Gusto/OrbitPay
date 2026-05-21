from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.audit import log_audit
from core.guards import get_current_user, require_permission
from db import get_db
from orm_models import BankingChangeRequest, Company, Employee, EmployeeUser, User
from schemas import BankingChangeCreate, BankingChangeReviewRequest

router = APIRouter(tags=["banking"])


@router.post("/banking-changes")
def submit_banking_change(
    body: BankingChangeCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
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
        status="pending",
    )
    db.add(req)
    _bc_emp = db.get(Employee, link.employee_id)
    log_audit(db, user.id, "banking_change.request", "employee", link.employee_id, {"bank": body.new_bank_name}, company_id=_bc_emp.company_id if _bc_emp else None)
    db.commit()
    db.refresh(req)
    return {"ok": True, "id": req.id}


@router.get("/banking-changes/my")
def get_my_banking_changes(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    link = db.query(EmployeeUser).filter_by(user_id=user.id).first()
    if not link:
        return []
    reqs = db.query(BankingChangeRequest).filter_by(employee_id=link.employee_id).order_by(BankingChangeRequest.requested_at.desc()).all()
    return [{
        "id": r.id, "new_bank_name": r.new_bank_name, "new_account_number": r.new_account_number,
        "new_account_type": r.new_account_type, "new_branch_code": r.new_branch_code,
        "status": r.status, "requested_at": r.requested_at.isoformat(),
        "rejection_reason": r.rejection_reason,
    } for r in reqs]


@router.get("/banking-changes/pending")
def get_pending_banking_changes(user: User = Depends(require_permission("VIEW_BANKING")), db: Session = Depends(get_db)):
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


@router.patch("/banking-changes/{req_id}/review")
def review_banking_change(
    req_id: int,
    body: BankingChangeReviewRequest,
    user: User = Depends(require_permission("APPROVE_BANKING")),
    db: Session = Depends(get_db),
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
    _bc_review_emp = db.get(Employee, req.employee_id)
    if body.status == "approved" and _bc_review_emp:
        _bc_review_emp.bank_name = req.new_bank_name or _bc_review_emp.bank_name
        _bc_review_emp.account_number = req.new_account_number or _bc_review_emp.account_number
        _bc_review_emp.account_type = req.new_account_type or _bc_review_emp.account_type
        _bc_review_emp.branch_code = req.new_branch_code or _bc_review_emp.branch_code
        if req.new_account_number and len(req.new_account_number) >= 4:
            _bc_review_emp.bank_account_last4 = req.new_account_number[-4:]
    log_audit(db, user.id, f"banking_change.{body.status}", "employee", req.employee_id, {"req_id": req_id, "reason": body.reason}, company_id=_bc_review_emp.company_id if _bc_review_emp else None)
    db.commit()
    return {"ok": True, "status": req.status}
