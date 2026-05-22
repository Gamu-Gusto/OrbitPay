from sqlalchemy import Column, Integer, String, Date, ForeignKey, Table, Boolean, DateTime, Float, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from sqlalchemy.types import String as SAString
from db import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    registration_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    uif_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    employees = relationship("Employee", back_populates="company", cascade="all, delete-orphan")
    accountant_assignments = relationship("AccountantAssignment", back_populates="company", cascade="all, delete-orphan")
    user_companies = relationship("UserCompany", back_populates="company", cascade="all, delete-orphan")
    payroll_records = relationship("PayrollRecord", back_populates="company", cascade="all, delete-orphan")


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)

    # Personal Information
    first_names: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    id_no: Mapped[str | None] = mapped_column(String(100), nullable=True)
    employee_no: Mapped[str | None] = mapped_column(String(100), nullable=True)
    position: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tax_ref: Mapped[str | None] = mapped_column(String(100), nullable=True)
    emp_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    
    # Employment Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    termination_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    
    # Salary Information
    basic_salary: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    hourly_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_type: Mapped[str] = mapped_column(String(20), nullable=False, default="monthly")  # monthly, hourly, daily
    
    # Allowances
    housing_allowance: Mapped[float] = mapped_column(Float, default=0.0)
    transport_allowance: Mapped[float] = mapped_column(Float, default=0.0)
    meal_allowance: Mapped[float] = mapped_column(Float, default=0.0)
    other_allowances: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Deductions
    pension_contribution: Mapped[float] = mapped_column(Float, default=0.0)
    medical_aid: Mapped[float] = mapped_column(Float, default=0.0)
    union_fees: Mapped[float] = mapped_column(Float, default=0.0)
    other_deductions: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Tax Information
    tax_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tax_directive: Mapped[str | None] = mapped_column(String(100), nullable=True)  # Tax directive number if applicable
    
    # Banking Information
    bank_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    account_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    branch_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    account_type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # savings, current, etc.
    bank_account_last4: Mapped[str | None] = mapped_column(String(4), nullable=True)

    # Fund / scheme names (displayed on payslip)
    pension_fund_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    medical_aid_scheme_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    company = relationship("Company", back_populates="employees")
    payroll_records = relationship("PayrollRecord", back_populates="employee", cascade="all, delete-orphan")
    leave_balances = relationship("LeaveBalance", back_populates="employee", cascade="all, delete-orphan")
    leave_requests = relationship("LeaveRequest", back_populates="employee", cascade="all, delete-orphan")


# ------------------ Auth & RBAC ------------------
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    force_password_change: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    companies = relationship("UserCompany", back_populates="user", cascade="all, delete-orphan")
    employee_link = relationship("EmployeeUser", back_populates="user", cascade="all, delete-orphan")


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    users = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)

    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")


class AccountantAssignment(Base):
    __tablename__ = "accountant_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    accountant_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="accountant_assignments")


class UserCompany(Base):
    __tablename__ = "user_companies"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="companies")
    company = relationship("Company", back_populates="user_companies")


class EmployeeUser(Base):
    __tablename__ = "employee_users"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), primary_key=True)

    user = relationship("User", back_populates="employee_link")


class PayrollRecord(Base):
    __tablename__ = "payroll_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Monthly payrun tracking
    payrun_month: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # 1-12
    payrun_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)   # e.g., 2025
    payrun_period: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # e.g., "2025-10"
    
    # Employee details (stored for historical record)
    employee_name: Mapped[str] = mapped_column(String(255), nullable=False)
    employee_id_no: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Payroll period
    pay_period_start: Mapped[Date] = mapped_column(Date, nullable=False)
    pay_period_end: Mapped[Date] = mapped_column(Date, nullable=False)
    
    # Earnings
    basic_pay: Mapped[float] = mapped_column(Float, nullable=False)
    other_earnings: Mapped[float] = mapped_column(Float, default=0.0)
    other_earnings_description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    leave_income: Mapped[float] = mapped_column(Float, default=0.0)
    total_earnings: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Deductions
    paye: Mapped[float] = mapped_column(Float, default=0.0)
    uif_employee: Mapped[float] = mapped_column(Float, default=0.0)
    uif_employer: Mapped[float] = mapped_column(Float, default=0.0)
    sdl: Mapped[float] = mapped_column(Float, default=0.0)
    pension: Mapped[float] = mapped_column(Float, default=0.0)
    medical: Mapped[float] = mapped_column(Float, default=0.0)
    total_deductions: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Net pay
    net_pay: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Approval workflow
    status: Mapped[str] = mapped_column(String(20), default="approved", server_default="approved")
    approved_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Distribution to employee portal
    distributed: Mapped[bool] = mapped_column(Boolean, default=False)
    distributed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    distributed_by: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    company = relationship("Company", back_populates="payroll_records")
    employee = relationship("Employee", back_populates="payroll_records")
    creator = relationship("User")


class LeaveBalance(Base):
    __tablename__ = "leave_balances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), index=True)
    leave_type: Mapped[str] = mapped_column(String(50), nullable=False)  # Annual, Sick, Family Responsibility, Unpaid
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    days_allocated: Mapped[float] = mapped_column(Float, default=21.0)
    days_taken: Mapped[float] = mapped_column(Float, default=0.0)

    employee = relationship("Employee", back_populates="leave_balances")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), index=True)
    leave_type: Mapped[str] = mapped_column(String(50), nullable=False)
    start_date: Mapped[Date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Date] = mapped_column(Date, nullable=False)
    days_requested: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    review_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    documentation_requested_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="leave_requests")


class EmployeeDocument(Base):
    __tablename__ = "employee_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), index=True)
    uploaded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_data: Mapped[str] = mapped_column(Text, nullable=False)  # base64-encoded
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee")
    uploader = relationship("User", foreign_keys=[uploaded_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])


class BankingChangeRequest(Base):
    __tablename__ = "banking_change_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), index=True)
    requested_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    new_bank_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    new_account_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    new_account_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    new_branch_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    employee = relationship("Employee")
    requester = relationship("User", foreign_keys=[requested_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    company_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payload: Mapped[str | None] = mapped_column(String(4000), nullable=True)  # JSON string
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)  # IPv4 or IPv6
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SystemConfig(Base):
    __tablename__ = "system_config"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ActivationToken(Base):
    __tablename__ = "activation_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AccountantRegistrationRequest(Base):
    __tablename__ = "accountant_registration_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    firm_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    rejection_reason: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    recipient_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

