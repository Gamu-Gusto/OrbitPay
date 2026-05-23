import io
import smtplib
import os
from calendar import monthrange
from datetime import date, datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Tuple
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from core.audit import log_audit
from core.guards import get_current_user, require_permission
from core.tenant import get_company
from db import get_db
from models import CompanyDetails, EmployeeDetails, PayslipData, PayrollInput, ReversePayrollInput, ReversePayrollResult
from orm_models import AccountantAssignment, Company, Employee, EmployeeUser, Notification, PayrollRecord, Role, User, UserRole
from sqlalchemy import insert
from schemas import (
    BulkPayrollEmployeeResult,
    BulkPayrollRequest,
    BulkPayrollResult,
    PayrollApprovalRequest,
)
from utils import calculate_leave_income, calculate_sdl, generate_payslip_pdf, gross_from_net_pay, monthly_paye_from_gross, uif_employee

router = APIRouter(tags=["payroll"])


@router.post("/calculate-payroll", response_model=PayslipData)
async def calculate_payroll(
    input_data: PayrollInput,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    roles = getattr(user, "role_names", [])
    if input_data.company_id:
        get_company(input_data.company_id, db, user)
    if input_data.employee_id:
        emp_obj = db.get(Employee, input_data.employee_id)
        if not emp_obj:
            raise HTTPException(status_code=404, detail="Employee not found")
        if input_data.company_id and emp_obj.company_id != input_data.company_id:
            raise HTTPException(status_code=400, detail="Employee does not belong to the specified company")
        if "employee" in roles:
            link = db.query(EmployeeUser).filter_by(user_id=user.id, employee_id=emp_obj.id).first()
            if not link:
                raise HTTPException(status_code=403, detail="Forbidden")
        else:
            get_company(emp_obj.company_id, db, user)

    basic_pay = input_data.basic_pay
    other_earnings = input_data.other_earnings
    pension = input_data.pension
    medical = input_data.medical

    leave_income_details = None
    leave_income = 0.0
    if input_data.leave_days_taken > 0:
        annual_salary = basic_pay * 12
        leave_income_details = calculate_leave_income(
            annual_salary=annual_salary,
            leave_days_taken=input_data.leave_days_taken,
            total_leave_days_available=input_data.total_leave_days_available,
        )
        leave_income = leave_income_details["leave_income"]

    total_remuneration = basic_pay + other_earnings + leave_income
    sdl_details = calculate_sdl(
        total_remuneration=total_remuneration,
        annual_payroll=input_data.annual_payroll,
        excluded_amounts=input_data.excluded_amounts,
    )
    sdl_amount = sdl_details["sdl_amount"]
    total_earnings = basic_pay + other_earnings + leave_income
    paye = monthly_paye_from_gross(total_earnings)
    uif = uif_employee(total_earnings)
    total_deductions = (
        pension + medical
        + (input_data.union_fees or 0.0)
        + (input_data.other_deductions or 0.0)
        + paye + uif
    )
    net_pay = total_earnings - total_deductions

    _earn_desc = input_data.other_earnings_description or "Other Earnings"
    earnings_list: List[Tuple[str, float]] = [("Basic Pay", basic_pay)]
    if other_earnings:
        earnings_list.append((_earn_desc, other_earnings))
    if leave_income > 0:
        earnings_list.append(("Leave Income", leave_income))
    deductions_list: List[Tuple[str, float]] = [("PAYE", paye), ("UIF", uif), ("Pension", pension), ("Medical Aid", medical)]
    if (input_data.union_fees or 0.0) > 0:
        deductions_list.append(("Union Fees", input_data.union_fees))
    if (input_data.other_deductions or 0.0) > 0:
        deductions_list.append(("Other Deductions", input_data.other_deductions))

    saved_record_id = None
    if input_data.company_id:
        try:
            payrun_month = input_data.period_end.month
            payrun_year = input_data.period_end.year
            payrun_period = f"{payrun_year}-{payrun_month:02d}"
            record = PayrollRecord(
                company_id=input_data.company_id,
                employee_id=input_data.employee_id,
                payrun_month=payrun_month,
                payrun_year=payrun_year,
                payrun_period=payrun_period,
                employee_name=f"{input_data.employee.first_names} {input_data.employee.last_name}",
                employee_id_no=input_data.employee.id_no,
                pay_period_start=input_data.period_start,
                pay_period_end=input_data.period_end,
                basic_pay=basic_pay,
                other_earnings=other_earnings,
                other_earnings_description=_earn_desc,
                leave_income=leave_income,
                total_earnings=total_earnings,
                paye=paye,
                uif_employee=uif,
                uif_employer=uif,
                sdl=sdl_amount,
                pension=pension,
                medical=medical,
                total_deductions=total_deductions,
                net_pay=net_pay,
                created_by=user.id,
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            saved_record_id = record.id
        except Exception:
            db.rollback()

    return PayslipData(
        employee=input_data.employee,
        company=input_data.company,
        period_start=input_data.period_start,
        period_end=input_data.period_end,
        payment_date=input_data.payment_date,
        earnings=earnings_list,
        total_earnings=total_earnings,
        deductions=deductions_list,
        total_deductions=total_deductions,
        net_pay=net_pay,
        paye=paye,
        uif=uif,
        sdl=sdl_amount,
        leave_income=leave_income,
        sdl_details=sdl_details,
        leave_income_details=leave_income_details,
        record_id=saved_record_id,
    )


@router.post("/calculate-reverse-payroll", response_model=ReversePayrollResult)
async def calculate_reverse_payroll(
    input_data: ReversePayrollInput,
    user: User = Depends(get_current_user),
):
    try:
        leave_income_details = None
        leave_income = 0.0
        if input_data.leave_days_taken > 0:
            estimated_annual_salary = input_data.target_net_pay * 12 * 1.4
            leave_income_details = calculate_leave_income(
                annual_salary=estimated_annual_salary,
                leave_days_taken=input_data.leave_days_taken,
                total_leave_days_available=input_data.total_leave_days_available,
            )
            leave_income = leave_income_details["leave_income"]

        calculated_gross_pay = gross_from_net_pay(
            target_net_pay=input_data.target_net_pay,
            pension=input_data.pension,
            medical=input_data.medical,
        )
        total_earnings = calculated_gross_pay + input_data.other_earnings + leave_income
        total_remuneration = calculated_gross_pay + input_data.other_earnings + leave_income
        sdl_details = calculate_sdl(
            total_remuneration=total_remuneration,
            annual_payroll=input_data.annual_payroll,
            excluded_amounts=input_data.excluded_amounts,
        )
        sdl_amount = sdl_details["sdl_amount"]
        paye = monthly_paye_from_gross(total_earnings)
        uif = uif_employee(total_earnings)
        total_deductions = (
            input_data.pension + input_data.medical
            + (input_data.union_fees or 0.0)
            + (input_data.other_deductions or 0.0)
            + paye + uif
        )
        net_pay = total_earnings - total_deductions

        _earn_desc_rev = input_data.other_earnings_description or "Other Earnings"
        earnings_list: List[Tuple[str, float]] = [("Basic Pay", calculated_gross_pay)]
        if input_data.other_earnings:
            earnings_list.append((_earn_desc_rev, input_data.other_earnings))
        if leave_income > 0:
            earnings_list.append(("Leave Income", leave_income))
        deductions_list: List[Tuple[str, float]] = [
            ("PAYE", paye), ("UIF", uif),
            ("Pension", input_data.pension), ("Medical Aid", input_data.medical),
        ]
        if (input_data.union_fees or 0.0) > 0:
            deductions_list.append(("Union Fees", input_data.union_fees))
        if (input_data.other_deductions or 0.0) > 0:
            deductions_list.append(("Other Deductions", input_data.other_deductions))

        return ReversePayrollResult(
            employee=input_data.employee,
            company=input_data.company,
            period_start=input_data.period_start,
            period_end=input_data.period_end,
            payment_date=input_data.payment_date,
            calculated_gross_pay=calculated_gross_pay,
            other_earnings=input_data.other_earnings,
            pension=input_data.pension,
            medical=input_data.medical,
            earnings=earnings_list,
            total_earnings=total_earnings,
            deductions=deductions_list,
            total_deductions=total_deductions,
            net_pay=net_pay,
            paye=paye,
            uif=uif,
            sdl=sdl_amount,
            uif_employer=uif,
            leave_income=leave_income,
            sdl_details=sdl_details,
            leave_income_details=leave_income_details,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in reverse calculation: {str(e)}")


@router.post("/generate-payslip")
async def generate_payslip(
    payslip_data: PayslipData,
    user: User = Depends(get_current_user),
):
    try:
        pdf_bytes = generate_payslip_pdf(payslip_data.model_dump())
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=payslip.pdf"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {e}")


@router.post("/companies/{company_id}/payroll/bulk", response_model=BulkPayrollResult)
def bulk_payroll_run(
    company_id: int,
    body: BulkPayrollRequest,
    user: User = Depends(require_permission("RUN_PAYROLL")),
    db: Session = Depends(get_db),
):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    get_company(company_id, db, user)

    active_employees = db.query(Employee).filter(
        Employee.company_id == company_id,
        Employee.is_active == True,
    ).all()
    if not active_employees:
        raise HTTPException(status_code=400, detail="No active employees found for this company")

    _, last_day = monthrange(body.year, body.month)
    period_start = date(body.year, body.month, 1)
    period_end = date(body.year, body.month, last_day)
    period = f"{body.year}-{body.month:02d}"

    payroll_run_id = f"{company_id}_{body.year}_{body.month:02d}_{uuid4().hex[:8]}"

    # Collect (employee, PayrollRecord | None, error_str | None)
    staged: List[tuple] = []
    for emp in active_employees:
        try:
            basic_pay = float(emp.basic_salary or 0.0)
            other_earn = float(
                (emp.housing_allowance or 0.0) + (emp.transport_allowance or 0.0)
                + (emp.meal_allowance or 0.0) + (emp.other_allowances or 0.0)
            )
            pension = float(emp.pension_contribution or 0.0)
            medical = float(emp.medical_aid or 0.0)
            union_fees = float(emp.union_fees or 0.0)
            other_ded = float(emp.other_deductions or 0.0)
            total_earnings = basic_pay + other_earn
            paye = monthly_paye_from_gross(total_earnings)
            uif = uif_employee(total_earnings)
            sdl_details = calculate_sdl(total_remuneration=total_earnings, annual_payroll=0.0, excluded_amounts=0.0)
            sdl_amount = sdl_details["sdl_amount"]
            total_deductions = pension + medical + union_fees + other_ded + paye + uif
            net_pay = total_earnings - total_deductions
            pr = PayrollRecord(
                company_id=company_id,
                employee_id=emp.id,
                payrun_month=body.month,
                payrun_year=body.year,
                payrun_period=period,
                payroll_run_id=payroll_run_id,
                employee_name=f"{emp.first_names} {emp.last_name}",
                employee_id_no=emp.id_no,
                pay_period_start=period_start,
                pay_period_end=period_end,
                basic_pay=basic_pay,
                other_earnings=other_earn,
                leave_income=0.0,
                total_earnings=total_earnings,
                paye=paye,
                uif_employee=uif,
                uif_employer=uif,
                sdl=sdl_amount,
                pension=pension,
                medical=medical,
                total_deductions=total_deductions,
                net_pay=net_pay,
                created_by=user.id,
                status="draft",
            )
            db.add(pr)
            staged.append((emp, pr, None))
        except Exception as e:
            staged.append((emp, None, str(e)))

    try:
        db.flush()  # assigns IDs without committing
        log_audit(db, user.id, "payroll.bulk_run", "company", company_id, {
            "period": period,
            "payroll_run_id": payroll_run_id,
            "total": len(staged),
            "successful": sum(1 for _, pr, _ in staged if pr is not None),
        }, company_id=company_id)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save payroll records")

    results: List[BulkPayrollEmployeeResult] = []
    for emp, pr, err in staged:
        if pr is not None:
            results.append(BulkPayrollEmployeeResult(
                employee_id=emp.id,
                employee_name=f"{emp.first_names} {emp.last_name}",
                record_id=pr.id,
                basic_pay=pr.basic_pay,
                total_earnings=pr.total_earnings,
                total_deductions=pr.total_deductions,
                net_pay=pr.net_pay,
                status="success",
                distributed=False,
            ))
        else:
            results.append(BulkPayrollEmployeeResult(
                employee_id=emp.id,
                employee_name=f"{emp.first_names} {emp.last_name}",
                record_id=None,
                basic_pay=0.0, total_earnings=0.0, total_deductions=0.0, net_pay=0.0,
                status="error", error=err,
            ))

    successful = [r for r in results if r.status == "success"]
    return BulkPayrollResult(
        company_id=company_id,
        period=period,
        payroll_run_id=payroll_run_id,
        total_employees=len(results),
        successful=len(successful),
        failed=len(results) - len(successful),
        total_net_pay=sum(r.net_pay for r in successful),
        employees=results,
    )


@router.post("/companies/{company_id}/payroll/send-payslips")
def send_payslips(
    company_id: int,
    body: BulkPayrollRequest,
    user: User = Depends(require_permission("RUN_PAYROLL")),
    db: Session = Depends(get_db),
):
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")
    smtp_from = os.environ.get("SMTP_FROM", smtp_user)

    if not smtp_host or not smtp_user:
        raise HTTPException(
            status_code=503,
            detail="Email not configured. Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM in environment variables.",
        )
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    get_company(company_id, db, user)

    period = f"{body.year}-{body.month:02d}"
    records = db.query(PayrollRecord).filter(
        PayrollRecord.company_id == company_id,
        PayrollRecord.payrun_period == period,
    ).all()
    if not records:
        raise HTTPException(status_code=404, detail=f"No payroll records found for period {period}")

    sent, failed, errors = 0, 0, []
    for record in records:
        try:
            if not record.employee_id:
                errors.append(f"{record.employee_name}: No employee record linked")
                failed += 1
                continue
            link = db.query(EmployeeUser).filter_by(employee_id=record.employee_id).first()
            if not link:
                errors.append(f"{record.employee_name}: No linked user account — skipped")
                failed += 1
                continue
            linked_user = db.get(User, link.user_id)
            if not linked_user:
                errors.append(f"{record.employee_name}: Linked user not found")
                failed += 1
                continue
            emp = db.get(Employee, record.employee_id)
            emp_details = EmployeeDetails(
                first_names=emp.first_names if emp else record.employee_name,
                last_name=emp.last_name if emp else "",
                id_no=record.employee_id_no or "",
                employee_no=(emp.employee_no if emp else "") or "",
                position=(emp.position if emp else "") or "",
                tax_ref=(emp.tax_ref if emp else "") or "",
                emp_date=(emp.emp_date if emp else record.pay_period_start) or record.pay_period_start,
                bank_account_last4=(emp.bank_account_last4 if emp else None),
                pension_fund_name=(emp.pension_fund_name if emp else None),
                medical_aid_scheme_name=(emp.medical_aid_scheme_name if emp else None),
            )
            comp_details = CompanyDetails(
                company_name=company.name,
                company_reg_no=company.registration_number or "",
                company_address=company.address or "",
                uif_ref=company.uif_reference or "",
                phone=company.phone or "",
                email=company.email or "",
                run=period,
            )
            _desc = record.other_earnings_description or "Other Earnings"
            earnings_list = [("Basic Pay", record.basic_pay)]
            if record.other_earnings:
                earnings_list.append((_desc, record.other_earnings))
            if record.leave_income:
                earnings_list.append(("Leave Income", record.leave_income))
            deductions_list = [
                ("PAYE", record.paye), ("UIF", record.uif_employee),
                ("Pension", record.pension), ("Medical Aid", record.medical),
            ]
            payslip = PayslipData(
                employee=emp_details, company=comp_details,
                period_start=record.pay_period_start, period_end=record.pay_period_end,
                payment_date=record.pay_period_end,
                earnings=earnings_list, total_earnings=record.total_earnings,
                deductions=deductions_list, total_deductions=record.total_deductions,
                net_pay=record.net_pay, paye=record.paye, uif=record.uif_employee,
                sdl=record.sdl, leave_income=record.leave_income,
                sdl_details={"sdl_amount": record.sdl, "sdl_applicable": True, "annual_payroll": 0, "annual_threshold": 500000, "rate": 0.01},
                leave_income_details=None,
            )
            pdf_bytes = generate_payslip_pdf(payslip.model_dump())
            msg = MIMEMultipart()
            msg["From"] = smtp_from
            msg["To"] = linked_user.email
            msg["Subject"] = f"Payslip {period} — {company.name}"
            msg.attach(MIMEText(
                f"Dear {linked_user.first_name or record.employee_name},\n\n"
                f"Please find your payslip for {period} attached.\n"
                f"Net Pay: R{record.net_pay:,.2f}\n\nRegards,\n{company.name}",
                "plain",
            ))
            part = MIMEBase("application", "octet-stream")
            part.set_payload(pdf_bytes)
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename=payslip_{period}.pdf")
            msg.attach(part)
            with smtplib.SMTP(smtp_host, smtp_port) as srv:
                srv.starttls()
                srv.login(smtp_user, smtp_pass)
                srv.send_message(msg)
            sent += 1
        except Exception as e:
            errors.append(f"{record.employee_name}: {str(e)}")
            failed += 1

    return {"period": period, "sent": sent, "failed": failed, "errors": errors}


@router.post("/companies/{company_id}/payroll/submit")
def submit_payroll(
    company_id: int,
    body: PayrollApprovalRequest,
    user: User = Depends(require_permission("RUN_PAYROLL")),
    db: Session = Depends(get_db),
):
    get_company(company_id, db, user)
    period = f"{body.year}-{body.month:02d}"
    records = db.query(PayrollRecord).filter(
        PayrollRecord.company_id == company_id,
        PayrollRecord.payrun_period == period,
        PayrollRecord.status == "draft",
    ).all()
    if not records:
        raise HTTPException(status_code=404, detail=f"No draft payroll records found for {period}")
    for r in records:
        r.status = "submitted"
    log_audit(db, user.id, "payroll.submit", "company", company_id, {"period": period, "records": len(records)}, company_id=company_id)
    db.commit()
    return {"ok": True, "submitted": len(records), "period": period}


@router.post("/companies/{company_id}/payroll/approve")
def approve_payroll(
    company_id: int,
    body: PayrollApprovalRequest,
    user: User = Depends(require_permission("APPROVE_PAYROLL")),
    db: Session = Depends(get_db),
):
    get_company(company_id, db, user)
    period = f"{body.year}-{body.month:02d}"
    records = db.query(PayrollRecord).filter(
        PayrollRecord.company_id == company_id,
        PayrollRecord.payrun_period == period,
        PayrollRecord.status == "submitted",
    ).all()
    if not records:
        raise HTTPException(status_code=404, detail=f"No submitted payroll records found for {period}")
    now = datetime.utcnow()
    for r in records:
        r.status = "approved"
        r.approved_by = user.id
        r.approved_at = now
    log_audit(db, user.id, "payroll.approve", "company", company_id, {"period": period, "records": len(records)}, company_id=company_id)
    db.commit()
    return {"ok": True, "approved": len(records), "period": period}


@router.post("/companies/{company_id}/payroll/reject")
def reject_payroll(
    company_id: int,
    body: PayrollApprovalRequest,
    user: User = Depends(require_permission("APPROVE_PAYROLL")),
    db: Session = Depends(get_db),
):
    get_company(company_id, db, user)
    period = f"{body.year}-{body.month:02d}"
    records = db.query(PayrollRecord).filter(
        PayrollRecord.company_id == company_id,
        PayrollRecord.payrun_period == period,
        PayrollRecord.status == "submitted",
    ).all()
    if not records:
        raise HTTPException(status_code=404, detail=f"No submitted payroll records found for {period}")
    for r in records:
        r.status = "rejected"
        r.rejection_reason = body.reason or "No reason given"
    log_audit(db, user.id, "payroll.reject", "company", company_id, {"period": period, "reason": body.reason}, company_id=company_id)
    db.commit()
    return {"ok": True, "rejected": len(records), "period": period}


@router.get("/companies/{company_id}/payroll/status")
def get_payroll_period_status(
    company_id: int,
    year: int = Query(...),
    month: int = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company(company_id, db, user)
    period = f"{year}-{month:02d}"
    records = db.query(PayrollRecord).filter(
        PayrollRecord.company_id == company_id,
        PayrollRecord.payrun_period == period,
    ).all()
    if not records:
        return {"period": period, "status": "none", "count": 0}
    statuses = {r.status for r in records}
    dominant = (
        "draft" if "draft" in statuses
        else ("submitted" if "submitted" in statuses
        else ("rejected" if "rejected" in statuses else "approved"))
    )
    return {
        "period": period,
        "status": dominant,
        "count": len(records),
        "total_net_pay": round(sum(r.net_pay for r in records), 2),
        "approved_at": next((r.approved_at.isoformat() for r in records if r.approved_at), None),
        "rejection_reason": next((r.rejection_reason for r in records if r.rejection_reason), None),
    }


@router.post("/payroll-records/{record_id}/distribute")
def distribute_payslip(
    record_id: int,
    user: User = Depends(require_permission("RUN_PAYROLL")),
    db: Session = Depends(get_db),
):
    record = db.get(PayrollRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Payroll record not found")
    get_company(record.company_id, db, user)

    if not record.employee_id:
        raise HTTPException(status_code=400, detail="No employee linked to this payroll record")

    link = db.query(EmployeeUser).filter_by(employee_id=record.employee_id).first()
    if not link:
        raise HTTPException(
            status_code=400,
            detail="This employee does not have an active portal account. Create login credentials before distributing payslips.",
        )
    portal_user = db.get(User, link.user_id)
    if not portal_user or not portal_user.is_active:
        raise HTTPException(
            status_code=400,
            detail="This employee does not have an active portal account. Create login credentials before distributing payslips.",
        )

    record.distributed = True
    record.distributed_at = datetime.utcnow()
    record.distributed_by = user.id

    emp = db.get(Employee, record.employee_id)
    period_label = record.payrun_period or f"{record.payrun_year}-{record.payrun_month:02d}"
    db.execute(
        insert(Notification),
        [{
            "recipient_user_id": portal_user.id,
            "type": "PAYSLIP_AVAILABLE",
            "message": f"Your payslip for {period_label} is available.",
            "entity_type": "payroll_record",
            "entity_id": record.id,
            "is_read": False,
        }],
    )

    log_audit(db, user.id, "payslip.distributed", "payroll_record", record.id,
              {"employee_id": record.employee_id, "period": period_label},
              company_id=record.company_id)
    db.commit()
    employee_name = emp.first_names + " " + emp.last_name if emp else record.employee_name
    return {"message": f"Payslip distributed successfully.", "employee_name": employee_name}


@router.get("/companies/{company_id}/payroll/runs")
def list_payroll_runs(
    company_id: int,
    user: User = Depends(require_permission("RUN_PAYROLL")),
    db: Session = Depends(get_db),
):
    """Return one summary row per distinct payroll_run_id for this company."""
    get_company(company_id, db, user)
    records = (
        db.query(PayrollRecord)
        .filter(
            PayrollRecord.company_id == company_id,
            PayrollRecord.payroll_run_id.isnot(None),
        )
        .order_by(PayrollRecord.payrun_year.desc(), PayrollRecord.payrun_month.desc())
        .all()
    )
    runs: dict = {}
    for r in records:
        rid = r.payroll_run_id
        if rid not in runs:
            runs[rid] = {
                "payroll_run_id": rid,
                "period": r.payrun_period,
                "year": r.payrun_year,
                "month": r.payrun_month,
                "status": r.status,
                "count": 0,
                "total_net_pay": 0.0,
                "published_count": 0,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
        runs[rid]["count"] += 1
        runs[rid]["total_net_pay"] = round(runs[rid]["total_net_pay"] + r.net_pay, 2)
        if r.distributed:
            runs[rid]["published_count"] += 1
        # Dominant status
        if r.status in ("draft", "submitted", "rejected"):
            runs[rid]["status"] = r.status
        elif runs[rid]["status"] != "draft" and r.status == "approved":
            runs[rid]["status"] = "approved"
    for run in runs.values():
        run["all_published"] = run["published_count"] == run["count"] and run["count"] > 0
    return list(runs.values())


@router.post("/payroll/runs/{run_id}/publish")
def publish_payroll_run(
    run_id: str,
    user: User = Depends(require_permission("RUN_PAYROLL")),
    db: Session = Depends(get_db),
):
    """Bulk-publish all records in a payroll run to employee portals."""
    records = db.query(PayrollRecord).filter(PayrollRecord.payroll_run_id == run_id).all()
    if not records:
        raise HTTPException(status_code=404, detail="Payroll run not found")
    get_company(records[0].company_id, db, user)

    now = datetime.utcnow()
    published, skipped = 0, 0
    notifications = []
    for record in records:
        if record.distributed:
            published += 1
            continue
        if not record.employee_id:
            skipped += 1
            continue
        link = db.query(EmployeeUser).filter_by(employee_id=record.employee_id).first()
        if not link:
            skipped += 1
            continue
        portal_user = db.get(User, link.user_id)
        if not portal_user or not portal_user.is_active:
            skipped += 1
            continue
        record.distributed = True
        record.distributed_at = now
        record.distributed_by = user.id
        period_label = record.payrun_period or f"{record.payrun_year}-{record.payrun_month:02d}"
        notifications.append({
            "recipient_user_id": portal_user.id,
            "type": "PAYSLIP_AVAILABLE",
            "message": f"Your payslip for {period_label} is available.",
            "entity_type": "payroll_record",
            "entity_id": record.id,
            "is_read": False,
        })
        published += 1

    if notifications:
        db.execute(insert(Notification), notifications)

    period = records[0].payrun_period if records else run_id
    log_audit(db, user.id, "payslip.bulk_published", "payroll_run", None,
              {"run_id": run_id, "period": period, "published": published, "skipped": skipped},
              company_id=records[0].company_id if records else None)
    db.commit()
    return {"ok": True, "published": published, "skipped": skipped}


@router.post("/payroll/runs/{run_id}/unpublish")
def unpublish_payroll_run(
    run_id: str,
    user: User = Depends(require_permission("RUN_PAYROLL")),
    db: Session = Depends(get_db),
):
    """Retract payslips for an entire payroll run from employee portals."""
    records = db.query(PayrollRecord).filter(PayrollRecord.payroll_run_id == run_id).all()
    if not records:
        raise HTTPException(status_code=404, detail="Payroll run not found")
    get_company(records[0].company_id, db, user)

    count = 0
    for record in records:
        if record.distributed:
            record.distributed = False
            record.distributed_at = None
            record.distributed_by = None
            count += 1

    period = records[0].payrun_period if records else run_id
    log_audit(db, user.id, "payslip.bulk_unpublished", "payroll_run", None,
              {"run_id": run_id, "period": period, "retracted": count},
              company_id=records[0].company_id if records else None)
    db.commit()
    return {"ok": True, "retracted": count}


@router.get("/payroll-records/{record_id}/payslip")
def download_payslip_by_record(
    record_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.get(PayrollRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    roles = getattr(user, "role_names", [])
    if "employee" in roles and not any(r in roles for r in ("super_admin", "accountant", "manager")):
        link = db.query(EmployeeUser).filter_by(user_id=user.id).first()
        if not link or link.employee_id != record.employee_id:
            raise HTTPException(status_code=403, detail="Forbidden")
        # Enforce: employees can only download distributed payslips
        if not record.distributed:
            raise HTTPException(status_code=403, detail="Forbidden")
    else:
        get_company(record.company_id, db, user)
    company = db.get(Company, record.company_id)
    emp = db.get(Employee, record.employee_id) if record.employee_id else None
    name_parts = record.employee_name.split(" ", 1)
    emp_details = EmployeeDetails(
        first_names=emp.first_names if emp else name_parts[0],
        last_name=emp.last_name if emp else (name_parts[1] if len(name_parts) > 1 else ""),
        id_no=record.employee_id_no or "",
        employee_no=(emp.employee_no if emp else "") or "",
        position=(emp.position if emp else "") or "",
        tax_ref=(emp.tax_ref if emp else "") or "",
        emp_date=(emp.emp_date if emp else record.pay_period_start) or record.pay_period_start,
        bank_account_last4=(emp.bank_account_last4 if emp else None),
        pension_fund_name=(emp.pension_fund_name if emp else None),
        medical_aid_scheme_name=(emp.medical_aid_scheme_name if emp else None),
    )
    comp_details = CompanyDetails(
        company_name=company.name if company else "",
        company_reg_no=(company.registration_number if company else "") or "",
        company_address=(company.address if company else "") or "",
        uif_ref=(company.uif_reference if company else "") or "",
        phone=(company.phone if company else "") or "",
        email=(company.email if company else "") or "",
        run=record.payrun_period,
    )
    _desc = record.other_earnings_description or "Other Earnings"
    earnings_list = [("Basic Pay", record.basic_pay)]
    if record.other_earnings:
        earnings_list.append((_desc, record.other_earnings))
    if record.leave_income:
        earnings_list.append(("Leave Income", record.leave_income))
    deductions_list = [("PAYE", record.paye), ("UIF", record.uif_employee)]
    if record.pension:
        deductions_list.append(("Pension", record.pension))
    if record.medical:
        deductions_list.append(("Medical Aid", record.medical))
    payslip = PayslipData(
        employee=emp_details, company=comp_details,
        period_start=record.pay_period_start, period_end=record.pay_period_end,
        payment_date=record.pay_period_end,
        earnings=earnings_list, total_earnings=record.total_earnings,
        deductions=deductions_list, total_deductions=record.total_deductions,
        net_pay=record.net_pay, paye=record.paye, uif=record.uif_employee,
        sdl=record.sdl, leave_income=record.leave_income or 0.0,
        sdl_details={"sdl_amount": record.sdl, "sdl_applicable": True, "annual_payroll": 0, "annual_threshold": 500000, "rate": 0.01},
        leave_income_details=None,
    )
    pdf_bytes = generate_payslip_pdf(payslip.model_dump())
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="payslip_{record.payrun_period}.pdf"'},
    )
