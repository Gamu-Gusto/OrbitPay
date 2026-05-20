"""
Seed script — run once to populate test data for approval flow testing.
Usage: python seed.py
Idempotent: checks for existing super_admin before inserting.
"""
import os, sys, base64
from datetime import date, datetime

# Allow running from repo root as well
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set.")
    sys.exit(1)

# Render uses postgres:// but SQLAlchemy needs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

from db import Base
from orm_models import (
    Company, Employee, User, Role, UserRole,
    AccountantAssignment, EmployeeUser,
    LeaveRequest, EmployeeDocument, BankingChangeRequest
)
from auth import hash_password

Base.metadata.create_all(bind=engine)


def get_or_create_role(db, name):
    role = db.query(Role).filter_by(name=name).first()
    if not role:
        role = Role(name=name)
        db.add(role)
        db.flush()
    return role


def seed():
    db = Session()
    try:
        # Guard: skip if super_admin already exists
        existing = db.query(User).join(UserRole).join(Role).filter(Role.name == "super_admin").first()
        if existing:
            print("Seed data already present. Skipping.")
            return

        # ── Roles ───────────────────────────────────────────────────
        role_super = get_or_create_role(db, "super_admin")
        role_accountant = get_or_create_role(db, "accountant")
        role_employee = get_or_create_role(db, "employee")

        # ── Companies ───────────────────────────────────────────────
        company_a = Company(
            name="Acme Industries",
            registration_number="2020/001234/07",
            address="1 Acme Road, Johannesburg, 2001",
            uif_reference="UIF-ACME-001",
            phone="011 555 1000",
            email="hr@acmeindustries.co.za",
        )
        company_b = Company(
            name="Beta Solutions",
            registration_number="2018/007890/07",
            address="22 Beta Street, Cape Town, 8001",
            uif_reference="UIF-BETA-002",
            phone="021 555 2000",
            email="hr@betasolutions.co.za",
        )
        db.add_all([company_a, company_b])
        db.flush()

        # ── Super Admin ─────────────────────────────────────────────
        super_admin = User(
            email="admin@orbitpay.co.za",
            password_hash=hash_password("Admin@1234"),
            first_name="Super",
            last_name="Admin",
            is_active=True,
        )
        db.add(super_admin)
        db.flush()
        db.add(UserRole(user_id=super_admin.id, role_id=role_super.id))

        # ── Accountants ─────────────────────────────────────────────
        accountant_a = User(
            email="acme.accountant@orbitpay.co.za",
            password_hash=hash_password("Accountant@1"),
            first_name="Alice",
            last_name="Mokoena",
            is_active=True,
        )
        accountant_b = User(
            email="beta.accountant@orbitpay.co.za",
            password_hash=hash_password("Accountant@2"),
            first_name="Bob",
            last_name="Dlamini",
            is_active=True,
        )
        db.add_all([accountant_a, accountant_b])
        db.flush()

        db.add(UserRole(user_id=accountant_a.id, role_id=role_accountant.id))
        db.add(UserRole(user_id=accountant_b.id, role_id=role_accountant.id))

        db.add(AccountantAssignment(accountant_user_id=accountant_a.id, company_id=company_a.id))
        db.add(AccountantAssignment(accountant_user_id=accountant_b.id, company_id=company_b.id))

        # ── Employees ───────────────────────────────────────────────
        emp1 = Employee(
            company_id=company_a.id,
            first_names="Thabo",
            last_name="Nkosi",
            employee_no="EMP-001",
            position="Software Developer",
            id_no="9001015009087",
            emp_date=date(2021, 3, 1),
            basic_salary=35000.0,
            transport_allowance=1500.0,
            pension_contribution=1750.0,
            bank_name="FNB",
            account_number="62001234567",
            account_type="Cheque",
            branch_code="250655",
            bank_account_last4="4567",
        )
        emp2 = Employee(
            company_id=company_a.id,
            first_names="Lerato",
            last_name="Sithole",
            employee_no="EMP-002",
            position="HR Officer",
            id_no="9205100049086",
            emp_date=date(2022, 6, 1),
            basic_salary=28000.0,
            housing_allowance=2000.0,
            medical_aid=1400.0,
            bank_name="ABSA",
            account_number="4070987654",
            account_type="Savings",
            branch_code="632005",
            bank_account_last4="7654",
        )
        emp3 = Employee(
            company_id=company_b.id,
            first_names="Sipho",
            last_name="Mthembu",
            employee_no="EMP-003",
            position="Accountant",
            id_no="8811205089083",
            emp_date=date(2020, 1, 15),
            basic_salary=42000.0,
            pension_contribution=2100.0,
            medical_aid=1800.0,
            bank_name="Standard Bank",
            account_number="272055001",
            account_type="Cheque",
            branch_code="051001",
            bank_account_last4="5001",
        )
        db.add_all([emp1, emp2, emp3])
        db.flush()

        # ── Employee User accounts ───────────────────────────────────
        emp_user1 = User(
            email="thabo.nkosi@acmeindustries.co.za",
            password_hash=hash_password("Employee@1"),
            first_name="Thabo",
            last_name="Nkosi",
            is_active=True,
        )
        db.add(emp_user1)
        db.flush()
        db.add(UserRole(user_id=emp_user1.id, role_id=role_employee.id))
        db.add(EmployeeUser(user_id=emp_user1.id, employee_id=emp1.id))

        # ── Pending Leave Request (from emp1) ────────────────────────
        leave_req = LeaveRequest(
            employee_id=emp1.id,
            leave_type="Annual",
            start_date=date(2026, 6, 9),
            end_date=date(2026, 6, 13),
            days_requested=5,
            reason="Family holiday",
            status="pending",
            created_at=datetime.utcnow(),
        )
        db.add(leave_req)

        # ── Pending Document (from emp1) ─────────────────────────────
        sample_content = b"Sample ID document for Thabo Nkosi - OrbitPay test seed"
        b64_data = base64.b64encode(sample_content).decode("utf-8")
        doc = EmployeeDocument(
            employee_id=emp1.id,
            uploaded_by=emp_user1.id,
            document_type="ID / Passport",
            description="Copy of South African ID",
            file_name="thabo_nkosi_id.txt",
            file_data=b64_data,
            file_size=len(sample_content),
            status="pending",
            uploaded_at=datetime.utcnow(),
        )
        db.add(doc)

        # ── Pending Banking Change (from emp1) ───────────────────────
        bank_change = BankingChangeRequest(
            employee_id=emp1.id,
            requested_by=emp_user1.id,
            new_bank_name="Nedbank",
            new_account_number="1234000999",
            new_account_type="Cheque",
            new_branch_code="198765",
            status="pending",
            requested_at=datetime.utcnow(),
        )
        db.add(bank_change)

        db.commit()
        print("Seed complete!")
        print()
        print("Credentials:")
        print("  Super Admin:    admin@orbitpay.co.za         / Admin@1234")
        print("  Accountant A:   acme.accountant@orbitpay.co.za / Accountant@1  (Acme Industries)")
        print("  Accountant B:   beta.accountant@orbitpay.co.za / Accountant@2  (Beta Solutions)")
        print("  Employee:       thabo.nkosi@acmeindustries.co.za / Employee@1")
        print()
        print("Pending approvals seeded:")
        print("  - 1 leave request (Annual, 5 days)")
        print("  - 1 document (ID / Passport)")
        print("  - 1 banking change (FNB → Nedbank)")

    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
