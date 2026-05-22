# activation_tokens table is retained for backwards compatibility — not used in current flow.
# New accounts are created immediately active with a password set by the admin.

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import hash_password
from core.audit import log_audit
from core.guards import require_permission
from db import get_db
from orm_models import (
    AccountantAssignment,
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
    UserUpdateRequest,
)

router = APIRouter(tags=["users"])


def _user_read_simple(user_obj: User, db: Session) -> UserRead:
    user_roles = [db.get(Role, ur.role_id).name for ur in user_obj.roles]
    return UserRead(
        id=user_obj.id,
        email=user_obj.email,
        first_name=user_obj.first_name,
        last_name=user_obj.last_name,
        is_active=user_obj.is_active,
        force_password_change=False,
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
    if not body.password or not body.confirm_password:
        raise HTTPException(status_code=422, detail="Password and confirm password are required")
    if body.password != body.confirm_password:
        raise HTTPException(status_code=422, detail="Passwords do not match")

    if db.query(User).filter(User.email == body.email.lower()).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    role_obj = db.query(Role).filter(Role.name == body.role).first()
    if not role_obj:
        raise HTTPException(status_code=500, detail=f"Role '{body.role}' not seeded")

    new_user = User(
        email=body.email.lower(),
        password_hash=hash_password(body.password),
        first_name=body.first_name,
        last_name=body.last_name,
        is_active=True,
        force_password_change=False,
    )
    db.add(new_user)
    db.flush()
    db.add(UserRole(user_id=new_user.id, role_id=role_obj.id))
    log_audit(db, current_user.id, "user.created", "user", new_user.id)
    db.commit()
    return _user_read_simple(new_user, db)


@router.patch("/users/{user_id}", response_model=UserRead)
def update_user_credentials(
    user_id: int,
    body: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("CREATE_USER")),
):
    """SUPER_ADMIN: update a user's email and/or password."""
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    updated_fields = []
    if body.email is not None:
        existing = db.query(User).filter(User.email == body.email.lower()).first()
        if existing and existing.id != user_id:
            raise HTTPException(status_code=400, detail="That email is already in use")
        target.email = body.email.lower()
        updated_fields.append("email")
    if body.password is not None:
        target.password_hash = hash_password(body.password)
        updated_fields.append("password")

    if not updated_fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    log_audit(db, current_user.id, "user.credentials_updated", "user", user_id,
              {"updated_fields": updated_fields})
    db.commit()
    return _user_read_simple(target, db)


@router.post("/users/{user_id}/resend-activation")
def resend_activation(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("CREATE_USER")),
):
    # activation_tokens retained for backwards compatibility — not used in current flow.
    # This endpoint is kept to avoid 404 on old links, but returns a helpful message.
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Accounts are now created immediately active. Use 'Edit credentials' to set a new password if needed."}


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
