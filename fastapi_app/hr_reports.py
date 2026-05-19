from pydantic import BaseModel
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from orm_models import Employee, User, PayrollRecord
from db import get_db
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth import decode_token
from utils import monthly_paye_from_gross, uif_employee, calculate_sdl

router = APIRouter()
security = HTTPBearer()

# Local authentication functions to avoid circular imports
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    try:
        payload = decode_token(credentials.credentials)
        user_id = int(payload.get("sub"))
        roles = payload.get("roles", [])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Inactive user")

    user.role_names = roles
    return user

def require_roles(*allowed: str):
    def dep(user: User = Depends(get_current_user)):
        if not any(r in allowed for r in getattr(user, "role_names", [])):
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return dep

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

@router.get("/hr-reports", response_model=HRReportsResponse)
def get_hr_reports(
    company_id: int = None,
    db: Session = Depends(get_db), 
    user: User = Depends(require_roles("super_admin", "client_admin", "accountant"))
):
    """Get basic HR reports including employee headcount, turnover, leave stats, and payroll summary"""
    try:
        # Filter employees based on user role and company access
        employee_query = db.query(Employee)
        
        # If user is not super_admin, filter by company access
        # Note: role checking is handled by main.py dependencies
        if hasattr(user, "role_names") and "super_admin" not in user.role_names:
            # Get companies user has access to
            from orm_models import AccountantAssignment, UserCompany
            allowed_company_ids = set()
            
            if "accountant" in user.role_names:
                allowed_company_ids |= {a.company_id for a in db.query(AccountantAssignment).filter_by(accountant_user_id=user.id)}
            if "client_admin" in user.role_names:
                allowed_company_ids |= {uc.company_id for uc in db.query(UserCompany).filter_by(user_id=user.id)}
            
            # If specific company requested, check access
            if company_id:
                if company_id not in allowed_company_ids:
                    raise HTTPException(status_code=403, detail="Access denied to this company")
                employee_query = employee_query.filter(Employee.company_id == company_id)
            else:
                # Filter by all companies user has access to
                employee_query = employee_query.filter(Employee.company_id.in_(allowed_company_ids))
        elif company_id:
            # Super admin requesting specific company
            employee_query = employee_query.filter(Employee.company_id == company_id)
        
        # Employee headcount using is_active/termination_date
        total_employees = employee_query.count()
        active_employees = employee_query.filter(Employee.is_active == True).count()
        terminated_employees = employee_query.filter(Employee.is_active == False).count()
        
        # Turnover rate (terminated vs total, simple ratio)
        turnover_rate = (terminated_employees / total_employees * 100.0) if total_employees else 0.0
        
        # Leave statistics - calculated from payroll records
        payroll_query = db.query(PayrollRecord)
        if company_id:
            payroll_query = payroll_query.filter(PayrollRecord.company_id == company_id)
        elif hasattr(user, "role_names") and "super_admin" not in user.role_names:
            # Filter payroll records by company access
            from orm_models import AccountantAssignment, UserCompany
            allowed_company_ids = set()
            if "accountant" in user.role_names:
                allowed_company_ids |= {a.company_id for a in db.query(AccountantAssignment).filter_by(accountant_user_id=user.id)}
            if "client_admin" in user.role_names:
                allowed_company_ids |= {uc.company_id for uc in db.query(UserCompany).filter_by(user_id=user.id)}
            if allowed_company_ids:
                payroll_query = payroll_query.filter(PayrollRecord.company_id.in_(allowed_company_ids))
        
        # Calculate totals from payroll records for CURRENT month, else estimate from employee salaries
        current_date = datetime.utcnow()
        current_month = current_date.month
        current_year = current_date.year

        # Query payroll records for current month/year
        month_query = db.query(PayrollRecord).filter(
            PayrollRecord.payrun_month == current_month,
            PayrollRecord.payrun_year == current_year
        )

        if company_id:
            month_query = month_query.filter(PayrollRecord.company_id == company_id)
        elif hasattr(user, "role_names") and "super_admin" not in user.role_names:
            from orm_models import AccountantAssignment, UserCompany
            allowed_company_ids = set()
            if "accountant" in user.role_names:
                allowed_company_ids |= {a.company_id for a in db.query(AccountantAssignment).filter_by(accountant_user_id=user.id)}
            if "client_admin" in user.role_names:
                allowed_company_ids |= {uc.company_id for uc in db.query(UserCompany).filter_by(user_id=user.id)}
            if allowed_company_ids:
                month_query = month_query.filter(PayrollRecord.company_id.in_(allowed_company_ids))

        current_month_payrolls = month_query.all()

        # We'll also need the employee list for both paths
        employees = employee_query.all()

        if current_month_payrolls:
            # Use actual payroll data
            total_salaries = sum((p.total_earnings if hasattr(p, 'total_earnings') else (p.basic_pay + (p.other_earnings or 0) + (p.leave_income or 0))) for p in current_month_payrolls)
            total_leave_taken = sum(p.leave_income or 0 for p in current_month_payrolls)
            total_leave_balance = 0  # Would need leave balance tracking
            paye_total = sum(p.paye or 0 for p in current_month_payrolls)
            uif_total = sum((p.uif_employee or 0) + (p.uif_employer or 0) for p in current_month_payrolls)
            sdl_total = sum(p.sdl or 0 for p in current_month_payrolls)
        else:
            # Estimate from employee salary data (monthly projection)
            total_basic = sum((emp.basic_salary or 0) for emp in employees)
            total_allowances = sum(((emp.housing_allowance or 0) + (emp.transport_allowance or 0) + (emp.meal_allowance or 0) + (emp.other_allowances or 0)) for emp in employees)
            gross_total = total_basic + total_allowances

            # Taxes per employee to capture brackets
            paye_total = 0.0
            uif_total = 0.0
            for emp in employees:
                emp_gross = (emp.basic_salary or 0) + ((emp.housing_allowance or 0) + (emp.transport_allowance or 0) + (emp.meal_allowance or 0) + (emp.other_allowances or 0))
                paye_total += monthly_paye_from_gross(emp_gross)
                uif_total += uif_employee(emp_gross) * 2  # include employer UIF to match existing summary

            # SDL based on company-wide remuneration and annual threshold
            annual_payroll_est = gross_total * 12
            sdl_details = calculate_sdl(total_remuneration=gross_total, annual_payroll=annual_payroll_est, excluded_amounts=0.0)
            sdl_total = sdl_details.get('sdl_amount', 0.0)

            total_salaries = total_basic  # maintain label meaning "Total Salaries Paid"
            total_leave_taken = 0.0
            total_leave_balance = 0.0

        # Get employee salary details
        employee_list = []
        for emp in employees:
            # Calculate totals from employee salary fields
            total_allowances = (
                (emp.housing_allowance or 0) + 
                (emp.transport_allowance or 0) + 
                (emp.meal_allowance or 0) + 
                (emp.other_allowances or 0)
            )
            total_deductions = (
                (emp.pension_contribution or 0) + 
                (emp.medical_aid or 0) + 
                (emp.union_fees or 0) + 
                (emp.other_deductions or 0)
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
                "is_active": getattr(emp, 'is_active', True),
                "emp_date": emp.emp_date.isoformat() if emp.emp_date else None,
                "bank_name": emp.bank_name,
                "account_number": emp.account_number
            })
        
        return HRReportsResponse(
            headcount={
                "active": active_employees,
                "terminated": terminated_employees,
                "total": total_employees
            },
            turnoverRate=round(turnover_rate, 2),
            leaveStats={
                "taken": total_leave_taken,
                "balance": total_leave_balance,
                "total": total_leave_taken + total_leave_balance
            },
            payrollSummary={
                "salaries": round(total_salaries, 2),
                "paye": round(paye_total, 2),
                "uif": round(uif_total, 2),
                "sdl": round(sdl_total, 2)
            },
            employeeList=employee_list
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate HR reports: {str(e)}")

@router.get("/hr-reports/detailed", response_model=DetailedReportsResponse)
def get_detailed_hr_reports(
    company_id: int = None,
    period: str = "monthly",
    db: Session = Depends(get_db), 
    user: User = Depends(require_roles("super_admin", "client_admin", "accountant"))
):
    """Get detailed HR reports filtered by period"""
    try:
        # Filter employees based on user role and company access
        employee_query = db.query(Employee)
        
        # If user is not super_admin, filter by company access
        # Note: role checking is handled by main.py dependencies
        if hasattr(user, "role_names") and "super_admin" not in user.role_names:
            # Get companies user has access to
            from orm_models import AccountantAssignment, UserCompany
            allowed_company_ids = set()
            
            if "accountant" in user.role_names:
                allowed_company_ids |= {a.company_id for a in db.query(AccountantAssignment).filter_by(accountant_user_id=user.id)}
            if "client_admin" in user.role_names:
                allowed_company_ids |= {uc.company_id for uc in db.query(UserCompany).filter_by(user_id=user.id)}
            
            # If specific company requested, check access
            if company_id:
                if company_id not in allowed_company_ids:
                    raise HTTPException(status_code=403, detail="Access denied to this company")
                employee_query = employee_query.filter(Employee.company_id == company_id)
            else:
                # Filter by all companies user has access to
                employee_query = employee_query.filter(Employee.company_id.in_(allowed_company_ids))
        elif company_id:
            # Super admin requesting specific company
            employee_query = employee_query.filter(Employee.company_id == company_id)
        
        # Calculate date range based on period
        now = datetime.utcnow()
        if period == "monthly":
            start_date = now - timedelta(days=30)
        elif period == "quarterly":
            start_date = now - timedelta(days=90)
        elif period == "yearly":
            start_date = now - timedelta(days=365)
        else:
            start_date = now - timedelta(days=30)
        
        # Employee headcount details - simplified since status field doesn't exist
        employees = employee_query.all()
        active_employees = employees  # Assuming all employees are active
        terminated_employees = []  # No status tracking yet
        
        # Turnover details - cannot calculate without termination tracking
        recent_terminations = []
        
        # Leave details (simplified)
        leave_details = {
            "totalEmployees": len(employees),
            "activeEmployees": len(active_employees),
            "terminatedEmployees": 0,
            "recentTerminations": 0,
            "period": period,
            "startDate": start_date.isoformat(),
            "endDate": now.isoformat(),
            "note": "Status tracking not yet implemented in Employee model"
        }
        
        # Payroll details - from actual payroll records using monthly periods
        current_date = datetime.utcnow()
        current_month = current_date.month
        current_year = current_date.year
        
        # Calculate how many months back to look based on period
        months_back = 1 if period == "monthly" else (3 if period == "quarterly" else 12)
        
        payroll_query = db.query(PayrollRecord)
        period_payrolls = []
        
        for i in range(months_back):
            month = current_month - i
            year = current_year
            if month <= 0:
                month += 12
                year -= 1
            
            # Create a fresh query for this specific month
            month_query = db.query(PayrollRecord).filter(
                PayrollRecord.payrun_month == month,
                PayrollRecord.payrun_year == year
            )
            
            # Apply company filtering to this month's query
            if company_id:
                month_query = month_query.filter(PayrollRecord.company_id == company_id)
            elif hasattr(user, "role_names") and "super_admin" not in user.role_names:
                from orm_models import AccountantAssignment, UserCompany
                allowed_company_ids = set()
                if "accountant" in user.role_names:
                    allowed_company_ids |= {a.company_id for a in db.query(AccountantAssignment).filter_by(accountant_user_id=user.id)}
                if "client_admin" in user.role_names:
                    allowed_company_ids |= {uc.company_id for uc in db.query(UserCompany).filter_by(user_id=user.id)}
                if allowed_company_ids:
                    month_query = month_query.filter(PayrollRecord.company_id.in_(allowed_company_ids))
            
            # Add this month's payrolls to the list
            period_payrolls.extend(month_query.all())
        
        total_active_salaries = sum(p.total_earnings for p in period_payrolls)
        unique_employees = len(set(p.employee_id for p in period_payrolls if p.employee_id))

        payroll_details = {
            "totalActiveSalaries": round(total_active_salaries, 2),
            "averageSalary": round(total_active_salaries / unique_employees if unique_employees > 0 else 0, 2),
            "totalEmployees": len(employees),
            "activeEmployees": len(active_employees),
            "payrollRecords": len(period_payrolls),
            "period": period
        }
        
        return DetailedReportsResponse(
            employeeHeadcount={
                "total": len(employees),
                "active": len(active_employees),
                "terminated": len(terminated_employees),
                "byCompany": {}  # Could be enhanced to group by company
            },
            turnoverDetails={
                "totalTerminations": len(recent_terminations),
                "turnoverRate": round((len(recent_terminations) / len(employees) * 100) if employees else 0, 2),
                "period": period,
                "terminations": [
                    {
                        "id": e.id,
                        "name": f"{e.first_names} {e.last_name}",
                        "terminationDate": e.termination_date.isoformat() if e.termination_date else None,
                        "company": e.company.name if e.company else "Unknown"
                    }
                    for e in recent_terminations
                ]
            },
            leaveDetails=leave_details,
            payrollDetails=payroll_details
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate detailed HR reports: {str(e)}")
