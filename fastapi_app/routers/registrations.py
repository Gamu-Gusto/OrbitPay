import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.audit import log_audit
from core.email import (
    send_registration_approved_email,
    send_registration_rejected_email,
)
from core.guards import require_permission
from db import get_db
from orm_models import (
    AccountantRegistrationRequest,
    Role,
    User,
    UserRole,
)
from schemas import (
    AccountantRegistrationRead,
    AccountantRegistrationReview,
)

router = APIRouter(tags=["registrations"])


@router.post("/auth/register/accountant", status_code=410)
def register_accountant():
    raise HTTPException(
        status_code=410,
        detail="Registration is not available. Contact your administrator.",
    )


@router.get("/accountant-registrations", response_model=list[AccountantRegistrationRead])
def list_registrations(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("CREATE_USER")),
):
    regs = db.query(AccountantRegistrationRequest).order_by(
        AccountantRegistrationRequest.requested_at.desc()
    ).all()
    return [
        AccountantRegistrationRead(
            id=r.id,
            full_name=r.full_name,
            email=r.email,
            firm_name=r.firm_name,
            phone=r.phone,
            status=r.status,
            rejection_reason=r.rejection_reason,
            requested_at=r.requested_at.isoformat(),
        )
        for r in regs
    ]


@router.get("/accountant-registrations/pending-count")
def pending_count(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("CREATE_USER")),
):
    count = db.query(AccountantRegistrationRequest).filter(
        AccountantRegistrationRequest.status == "pending"
    ).count()
    return {"count": count}


@router.patch("/accountant-registrations/{reg_id}/review")
def review_registration(
    reg_id: int,
    body: AccountantRegistrationReview,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("CREATE_USER")),
):
    reg = db.get(AccountantRegistrationRequest, reg_id)
    if not reg:
        raise HTTPException(status_code=404, detail="Registration not found")
    if reg.status != "pending":
        raise HTTPException(status_code=400, detail="Registration already reviewed")

    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    status = body.status.lower()

    if status == "approved":
        if db.query(User).filter(User.email == reg.email).first():
            raise HTTPException(status_code=400, detail="Email already registered as a user")

        accountant_role = db.query(Role).filter(Role.name == "accountant").first()
        if not accountant_role:
            raise HTTPException(status_code=500, detail="Accountant role not found")

        name_parts = reg.full_name.strip().split(" ", 1)
        new_user = User(
            email=reg.email,
            password_hash=reg.password_hash,
            first_name=name_parts[0],
            last_name=name_parts[1] if len(name_parts) > 1 else None,
            is_active=True,
            force_password_change=False,
        )
        db.add(new_user)
        db.flush()
        db.add(UserRole(user_id=new_user.id, role_id=accountant_role.id))

        reg.status = "approved"
        reg.reviewed_by = user.id
        reg.reviewed_at = datetime.utcnow()

        log_audit(db, user.id, "accountant_registration.approved", "accountant_registration", reg.id)
        db.commit()

        try:
            send_registration_approved_email(reg.email, reg.full_name, frontend_url)
        except Exception:
            pass

        return {"ok": True, "message": f"Account created for {reg.full_name}"}

    elif status == "rejected":
        if not body.reason:
            raise HTTPException(status_code=400, detail="Rejection reason is required")
        reg.status = "rejected"
        reg.rejection_reason = body.reason
        reg.reviewed_by = user.id
        reg.reviewed_at = datetime.utcnow()

        log_audit(db, user.id, "accountant_registration.rejected", "accountant_registration", reg.id)
        db.commit()

        try:
            send_registration_rejected_email(reg.email, reg.full_name, body.reason)
        except Exception:
            pass

        return {"ok": True}

    else:
        raise HTTPException(status_code=400, detail="status must be 'approved' or 'rejected'")
