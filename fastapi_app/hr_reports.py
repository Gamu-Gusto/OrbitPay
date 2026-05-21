from pydantic import BaseModel
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from orm_models import AccountantAssignment, Employee, User, PayrollRecord, UserCompany
from db import get_db
from utils import monthly_paye_from_gross, uif_employee, calculate_sdl
from core.guards import get_current_user, require_permission

router = APIRouter()

class HRReportsResponse(BaseModel):
    headcount: dict
    turnoverRate: float
    leaveStats: dict
    payrollSummary: dict
    employeeList: list = []

class DetailedReportsResponse(BaseModel):
    employeeHeadcount: dict
    turnoverDetails: dict
    leaveDetails: dict
    payrollDetails: dict

class EmployeeSalaryInfo(BaseModel):
    id: int
    employee_no: str | None
    full_name: str
    position: str | None
    basic_salary: float
    total_allowances: float
    total_deductions: float
    gross_salary: float
    is_active: bool
    emp_date: str | None
    bank_name: str | None
    account_number: str | None


def _allowed_ids(user, db) -> set[int] | None:
    """Return the set of company IDs accessible to non-super-admin users, or None for super_admin."""
    roles = getattr(user, "role_names", [])
    if "super_admin" in roles:
        return None
    ids: set[int] = set()
    if "accountant" in roles:
        ids |= {a.company_id for a in db.query(AccountantAssignment).filter_by(accountant_user_id=user.id)}
    if "manager" in roles:
        ids |= {uc.company_id for uc in db.query(UserCompany).filter_by(user_id=user.id)}
    return ids


def _apply_company_filter(query, model, company_id, allowed_ids):
    """Apply tenant-scoped company filter to a SQLAlchemy query."""
    if company_id:
        return query.filter(model.company_id == company_id)
    if allowed_ids is not None:
        return query.filter(model.company_id.in_(allowed_ids))
    return query


