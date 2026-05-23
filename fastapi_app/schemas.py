from datetime import date
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any


# ------------------ Company ------------------
class CompanyBase(BaseModel):
    name: str
    registration_number: Optional[str] = None
    address: Optional[str] = None
    uif_reference: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    registration_number: Optional[str] = None
    address: Optional[str] = None
    uif_reference: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None


class CompanyRead(CompanyBase):
    id: int

    class Config:
        from_attributes = True


# ------------------ Employee ------------------
class EmployeeBase(BaseModel):
    first_names: str
    last_name: str
    id_no: Optional[str] = None
    employee_no: Optional[str] = None
    position: Optional[str] = None
    tax_ref: Optional[str] = None
    emp_date: Optional[date] = None
    
    # Employment Status
    is_active: Optional[bool] = True
    termination_date: Optional[date] = None
    
    # Salary Information
    basic_salary: float = 0.0
    hourly_rate: Optional[float] = None
    salary_type: str = "monthly"  # monthly, hourly, daily
    
    # Allowances
    housing_allowance: float = 0.0
    transport_allowance: float = 0.0
    meal_allowance: float = 0.0
    other_allowances: float = 0.0
    
    # Deductions
    pension_contribution: float = 0.0
    medical_aid: float = 0.0
    union_fees: float = 0.0
    other_deductions: float = 0.0
    
    # Tax Information
    tax_number: Optional[str] = None
    tax_directive: Optional[str] = None
    
    # Banking Information
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    branch_code: Optional[str] = None
    account_type: Optional[str] = None
    bank_account_last4: Optional[str] = None

    # Fund / scheme names
    pension_fund_name: Optional[str] = None
    medical_aid_scheme_name: Optional[str] = None


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeCreateWithCredentials(EmployeeCreate):
    login_email: Optional[EmailStr] = None
    login_password: Optional[str] = Field(None, min_length=8, max_length=64)


class EmployeeUpdate(BaseModel):
    first_names: Optional[str] = None
    last_name: Optional[str] = None
    id_no: Optional[str] = None
    employee_no: Optional[str] = None
    position: Optional[str] = None
    tax_ref: Optional[str] = None
    emp_date: Optional[date] = None
    
    # Employment Status
    is_active: Optional[bool] = None
    termination_date: Optional[date] = None
    
    # Salary Information
    basic_salary: Optional[float] = None
    hourly_rate: Optional[float] = None
    salary_type: Optional[str] = None
    
    # Allowances
    housing_allowance: Optional[float] = None
    transport_allowance: Optional[float] = None
    meal_allowance: Optional[float] = None
    other_allowances: Optional[float] = None
    
    # Deductions
    pension_contribution: Optional[float] = None
    medical_aid: Optional[float] = None
    union_fees: Optional[float] = None
    other_deductions: Optional[float] = None
    
    # Tax Information
    tax_number: Optional[str] = None
    tax_directive: Optional[str] = None
    
    # Banking Information
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    branch_code: Optional[str] = None
    account_type: Optional[str] = None
    bank_account_last4: Optional[str] = None

    # Fund / scheme names
    pension_fund_name: Optional[str] = None
    medical_aid_scheme_name: Optional[str] = None


class EmployeeUserInfo(BaseModel):
    user_id: int
    email: str
    is_active: bool
    last_login: Optional[str] = None

    class Config:
        from_attributes = True


class EmployeeRead(EmployeeBase):
    id: int
    company_id: int
    user_info: Optional[EmployeeUserInfo] = None

    class Config:
        from_attributes = True


class EmployeeUpdateWithCredentials(EmployeeUpdate):
    login_email: Optional[EmailStr] = None
    login_password: Optional[str] = Field(None, min_length=8, max_length=64)


class CompanyWithEmployees(CompanyRead):
    employees: List[EmployeeRead] = []


# ------------------ Auth ------------------
class UserRead(BaseModel):
    id: int
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool
    force_password_change: bool = False
    roles: List[str] = []
    assigned_company_ids: List[int] = []

    class Config:
        from_attributes = True


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=64, description="Password must be 8-64 characters long")
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str
    company_id: Optional[int] = None
    employee_id: Optional[int] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=64)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str = ""
    token_type: str = "bearer"
    user: UserRead


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


# ------------------ Leave Balances ------------------
class LeaveBalanceCreate(BaseModel):
    leave_type: str  # Annual, Sick, Family Responsibility, Unpaid
    year: int
    days_allocated: float = 21.0
    days_taken: float = 0.0


class LeaveBalanceUpdate(BaseModel):
    days_allocated: Optional[float] = None
    days_taken: Optional[float] = None


class LeaveBalanceRead(BaseModel):
    id: int
    employee_id: int
    leave_type: str
    year: int
    days_allocated: float
    days_taken: float
    days_remaining: float

    class Config:
        from_attributes = True


# ------------------ Bulk Payroll ------------------
class BulkPayrollRequest(BaseModel):
    year: int
    month: int  # 1-12


