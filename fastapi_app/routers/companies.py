from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.guards import require_permission
from core.tenant import get_company
from db import get_db
from orm_models import AccountantAssignment, Company, User, UserCompany
from schemas import CompanyCreate, CompanyRead, CompanyUpdate

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("", response_model=CompanyRead)
def create_company(
    company_in: CompanyCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("MANAGE_COMPANIES")),
):
    try:
        company = Company(**company_in.model_dump(exclude_unset=True))
        db.add(company)
        db.commit()
        db.refresh(company)
        return company
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create company: {str(e)}")


@router.get("", response_model=list[CompanyRead])
def list_companies(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("VIEW_COMPANIES")),
):
    try:
        q = db.query(Company)
        roles = getattr(user, "role_names", [])
        if "super_admin" not in roles:
            allowed_company_ids = set()
            if "accountant" in roles:
                allowed_company_ids |= {
                    a.company_id
                    for a in db.query(AccountantAssignment).filter_by(accountant_user_id=user.id)
                }
            # TODO: remove client_admin scope after data migration is confirmed
            if "client_admin" in roles:
                allowed_company_ids |= {
                    uc.company_id for uc in db.query(UserCompany).filter_by(user_id=user.id)
                }
            if not allowed_company_ids:
                return []
            q = q.filter(Company.id.in_(allowed_company_ids))
        return list(q.offset(skip).limit(limit).all())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list companies: {str(e)}")


@router.get("/{company_id}", response_model=CompanyRead)
def get_company_route(
    company_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("VIEW_COMPANIES")),
):
    return get_company(company_id, db, user)


@router.put("/{company_id}", response_model=CompanyRead)
def update_company(
    company_id: int,
    company_in: CompanyUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("MANAGE_COMPANIES")),
):
    company = get_company(company_id, db, user)
    for k, v in company_in.model_dump(exclude_unset=True).items():
        setattr(company, k, v)
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.delete("/{company_id}", status_code=204)
def delete_company(
    company_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("DELETE_COMPANY")),
):
    company = get_company(company_id, db, user)
    db.delete(company)
    db.commit()
    return None
