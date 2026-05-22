from datetime import date
from pydantic import BaseModel
from typing import List, Tuple, Optional

class EmployeeDetails(BaseModel):
    first_names: str
    last_name: str
    id_no: str
    employee_no: str
    position: str
    tax_ref: str
    emp_date: date
    bank_account_last4: Optional[str] = None
    pension_fund_name: Optional[str] = None
    medical_aid_scheme_name: Optional[str] = None

class CompanyDetails(BaseModel):
    company_name: str
    company_reg_no: str
    company_address: str
    uif_ref: str
    phone: str
    email: str
    run: str

class PayrollInput(BaseModel):
    employee: EmployeeDetails
    company: CompanyDetails
    period_start: date
    period_end: date
    payment_date: date
    basic_pay: float
    other_earnings: float
    pension: float
    medical: float
    # SDL calculation fields
    annual_payroll: float = 0.0  # Total annual payroll for SDL threshold check
    excluded_amounts: float = 0.0  # Amounts to exclude from SDL calculation
    # Leave income fields
    leave_days_taken: int = 0  # Number of leave days taken in the period
    total_leave_days_available: int = 21  # Total annual leave days available
    # Database IDs for linking to existing records
    company_id: Optional[int] = None
    employee_id: Optional[int] = None
    # Additional employee deductions
    union_fees: float = 0.0
    other_deductions: float = 0.0
    # Label for the other_earnings line on the payslip
    other_earnings_description: str = "Other Earnings"

class PayslipData(BaseModel):
    employee: EmployeeDetails
    company: CompanyDetails
    period_start: date
    period_end: date
    payment_date: date
    earnings: List[Tuple[str, float]]
    total_earnings: float
    deductions: List[Tuple[str, float]]
    total_deductions: float
    net_pay: float
    paye: float
    uif: float
    sdl: float = 0.0
    leave_income: float = 0.0
    sdl_details: Optional[dict] = None
    leave_income_details: Optional[dict] = None
    record_id: Optional[int] = None

class ReversePayrollInput(BaseModel):
    employee: EmployeeDetails
    company: CompanyDetails
    period_start: date
    period_end: date
    payment_date: date
    target_net_pay: float
    other_earnings: float = 0.0
    pension: float
    medical: float
    # Additional employee deductions
    union_fees: float = 0.0
    other_deductions: float = 0.0
    # Label for the other_earnings line on the payslip
    other_earnings_description: str = "Other Earnings"
    # SDL calculation fields
    annual_payroll: float = 0.0  # Total annual payroll for SDL threshold check
    excluded_amounts: float = 0.0  # Amounts to exclude from SDL calculation
    # Leave income fields
    leave_days_taken: int = 0  # Number of leave days taken in the period
    total_leave_days_available: int = 21  # Total annual leave days available

class ReversePayrollResult(BaseModel):
    employee: EmployeeDetails
    company: CompanyDetails
    period_start: date
    period_end: date
    payment_date: date
    calculated_gross_pay: float
    other_earnings: float = 0.0
    pension: float
    medical: float
    earnings: List[Tuple[str, float]]
    total_earnings: float
    deductions: List[Tuple[str, float]]
    total_deductions: float
    net_pay: float
    paye: float
    uif: float
    sdl: float = 0.0
    leave_income: float = 0.0
    sdl_details: Optional[dict] = None
    leave_income_details: Optional[dict] = None