class BulkPayrollEmployeeResult(BaseModel):
    employee_id: int
    employee_name: str
    record_id: Optional[int] = None
    basic_pay: float
    total_earnings: float
    total_deductions: float
    net_pay: float
    status: str  # "success" or "error"
    error: Optional[str] = None
    distributed: bool = False


class BulkPayrollResult(BaseModel):
    company_id: int
    period: str
    payroll_run_id: Optional[str] = None
    total_employees: int
    successful: int
    failed: int
    total_net_pay: float
    employees: List[BulkPayrollEmployeeResult]


# ------------------ Payroll Approval ------------------
class PayrollApprovalRequest(BaseModel):
    year: int
    month: int
    reason: Optional[str] = None  # Used for rejection


# ------------------ Employee Import ------------------
class EmployeeImportResult(BaseModel):
    created: int
    failed: int
    errors: List[str] = []


# ------------------ Leave Requests ------------------
class LeaveRequestCreate(BaseModel):
    leave_type: str
    start_date: date
    end_date: date
    reason: Optional[str] = None


class LeaveRequestReview(BaseModel):
    status: str  # "approved", "rejected", "under_review"
    note: Optional[str] = None


class LeaveDocumentRequest(BaseModel):
    reason: str


# ------------------ Assignments ------------------
class AccountantAssignRequest(BaseModel):
    accountant_user_id: int
    company_id: int


class ManagerAssignRequest(BaseModel):
    user_id: int
    company_id: int


ClientAdminAssignRequest = ManagerAssignRequest  # backward-compat alias


class EmployeeLinkRequest(BaseModel):
    user_id: int
    employee_id: int


# ------------------ Employee Documents ------------------
class EmployeeDocumentRead(BaseModel):
    id: int
    employee_id: int
    document_type: str
    description: Optional[str] = None
    file_name: str
    file_size: int
    status: str
    rejection_reason: Optional[str] = None
    uploaded_at: str
    uploaded_by_name: Optional[str] = None

    class Config:
        from_attributes = True


class DocumentReviewRequest(BaseModel):
    status: str  # "approved" | "rejected"
    reason: Optional[str] = None


# ------------------ Banking Change Requests ------------------
class BankingChangeCreate(BaseModel):
    new_bank_name: Optional[str] = None
    new_account_number: Optional[str] = None
    new_account_type: Optional[str] = None
    new_branch_code: Optional[str] = None


class BankingChangeRead(BaseModel):
    id: int
    employee_id: int
    employee_name: Optional[str] = None
    company_name: Optional[str] = None
    new_bank_name: Optional[str] = None
    new_account_number: Optional[str] = None
    new_account_type: Optional[str] = None
    new_branch_code: Optional[str] = None
    current_bank_name: Optional[str] = None
    current_account_number: Optional[str] = None
    current_account_type: Optional[str] = None
    current_branch_code: Optional[str] = None
    status: str
    requested_at: str
    rejection_reason: Optional[str] = None

    class Config:
        from_attributes = True


class BankingChangeReviewRequest(BaseModel):
    status: str  # "approved" | "rejected"
    reason: Optional[str] = None


# ------------------ User Management ------------------
class UserCreateRequest(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    role: str  # super_admin | accountant | manager | employee
    password: Optional[str] = Field(None, min_length=8, max_length=64)
    confirm_password: Optional[str] = None


class ActivateAccountRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=64)
    confirm_password: str


class AdminSetupRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=64)
    confirm_password: str


# ------------------ User Credentials Update ------------------
class UserUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8, max_length=64)


# ------------------ Portal / Employee Self-Service ------------------
class EmergencyContactCreate(BaseModel):
    full_name: str
    relationship: str
    phone: str
    email: Optional[EmailStr] = None
    is_primary: bool = False


class EmergencyContactUpdate(BaseModel):
    full_name: Optional[str] = None
    relationship: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    is_primary: Optional[bool] = None


class EmergencyContactRead(BaseModel):
    id: int
    employee_id: int
    full_name: str
    relationship: str
    phone: str
    email: Optional[str] = None
    is_primary: bool

    class Config:
        from_attributes = True


class EmployeeProfileUpdate(BaseModel):
    first_names: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    personal_email: Optional[EmailStr] = None
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_province: Optional[str] = None
    address_postal_code: Optional[str] = None
    tax_number: Optional[str] = None
    tax_ref: Optional[str] = None


class AnnouncementCreate(BaseModel):
    company_id: int
    title: str
    body: str
    is_active: bool = True


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    is_active: Optional[bool] = None


class AnnouncementRead(BaseModel):
    id: int
    company_id: int
    title: str
    body: str
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


class EmployeeTaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None


class EmployeeTaskRead(BaseModel):
    id: int
    employee_id: int
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    is_complete: bool
    completed_at: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


# ------------------ Notifications ------------------
class NotificationRead(BaseModel):
    id: int
    type: str
    message: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    is_read: bool
    created_at: str

    class Config:
        from_attributes = True

