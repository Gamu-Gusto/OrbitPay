import os
from calendar import monthrange
from datetime import date
from typing import List, Tuple

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import hash_password
from core.audit import log_audit
from core.email import send_welcome_email
from core.guards import get_current_user, require_permission
from core.tenant import get_company
from db import get_db
from models import CompanyDetails, EmployeeDetails, PayslipData
from orm_models import Company, Employee, EmployeeUser, Role, User, UserCompany, UserRole
from schemas import EmployeeCreateWithCredentials, EmployeeImportResult, EmployeeRead, EmployeeUpdate
from utils import calculate_sdl, monthly_paye_from_gross, uif_employee

router = APIRouter(tags=["employees"])


@router.post("/companies/{company_id}/employees", response_model=EmployeeRead)
def create_employee(
    company_id: int,
    employee_in: EmployeeCreateWithCredentials,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("CREATE_EMPLOYEE")),
):
    if not db.get(Company, company_id):
        raise HTTPException(status_code=404, detail="Company not found")
    get_company(company_id, db, user)

    # Validate credentials before creating employee (fail fast)
    if employee_in.login_email:
        if not employee_in.login_password:
            raise HTTPException(status_code=400, detail="login_password is required when login_email is provided")
        if db.query(User).filter(User.email == employee_in.login_email).first():
            raise HTTPException(status_code=400, detail="A user with that email already exists")

    employee_data = employee_in.model_dump(exclude_unset=True, exclude={"login_email", "login_password"})
    employee = Employee(company_id=company_id, **employee_data)
    db.add(employee)
    db.flush()

    # Create linked user account if credentials were provided
    if employee_in.login_email and employee_in.login_password:
        role = db.query(Role).filter(Role.name == "employee").first()
        if not role:
            raise HTTPException(status_code=500, detail="Employee role not found — run seed first")
        new_user = User(
            email=employee_in.login_email,
            password_hash=hash_password(employee_in.login_password),
            first_name=employee.first_names,
            last_name=employee.last_name,
            force_password_change=True,
        )
        db.add(new_user)
        db.flush()
        db.add(UserRole(user_id=new_user.id, role_id=role.id))
        db.add(UserCompany(user_id=new_user.id, company_id=company_id))
        db.add(EmployeeUser(user_id=new_user.id, employee_id=employee.id))

        frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
        try:
            send_welcome_email(
                to_email=employee_in.login_email,
                full_name=f"{employee.first_names} {employee.last_name}",
                temp_password=employee_in.login_password,
                frontend_url=frontend_url,
            )
        except Exception:
            pass  # Don't block employee creation if email delivery fails

    log_audit(
        db, user.id, "employee.create", "employee", employee.id,
        {"name": f"{employee.first_names} {employee.last_name}", "company_id": company_id,
         "user_account_created": bool(employee_in.login_email)},
        company_id=company_id,
    )
    db.commit()
    db.refresh(employee)
    return employee


@router.get("/companies/{company_id}/employees", response_model=list[EmployeeRead])
def list_employees(
    company_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("VIEW_EMPLOYEES")),
):
    if not db.get(Company, company_id):
        raise HTTPException(status_code=404, detail="Company not found")
    get_company(company_id, db, user)
    return list(db.query(Employee).filter(Employee.company_id == company_id).offset(skip).limit(limit).all())


