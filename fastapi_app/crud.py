from sqlalchemy.orm import Session
from sqlalchemy import select
from orm_models import Company, Employee
from schemas import (
    CompanyCreate,
    CompanyUpdate,
    EmployeeCreate,
    EmployeeUpdate,
)


# ------------------ Companies ------------------
def create_company(db: Session, company_in: CompanyCreate) -> Company:
    company = Company(**company_in.model_dump(exclude_unset=True))
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


def get_company(db: Session, company_id: int) -> Company | None:
    return db.get(Company, company_id)


def list_companies(db: Session, skip: int = 0, limit: int = 100) -> list[Company]:
    stmt = select(Company).offset(skip).limit(limit)
    return list(db.scalars(stmt))


def update_company(db: Session, company: Company, company_in: CompanyUpdate) -> Company:
    data = company_in.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(company, k, v)
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


def delete_company(db: Session, company: Company) -> None:
    db.delete(company)
    db.commit()


# ------------------ Employees ------------------
def create_employee(db: Session, company_id: int, employee_in: EmployeeCreate) -> Employee:
    employee = Employee(company_id=company_id, **employee_in.model_dump(exclude_unset=True))
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


def get_employee(db: Session, employee_id: int) -> Employee | None:
    return db.get(Employee, employee_id)


def list_employees(db: Session, company_id: int, skip: int = 0, limit: int = 100) -> list[Employee]:
    stmt = select(Employee).where(Employee.company_id == company_id).offset(skip).limit(limit)
    return list(db.scalars(stmt))


def update_employee(db: Session, employee: Employee, employee_in: EmployeeUpdate) -> Employee:
    data = employee_in.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(employee, k, v)
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


def delete_employee(db: Session, employee: Employee) -> None:
    db.delete(employee)
    db.commit()


