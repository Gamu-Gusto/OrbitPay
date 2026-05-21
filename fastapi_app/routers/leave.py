from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.audit import log_audit
from core.guards import get_current_user, require_permission
from core.leave_state_machine import assert_transition
from core.tenant import get_company
from db import get_db
from orm_models import Company, Employee, EmployeeUser, LeaveBalance, LeaveRequest, User
from schemas import (
    LeaveBalanceCreate,
    LeaveBalanceRead,
    LeaveBalanceUpdate,
    LeaveDocumentRequest,
    LeaveRequestCreate,
    LeaveRequestReview,
)

router = APIRouter(tags=["leave"])


# ------------------ Leave Balances ------------------

@router.get("/employees/{employee_id}/leave-balances", response_model=list[LeaveBalanceRead])
def list_leave_balances(
    employee_id: int,
    year: Optional[int] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = db.get(Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    roles = getattr(user, "role_names", [])
    if "super_admin" not in roles:
        if "employee" in roles:
            link = db.query(EmployeeUser).filter_by(user_id=user.id, employee_id=employee_id).first()
            if not link:
                raise HTTPException(status_code=403, detail="Forbidden")
        else:
            get_company(emp.company_id, db, user)
    q = db.query(LeaveBalance).filter(LeaveBalance.employee_id == employee_id)
    if year:
        q = q.filter(LeaveBalance.year == year)
    return [
        LeaveBalanceRead(
            id=b.id, employee_id=b.employee_id, leave_type=b.leave_type,
            year=b.year, days_allocated=b.days_allocated, days_taken=b.days_taken,
            days_remaining=max(b.days_allocated - b.days_taken, 0.0),
        )
        for b in q.all()
    ]


@router.post("/employees/{employee_id}/leave-balances", response_model=LeaveBalanceRead)
def create_leave_balance(
    employee_id: int,
    body: LeaveBalanceCreate,
    user: User = Depends(require_permission("MANAGE_LEAVE_BALANCES")),
    db: Session = Depends(get_db),
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
        days_taken=body.days_taken,
    )
    db.add(lb)
    db.commit()
    db.refresh(lb)
    return LeaveBalanceRead(
        id=lb.id, employee_id=lb.employee_id, leave_type=lb.leave_type,
        year=lb.year, days_allocated=lb.days_allocated, days_taken=lb.days_taken,
        days_remaining=max(lb.days_allocated - lb.days_taken, 0.0),
    )


@router.put("/employees/{employee_id}/leave-balances/{balance_id}", response_model=LeaveBalanceRead)
def update_leave_balance(
    employee_id: int,
    balance_id: int,
    body: LeaveBalanceUpdate,
    user: User = Depends(require_permission("MANAGE_LEAVE_BALANCES")),
    db: Session = Depends(get_db),
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
        days_remaining=max(lb.days_allocated - lb.days_taken, 0.0),
    )


@router.delete("/employees/{employee_id}/leave-balances/{balance_id}", status_code=204)
def delete_leave_balance(
    employee_id: int,
    balance_id: int,
    user: User = Depends(require_permission("MANAGE_LEAVE_BALANCES")),
    db: Session = Depends(get_db),
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


# ------------------ Leave Requests (manager) ------------------

@router.get("/companies/{company_id}/leave/requests")
def list_company_leave_requests(
    company_id: int,
    status: Optional[str] = Query(None),
    user: User = Depends(require_permission("VIEW_LEAVE_REQUESTS")),
    db: Session = Depends(get_db),
):
    get_company(company_id, db, user)
    company_employees = db.query(Employee).filter(Employee.company_id == company_id).all()
    if not company_employees:
        return []
    employees_map = {e.id: e for e in company_employees}
    emp_ids = list(employees_map)
    q = db.query(LeaveRequest).filter(LeaveRequest.employee_id.in_(emp_ids))
    if status:
        q = q.filter(LeaveRequest.status == status)
    q = q.order_by(LeaveRequest.created_at.desc())
    result = []
    for r in q.all():
        emp = employees_map.get(r.employee_id)
        result.append({
            "id": r.id, "employee_id": r.employee_id,
            "employee_name": f"{emp.first_names} {emp.last_name}" if emp else f"Employee #{r.employee_id}",
            "leave_type": r.leave_type,
            "start_date": r.start_date.isoformat(), "end_date": r.end_date.isoformat(),
            "days_requested": r.days_requested, "reason": r.reason,
            "status": r.status, "review_note": r.review_note,
            "documentation_requested_reason": r.documentation_requested_reason,
            "created_at": r.created_at.isoformat(),
        })
    return result


@router.get("/leave/pending")
def get_pending_leave_requests(
    user: User = Depends(require_permission("APPROVE_LEAVE")),
    db: Session = Depends(get_db),
):
    actionable = ("pending", "under_review", "request_documentation")
    requests = db.query(LeaveRequest).filter(LeaveRequest.status.in_(actionable)).order_by(LeaveRequest.created_at.asc()).all()
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
            "documentation_requested_reason": r.documentation_requested_reason,
        })
    return result


@router.put("/leave/requests/{request_id}/review")
def review_leave_request(
    request_id: int,
    body: LeaveRequestReview,
    user: User = Depends(require_permission("APPROVE_LEAVE")),
    db: Session = Depends(get_db),
):
    req = db.get(LeaveRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Leave request not found")
    if body.status not in ("approved", "rejected", "under_review"):
        raise HTTPException(status_code=400, detail="status must be 'approved', 'rejected', or 'under_review'")
    assert_transition(req.status, body.status)
    emp = db.get(Employee, req.employee_id)
    if emp:
        get_company(emp.company_id, db, user)
    req.status = body.status
    req.reviewed_by = user.id
    req.reviewed_at = datetime.utcnow()
    req.review_note = body.note
    if body.status == "approved":
        balance = db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == req.employee_id,
            LeaveBalance.leave_type == req.leave_type,
            LeaveBalance.year == req.start_date.year,
        ).first()
        if balance:
            balance.days_taken = min(balance.days_allocated, balance.days_taken + req.days_requested)
    log_audit(db, user.id, "leave.review", "employee", req.employee_id, {"request_id": request_id, "status": req.status}, company_id=emp.company_id if emp else None)
    db.commit()
    return {"ok": True, "status": req.status}


@router.post("/leave/requests/{request_id}/request-documents")
def request_leave_documentation(
    request_id: int,
    body: LeaveDocumentRequest,
    user: User = Depends(require_permission("REQUEST_DOCUMENTATION")),
    db: Session = Depends(get_db),
):
    req = db.get(LeaveRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Leave request not found")
    assert_transition(req.status, "request_documentation")
    emp = db.get(Employee, req.employee_id)
    if emp:
        get_company(emp.company_id, db, user)
    req.status = "request_documentation"
    req.documentation_requested_reason = body.reason
    req.reviewed_by = user.id
    req.reviewed_at = datetime.utcnow()
    log_audit(db, user.id, "leave.request_docs", "employee", req.employee_id, {"request_id": request_id, "reason": body.reason}, company_id=emp.company_id if emp else None)
    db.commit()
    return {"ok": True, "status": req.status}


# ------------------ Leave Self-Service ------------------

@router.get("/me/leave")
def get_my_leave(
    year: Optional[int] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    link = db.query(EmployeeUser).filter_by(user_id=user.id).first()
    if not link:
        return {"employee_id": None, "year": year or date.today().year, "balances": [], "requests": []}
    curr_year = year or date.today().year
    balances = db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == link.employee_id,
        LeaveBalance.year == curr_year,
    ).all()
    requests = db.query(LeaveRequest).filter(
        LeaveRequest.employee_id == link.employee_id,
    ).order_by(LeaveRequest.created_at.desc()).limit(30).all()
    return {
        "employee_id": link.employee_id,
        "year": curr_year,
        "balances": [{
            "id": b.id, "leave_type": b.leave_type,
            "days_allocated": b.days_allocated, "days_taken": b.days_taken,
            "days_remaining": round(max(b.days_allocated - b.days_taken, 0.0), 1),
        } for b in balances],
        "requests": [{
            "id": r.id, "leave_type": r.leave_type,
            "start_date": r.start_date.isoformat(), "end_date": r.end_date.isoformat(),
            "days_requested": r.days_requested, "reason": r.reason,
            "status": r.status, "review_note": r.review_note,
            "documentation_requested_reason": r.documentation_requested_reason,
            "created_at": r.created_at.isoformat(),
        } for r in requests],
    }


@router.post("/me/leave/request")
def submit_leave_request(
    body: LeaveRequestCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
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
        status="pending",
    )
    db.add(req)
    _leave_emp = db.get(Employee, link.employee_id)
    log_audit(db, user.id, "leave.request", "employee", link.employee_id, {"type": body.leave_type, "days": delta}, company_id=_leave_emp.company_id if _leave_emp else None)
    db.commit()
    db.refresh(req)
    return {"ok": True, "id": req.id, "days_requested": req.days_requested}


@router.post("/leave/requests/{request_id}/submit-documents")
def submit_leave_documents(
    request_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    link = db.query(EmployeeUser).filter_by(user_id=user.id).first()
    if not link:
        raise HTTPException(status_code=403, detail="No employee profile linked")
    req = db.get(LeaveRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Leave request not found")
    if req.employee_id != link.employee_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    assert_transition(req.status, "pending")
    req.status = "pending"
    req.documentation_requested_reason = None
    _docs_emp = db.get(Employee, req.employee_id)
    log_audit(db, user.id, "leave.docs_submitted", "employee", req.employee_id, {"request_id": request_id}, company_id=_docs_emp.company_id if _docs_emp else None)
    db.commit()
    return {"ok": True, "status": req.status}