@router.get("/hr-reports", response_model=HRReportsResponse)
def get_hr_reports(
    company_id: int = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("VIEW_HR_REPORTS"))
):
    try:
        allowed = _allowed_ids(user, db)

        if allowed is not None and company_id and company_id not in allowed:
            raise HTTPException(status_code=403, detail="Access denied to this company")

        employee_query = _apply_company_filter(db.query(Employee), Employee, company_id, allowed)

        total_employees = employee_query.count()
        active_employees = employee_query.filter(Employee.is_active == True).count()
        terminated_employees = employee_query.filter(Employee.is_active == False).count()
        turnover_rate = (terminated_employees / total_employees * 100.0) if total_employees else 0.0

        current_date = datetime.utcnow()
        month_query = _apply_company_filter(
            db.query(PayrollRecord).filter(
                PayrollRecord.payrun_month == current_date.month,
                PayrollRecord.payrun_year == current_date.year,
            ),
            PayrollRecord, company_id, allowed,
        )
        current_month_payrolls = month_query.all()
        employees = employee_query.all()

        if current_month_payrolls:
            total_salaries = sum(p.total_earnings for p in current_month_payrolls)
            total_leave_taken = sum(p.leave_income or 0 for p in current_month_payrolls)
            total_leave_balance = 0
            paye_total = sum(p.paye or 0 for p in current_month_payrolls)
            uif_total = sum((p.uif_employee or 0) + (p.uif_employer or 0) for p in current_month_payrolls)
            sdl_total = sum(p.sdl or 0 for p in current_month_payrolls)
        else:
            total_basic = sum(emp.basic_salary or 0 for emp in employees)
            total_allowances_sum = sum(
                (emp.housing_allowance or 0) + (emp.transport_allowance or 0) +
                (emp.meal_allowance or 0) + (emp.other_allowances or 0)
                for emp in employees
            )
            gross_total = total_basic + total_allowances_sum
            paye_total = 0.0
            uif_total = 0.0
            for emp in employees:
                emp_gross = (emp.basic_salary or 0) + (
                    (emp.housing_allowance or 0) + (emp.transport_allowance or 0) +
                    (emp.meal_allowance or 0) + (emp.other_allowances or 0)
                )
                paye_total += monthly_paye_from_gross(emp_gross)
                uif_total += uif_employee(emp_gross) * 2
            sdl_details = calculate_sdl(total_remuneration=gross_total, annual_payroll=gross_total * 12, excluded_amounts=0.0)
            sdl_total = sdl_details.get("sdl_amount", 0.0)
            total_salaries = total_basic
            total_leave_taken = 0.0
            total_leave_balance = 0.0

        employee_list = []
        for emp in employees:
            total_allowances = (
                (emp.housing_allowance or 0) + (emp.transport_allowance or 0) +
                (emp.meal_allowance or 0) + (emp.other_allowances or 0)
            )
            total_deductions = (
                (emp.pension_contribution or 0) + (emp.medical_aid or 0) +
                (emp.union_fees or 0) + (emp.other_deductions or 0)
            )
            gross_salary = (emp.basic_salary or 0) + total_allowances
            employee_list.append({
                "id": emp.id,
                "employee_no": emp.employee_no,
                "full_name": f"{emp.first_names} {emp.last_name}",
                "position": emp.position,
                "basic_salary": round(emp.basic_salary or 0, 2),
                "total_allowances": round(total_allowances, 2),
                "total_deductions": round(total_deductions, 2),
                "gross_salary": round(gross_salary, 2),
                "is_active": getattr(emp, "is_active", True),
                "emp_date": emp.emp_date.isoformat() if emp.emp_date else None,
                "bank_name": emp.bank_name,
                "account_number": emp.account_number,
            })

        return HRReportsResponse(
            headcount={"active": active_employees, "terminated": terminated_employees, "total": total_employees},
            turnoverRate=round(turnover_rate, 2),
            leaveStats={"taken": total_leave_taken, "balance": total_leave_balance, "total": total_leave_taken + total_leave_balance},
            payrollSummary={
                "salaries": round(total_salaries, 2),
                "paye": round(paye_total, 2),
                "uif": round(uif_total, 2),
                "sdl": round(sdl_total, 2),
            },
            employeeList=employee_list,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate HR reports: {str(e)}")


@router.get("/hr-reports/detailed", response_model=DetailedReportsResponse)
def get_detailed_hr_reports(
    company_id: int = None,
    period: str = "monthly",
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("VIEW_HR_REPORTS"))
):
    try:
        allowed = _allowed_ids(user, db)

        if allowed is not None and company_id and company_id not in allowed:
            raise HTTPException(status_code=403, detail="Access denied to this company")

        employee_query = _apply_company_filter(db.query(Employee), Employee, company_id, allowed)
        employees = employee_query.all()

        now = datetime.utcnow()
        days_back = {"monthly": 30, "quarterly": 90, "yearly": 365}.get(period, 30)
        start_date = now - timedelta(days=days_back)
        months_back = {"monthly": 1, "quarterly": 3, "yearly": 12}.get(period, 1)

        period_payrolls = []
        for i in range(months_back):
            month = now.month - i
            year = now.year
            if month <= 0:
                month += 12
                year -= 1
            month_query = _apply_company_filter(
                db.query(PayrollRecord).filter(
                    PayrollRecord.payrun_month == month,
                    PayrollRecord.payrun_year == year,
                ),
                PayrollRecord, company_id, allowed,
            )
            period_payrolls.extend(month_query.all())

        total_active_salaries = sum(p.total_earnings for p in period_payrolls)
        unique_employees = len({p.employee_id for p in period_payrolls if p.employee_id})

        return DetailedReportsResponse(
            employeeHeadcount={
                "total": len(employees),
                "active": sum(1 for e in employees if e.is_active),
                "terminated": sum(1 for e in employees if not e.is_active),
                "byCompany": {},
            },
            turnoverDetails={
                "totalTerminations": 0,
                "turnoverRate": 0.0,
                "period": period,
                "terminations": [],
            },
            leaveDetails={
                "totalEmployees": len(employees),
                "activeEmployees": sum(1 for e in employees if e.is_active),
                "terminatedEmployees": sum(1 for e in employees if not e.is_active),
                "recentTerminations": 0,
                "period": period,
                "startDate": start_date.isoformat(),
                "endDate": now.isoformat(),
            },
            payrollDetails={
                "totalActiveSalaries": round(total_active_salaries, 2),
                "averageSalary": round(total_active_salaries / unique_employees if unique_employees else 0, 2),
                "totalEmployees": len(employees),
                "activeEmployees": sum(1 for e in employees if e.is_active),
                "payrollRecords": len(period_payrolls),
                "period": period,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate detailed HR reports: {str(e)}")
