import os
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import hash_password, hash_refresh_token
from core.audit import log_audit
from core.email import send_activation_email, send_welcome_email
from core.guards import require_permission
from db import get_db
from orm_models import (
    AccountantAssignment,
    ActivationToken,
    Company,
    Employee,
    EmployeeUser,
    Role,
    User,
    UserCompany,
    UserRole,
)
from schemas import (
    AccountantAssignRequest,
    EmployeeLinkRequest,
    ManagerAssignRequest,
    UserCreateRequest,
    UserRead,
)

router = APIRouter(tags=["users"])

ACTIVATION_TOKEN_HOURS = 72


def _user_read_simple(user_obj: User, db: Session) -> UserRead:
    user_roles = [db.get(Role, ur.role_id).name for ur in user_obj.roles]
    return UserRead(
        id=user_obj.id,
        email=user_obj.email,
        first_name=user_obj.first_name,
        last_name=user_obj.last_name,
        is_active=user_obj.is_active,
        force_password_change=bool(getattr(user_obj, "force_password_change", False)),
        roles=user_roles,
    )


@router.get("/users", response_model=list[UserRead])
def list_users(
    role: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("CREATE_USER")),
):
    query = db.query(User)
    if role:
        role_obj = db.query(Role).filter(Role.name == role).first()
        if role_obj:
            query = query.join(UserRole).filter(UserRole.role_id == role_obj.id)
        else:
            return []
    return [_user_read_simple(u, db) for u in query.offset(skip).limit(limit).all()]


@router.post("/users", response_model=UserRead, status_code=201)
def create_user(
    body: UserCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("CREATE_USER")),
):
    allowed_roles = {"super_admin", "accountant", "manager"}
    current_roles = {db.get(Role, ur.role_id).name for ur in current_user.roles}
    if body.role not in allowed_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {', '.join(sorted(allowed_roles))}")
    if body.role == "super_admin" and "super_admin" not in current_roles:
        raise HTTPException(status_code=403, detail="Only Super Admin can create Super Admin accounts")

    if db.query(User).filter(User.email == body.email.lower()).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    role_obj = db.query(Role).filter(Role.name == body.role).first()
    if not role_obj:
        raise HTTPException(status_code=500, detail=f"Role '{body.role}' not seeded")

    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    warning = None

    if body.role in ("accountant", "manager"):
        new_user = User(
            email=body.email.lower(),
            password_hash="!",  # placeholder — not valid bcrypt, login will fail until activated
            first_name=body.first_name,
            last_name=body.last_name,
            is_active=False,
            force_password_change=False,
        )
        db.add(new_user)
        db.flush()
        db.add(UserRole(user_id=new_user.id, role_id=role_obj.id))

        raw_token = secrets.token_urlsafe(32)
        token_hash = hash_refresh_token(raw_token)
        db.add(ActivationToken(
            user_id=new_user.id,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(hours=ACTIVATION_TOKEN_HOURS),
        ))
        log_audit(db, current_user.id, "user.created", "user", new_user.id)
        db.commit()

        activation_link = f"{frontend_url}/activate?token={raw_token}"
        try:
            send_activation_email(new_user.email, f"{body.first_name} {body.last_name}",
                                  body.role.capitalize(), activation_link)
        except Exception:
            warning = "User created but activation email failed. Use resend-activation to retry."

    else:  # super_admin
        if not body.password or not body.confirm_password:
            raise HTTPException(status_code=422, detail="Password is required for Super Admin accounts")
        if body.password != body.confirm_password:
            raise HTTPException(status_code=422, detail="Passwords do not match")

        new_user = User(
            email=body.email.lower(),
            password_hash=hash_password(body.password),
            first_name=body.first_name,
            last_name=body.last_name,
            is_active=True,
            force_password_change=True,
        )
        db.add(new_user)
        db.flush()
        db.add(UserRole(user_id=new_user.id, role_id=role_obj.id))
        log_audit(db, current_user.id, "user.created", "user", new_user.id)
        db.commit()

        try:
            send_welcome_email(new_user.email, f"{body.first_name} {body.last_name}",
                               body.password, frontend_url)
        except Exception:
            warning = "User created but welcome email failed to send."

    result = _user_read_simple(new_user, db)
    if warning:
        # Attach warning via response header approach — return dict instead
        return result
    return result


@router.post("/users/{user_id}/resend-activation")
def resend_activation(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("CREATE_USER")),
):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.is_active:
        raise HTTPException(status_code=400, detail="User is already active")

    # Invalidate existing tokens
    db.query(ActivationToken).filter(
        ActivationToken.user_id == user_id,
        ActivationToken.used_at.is_(None),
    ).update({"used_at": datetime.utcnow()})

    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_refresh_token(raw_token)
    db.add(ActivationToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(hours=ACTIVATION_TOKEN_HOURS),
    ))
    db.commit()

    roles = [db.get(Role, ur.role_id).name for ur in target.roles]
    role_display = roles[0].capitalize() if roles else "User"
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    activation_link = f"{frontend_url}/activate?token={raw_token}"
    try:
        send_activation_email(target.email, f"{target.first_name or ''} {target.last_name or ''}".strip(),
                              role_display, activation_link)
    except Exception:
        return {"message": "Activation email failed to send. Token was reset — try again.", "warning": True}

    return {"message": "Activation email resent."}


@router.get("/users/accountants", response_model=list[UserRead])
def list_accountants(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("MANAGE_ASSIGNMENTS")),
):
    return list_users(role="accountant", skip=skip, limit=limit, db=db, user=user)


@router.get("/users/managers", response_model=list[UserRead])
def list_managers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("MANAGE_ASSIGNMENTS")),
):
    return list_users(role="manager", skip=skip, limit=limit, db=db, user=user)


@router.get("/users/employees", response_model=list[UserRead])
def list_employee_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("MANAGE_ASSIGNMENTS")),
):
    return list_users(role="employee", skip=skip, limit=limit, db=db, user=user)


@router.post("/assignments/accountant")
def assign_accountant(
    body: AccountantAssignRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("ASSIGN_ACCOUNTANTS")),
):
    if not db.get(User, body.accountant_user_id) or not db.get(Company, body.company_id):
        raise HTTPException(status_code=400, detail="Invalid ids")
    db.add(AccountantAssignment(accountant_user_id=body.accountant_user_id, company_id=body.company_id))
    db.commit()
    return {"ok": True}


@router.post("/assignments/manager")
def assign_manager(
    body: ManagerAssignRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("MANAGE_ASSIGNMENTS")),
):
    if not db.get(User, body.user_id) or not db.get(Company, body.company_id):
        raise HTTPException(status_code=400, detail="Invalid ids")
    db.add(UserCompany(user_id=body.user_id, company_id=body.company_id))
    db.commit()
    return {"ok": True}


@router.post("/assignments/employee-link")
def link_employee(
    body: EmployeeLinkRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("MANAGE_ASSIGNMENTS")),
):
    if not db.get(User, body.user_id) or not db.get(Employee, body.employee_id):
        raise HTTPException(status_code=400, detail="Invalid ids")
    db.add(EmployeeUser(user_id=body.user_id, employee_id=body.employee_id))
    db.commit()
    return {"ok": True}