@router.get("/employees/{employee_id}", response_model=EmployeeRead)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("VIEW_EMPLOYEES")),
):
    employee = db.get(Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    roles = getattr(user, "role_names", [])
    if "super_admin" in roles:
        return employee
    get_company(employee.company_id, db, user)
    return employee


@router.put("/employees/{employee_id}", response_model=EmployeeRead)
def update_employee(
    employee_id: int,
    employee_in: EmployeeUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("EDIT_EMPLOYEE")),
):
    employee = db.get(Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    get_company(employee.company_id, db, user)
    changes = employee_in.model_dump(exclude_unset=True)
    for k, v in changes.items():
        setattr(employee, k, v)
    db.add(employee)
    log_audit(
        db, user.id, "employee.update", "employee", employee_id,
        {"fields_changed": list(changes.keys())},
        company_id=employee.company_id,
    )
    db.commit()
    db.refresh(employee)
    return employee


@router.delete("/employees/{employee_id}", status_code=204)
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("DELETE_EMPLOYEE")),
):
    employee = db.get(Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    get_company(employee.company_id, db, user)
    log_audit(
        db, user.id, "employee.delete", "employee", employee_id,
        {"name": f"{employee.first_names} {employee.last_name}"},
        company_id=employee.company_id,
    )
    db.delete(employee)
    db.commit()
    return None


@router.get(
    "/companies/{company_id}/employees/{employee_id}/payroll-preview",
    response_model=PayslipData,
)
def preview_payroll_from_employee(
    company_id: int,
    employee_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    get_company(company_id, db, user)
    employee = db.get(Employee, employee_id)
    if not employee or employee.company_id != company_id:
        raise HTTPException(status_code=404, detail="Employee not found for this company")

    today = date.today()
    start_day = date(today.year, today.month, 1)
    end_day = date(today.year, today.month, monthrange(today.year, today.month)[1])

    emp_details = EmployeeDetails(
        first_names=employee.first_names,
        last_name=employee.last_name,
        id_no=employee.id_no or "",
        employee_no=employee.employee_no or "",
        position=employee.position or "",
        tax_ref=employee.tax_ref or "",
        emp_date=employee.emp_date or start_day,
        bank_account_last4=employee.bank_account_last4 or None,
        pension_fund_name=employee.pension_fund_name or None,
        medical_aid_scheme_name=employee.medical_aid_scheme_name or None,
    )
    comp_details = CompanyDetails(
        company_name=company.name,
        company_reg_no=company.registration_number or "",
        company_address=company.address or "",
        uif_ref=company.uif_reference or "",
        phone=company.phone or "",
        email=company.email or "",
        run=f"{today.year}-{today.month:02d}",
    )

    basic_pay = float(getattr(employee, "basic_salary", 0.0) or 0.0)
    other_earnings = float(
        (getattr(employee, "housing_allowance", 0.0) or 0.0)
        + (getattr(employee, "transport_allowance", 0.0) or 0.0)
        + (getattr(employee, "meal_allowance", 0.0) or 0.0)
        + (getattr(employee, "other_allowances", 0.0) or 0.0)
    )
    pension = float(getattr(employee, "pension_contribution", 0.0) or 0.0)
    medical = float(getattr(employee, "medical_aid", 0.0) or 0.0)
    union_fees = float(getattr(employee, "union_fees", 0.0) or 0.0)
    other_deductions = float(getattr(employee, "other_deductions", 0.0) or 0.0)

    total_earnings = basic_pay + other_earnings
    paye = monthly_paye_from_gross(total_earnings)
    uif = uif_employee(total_earnings)
    sdl_details = calculate_sdl(total_remuneration=total_earnings, annual_payroll=0.0, excluded_amounts=0.0)
    sdl_amount = sdl_details["sdl_amount"]
    total_deductions = pension + medical + union_fees + other_deductions + paye + uif
    net_pay = total_earnings - total_deductions

    earnings_list: List[Tuple[str, float]] = [("Basic Pay", basic_pay)]
    if other_earnings:
        earnings_list.append(("Allowances", other_earnings))
    deductions_list: List[Tuple[str, float]] = [("PAYE", paye), ("UIF", uif)]
    if pension:
        deductions_list.append(("Pension", pension))
    if medical:
        deductions_list.append(("Medical Aid", medical))
    if union_fees:
        deductions_list.append(("Union Fees", union_fees))
    if other_deductions:
        deductions_list.append(("Other Deductions", other_deductions))

    return PayslipData(
        employee=emp_details,
        company=comp_details,
        period_start=start_day,
        period_end=end_day,
        payment_date=today,
        earnings=earnings_list,
        total_earnings=total_earnings,
        deductions=deductions_list,
        total_deductions=total_deductions,
        net_pay=net_pay,
        paye=paye,
        uif=uif,
        sdl=sdl_amount,
        leave_income=0.0,
        sdl_details=sdl_details,
        leave_income_details=None,
    )


@router.post("/companies/{company_id}/employees/import", response_model=EmployeeImportResult)
def import_employees(
    company_id: int,
    employees_data: List[EmployeeCreateWithCredentials],
    user: User = Depends(require_permission("IMPORT_EMPLOYEES")),
    db: Session = Depends(get_db),
):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    get_company(company_id, db, user)
    created = 0
    errors: List[str] = []
    for i, emp_data in enumerate(employees_data):
        try:
            emp_dict = emp_data.model_dump(exclude={"login_email", "login_password"})
            emp = Employee(company_id=company_id, **emp_dict)
            db.add(emp)
            created += 1
        except Exception as e:
            errors.append(f"Row {i + 1} ({emp_data.first_names} {emp_data.last_name}): {str(e)}")
    try:
        log_audit(
            db, user.id, "employee.import", "company", company_id,
            {"created": created, "failed": len(errors)},
            company_id=company_id,
        )
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
    return EmployeeImportResult(created=created, failed=len(errors), errors=errors)
