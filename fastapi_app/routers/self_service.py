from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.guards import get_current_user
from db import get_db
from orm_models import Company, Employee, EmployeeUser, PayrollRecord, User

router = APIRouter(tags=["self-service"])


@router.get("/me/profile")
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
            "first_name": user.first_name, "last_name": user.last_name, "roles": roles,
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
        } if employee else None,
    }


@router.get("/me/payslips")
def get_my_payslips(
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    link = db.query(EmployeeUser).filter_by(user_id=user.id).first()
    if not link:
        return {"total": 0, "payslips": []}
    # Employees only see payslips that have been explicitly distributed by admin
    q = db.query(PayrollRecord).filter(
        PayrollRecord.employee_id == link.employee_id,
        PayrollRecord.distributed == True,
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
        } for r in records],
    }
