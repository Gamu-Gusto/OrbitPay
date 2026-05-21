from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.guards import require_permission
from db import get_db
from orm_models import AccountantAssignment, Company, Employee, EmployeeUser, Role, User, UserCompany, UserRole
from schemas import (
    AccountantAssignRequest,
    ClientAdminAssignRequest,
    EmployeeLinkRequest,
    UserRead,
)

router = APIRouter(tags=["users"])


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
    users = query.offset(skip).limit(limit).all()
    result = []
    for user_obj in users:
        user_roles = [db.get(Role, ur.role_id).name for ur in user_obj.roles]
        result.append(UserRead(
            id=user_obj.id,
            email=user_obj.email,
            first_name=user_obj.first_name,
            last_name=user_obj.last_name,
            is_active=user_obj.is_active,
            roles=user_roles,
        ))
    return result


@router.get("/users/accountants", response_model=list[UserRead])
def list_accountants(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("MANAGE_ASSIGNMENTS")),
):
    return list_users(role="accountant", skip=skip, limit=limit, db=db, user=user)


@router.get("/users/client-admins", response_model=list[UserRead])
def list_client_admins(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("MANAGE_ASSIGNMENTS")),
):
    return list_users(role="client_admin", skip=skip, limit=limit, db=db, user=user)


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


@router.post("/assignments/client-admin")
def assign_client_admin(
    body: ClientAdminAssignRequest,
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
