from fastapi import HTTPException
from sqlalchemy.orm import Session

from orm_models import Company, AccountantAssignment, UserCompany


def get_company(company_id: int, db: Session, user) -> Company:
    """Return company if the user has tenant scope for it, else raise 403/404."""
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    roles = getattr(user, "role_names", [])
    if "super_admin" not in roles:
        allowed = False
        if "accountant" in roles and db.query(AccountantAssignment).filter_by(
            accountant_user_id=user.id, company_id=company_id
        ).first():
            allowed = True
        # TODO: remove manager scope after data migration is confirmed
        if "manager" in roles and db.query(UserCompany).filter_by(
            user_id=user.id, company_id=company_id
        ).first():
            allowed = True
        if not allowed:
            raise HTTPException(status_code=403, detail="Forbidden")
    return company
