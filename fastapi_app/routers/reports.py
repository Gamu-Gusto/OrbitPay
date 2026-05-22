import io
from collections import defaultdict
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from core.guards import get_current_user, require_permission
from core.tenant import get_company
from db import get_db
from orm_models import (
    AccountantAssignment,
    AuditEvent,
    BankingChangeRequest,
    Company,
    Employee,
    EmployeeDocument,
    LeaveRequest,
    PayrollRecord,
    User,
    UserCompany,
)

router = APIRouter(tags=["reports"])


# ------------------ Dashboard ------------------

@router.get("/dashboard/stats")
def get_dashboard_stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    roles = getattr(user, "role_names", [])
    if "super_admin" in roles:
        company_ids = [c.id for c in db.query(Company).all()]
    else:
        cids = set()
        if "accountant" in roles:
            cids |= {a.company_id for a in db.query(AccountantAssignment).filter_by(accountant_user_id=user.id).all()}
        # TODO: remove manager scope after data migration is confirmed
        if "manager" in roles:
            cids |= {uc.company_id for uc in db.query(UserCompany).filter_by(user_id=user.id).all()}
        company_ids = list(cids)

    all_employees = db.query(Employee).filter(Employee.company_id.in_(company_ids)).all() if company_ids else []
    active_count = sum(1 for e in all_employees if e.is_active)

    alerts = []
    for emp in all_employees:
        if not emp.is_active:
            continue
        missing = []
        if not emp.id_no:
            missing.append("ID number")
        if not emp.bank_name or not emp.account_number:
            missing.append("banking details")
        if not emp.tax_number and not emp.tax_ref:
            missing.append("tax reference")
        if missing:
            alerts.append({
                "employee_id": emp.id,
                "employee_name": f"{emp.first_names} {emp.last_name}",
                "company_id": emp.company_id,
                "missing": missing,
            })

    today = date.today()
    month_records = db.query(PayrollRecord).filter(
        PayrollRecord.company_id.in_(company_ids),
        PayrollRecord.payrun_year == today.year,
        PayrollRecord.payrun_month == today.month,
    ).all() if company_ids else []

    pending_count = db.query(PayrollRecord).filter(
        PayrollRecord.company_id.in_(company_ids),
        PayrollRecord.status == "submitted",
    ).count() if company_ids else 0

    recent_activity = []
    if "super_admin" in roles or "accountant" in roles or "manager" in roles:
        events = db.query(AuditEvent).order_by(AuditEvent.timestamp.desc()).limit(8).all()
        for e in events:
            event_user = db.get(User, e.user_id) if e.user_id else None
            recent_activity.append({
                "id": e.id,
                "action": e.action,
                "entity_type": e.entity_type,
                "entity_id": e.entity_id,
                "user_name": f"{event_user.first_name or ''} {event_user.last_name or ''}".strip() if event_user else "System",
                "timestamp": e.timestamp.isoformat(),
            })

    pending_leave = 0
    pending_documents = 0
    pending_banking = 0
    if "super_admin" in roles:
        pending_leave = db.query(LeaveRequest).filter(LeaveRequest.status == "pending").count()
        pending_documents = db.query(EmployeeDocument).filter(EmployeeDocument.status == "pending").count()
        pending_banking = db.query(BankingChangeRequest).filter(BankingChangeRequest.status == "pending").count()

    return {
        "companies": len(company_ids),
        "employees": {"total": len(all_employees), "active": active_count, "inactive": len(all_employees) - active_count},
        "current_month": {
            "period": f"{today.year}-{today.month:02d}",
            "records": len(month_records),
            "total_net_pay": round(sum(r.net_pay for r in month_records), 2),
            "employees_processed": len({r.employee_id for r in month_records if r.employee_id}),
        },
        "pending_approvals": pending_count,
        "pending_leave": pending_leave,
        "pending_documents": pending_documents,
        "pending_banking": pending_banking,
        "alerts": alerts[:15],
        "recent_activity": recent_activity,
    }


# ------------------ Payroll Reports ------------------

@router.get("/reports/payroll-summary")
def payroll_summary(
    company_id: int = Query(...),
    year: int = Query(...),
    month: Optional[int] = Query(None),
    user: User = Depends(require_permission("VIEW_PAYROLL_REPORTS")),
    db: Session = Depends(get_db),
):
    get_company(company_id, db, user)
    company = db.get(Company, company_id)
    q = db.query(PayrollRecord).filter(
        PayrollRecord.company_id == company_id,
        PayrollRecord.payrun_year == year,
    )
    if month:
        q = q.filter(PayrollRecord.payrun_month == month)
    records = q.order_by(PayrollRecord.payrun_month, PayrollRecord.employee_name).all()
    return {
        "company_id": company_id,
        "company_name": company.name,
        "year": year, "month": month,
        "record_count": len(records),
        "totals": {
            "total_earnings": round(sum(r.total_earnings for r in records), 2),
            "paye": round(sum(r.paye for r in records), 2),
            "uif_employee": round(sum(r.uif_employee for r in records), 2),
            "uif_employer": round(sum(r.uif_employer for r in records), 2),
            "sdl": round(sum(r.sdl for r in records), 2),
            "pension": round(sum(r.pension for r in records), 2),
            "medical": round(sum(r.medical for r in records), 2),
            "total_deductions": round(sum(r.total_deductions for r in records), 2),
            "net_pay": round(sum(r.net_pay for r in records), 2),
        },
        "records": [{
            "id": r.id, "period": r.payrun_period, "month": r.payrun_month,
            "employee_name": r.employee_name, "employee_id_no": r.employee_id_no,
            "basic_pay": r.basic_pay, "other_earnings": r.other_earnings,
            "total_earnings": r.total_earnings,
            "paye": r.paye, "uif_employee": r.uif_employee, "uif_employer": r.uif_employer,
            "sdl": r.sdl, "pension": r.pension, "medical": r.medical,
            "total_deductions": r.total_deductions, "net_pay": r.net_pay,
            "status": r.status or "approved",
        } for r in records],
    }


@router.get("/reports/analytics")
def payroll_analytics(
    company_id: int = Query(...),
    year: int = Query(...),
    user: User = Depends(require_permission("VIEW_PAYROLL_REPORTS")),
    db: Session = Depends(get_db),
):
    get_company(company_id, db, user)
    all_records = db.query(PayrollRecord).filter(
        PayrollRecord.company_id == company_id,
        PayrollRecord.payrun_year == year,
    ).all()
    monthly = []
    for m in range(1, 13):
        recs = [r for r in all_records if r.payrun_month == m]
        monthly.append({
            "month": m,
            "employee_count": len({r.employee_id for r in recs if r.employee_id}),
            "total_gross": round(sum(r.total_earnings for r in recs), 2),
            "total_net": round(sum(r.net_pay for r in recs), 2),
            "total_paye": round(sum(r.paye for r in recs), 2),
            "total_sdl": round(sum(r.sdl for r in recs), 2),
        })
    earner_map: dict = defaultdict(float)
    for r in all_records:
        earner_map[r.employee_name] += r.net_pay
    top_earners = sorted(earner_map.items(), key=lambda x: x[1], reverse=True)[:10]
    return {
        "company_id": company_id, "year": year,
        "monthly_trend": monthly,
        "ytd": {
            "total_gross": round(sum(r.total_earnings for r in all_records), 2),
            "total_net": round(sum(r.net_pay for r in all_records), 2),
            "total_paye": round(sum(r.paye for r in all_records), 2),
            "total_uif": round(sum(r.uif_employee for r in all_records), 2),
            "total_sdl": round(sum(r.sdl for r in all_records), 2),
        },
        "top_earners": [{"name": n, "net_pay": round(v, 2)} for n, v in top_earners],
    }


@router.get("/reports/export")
def export_payroll_csv(
    company_id: int = Query(...),
    year: int = Query(...),
    month: Optional[int] = Query(None),
    user: User = Depends(require_permission("VIEW_PAYROLL_REPORTS")),
    db: Session = Depends(get_db),
):
    import csv as csv_mod
    get_company(company_id, db, user)
    company = db.get(Company, company_id)
    q = db.query(PayrollRecord).filter(
        PayrollRecord.company_id == company_id,
        PayrollRecord.payrun_year == year,
    )
    if month:
        q = q.filter(PayrollRecord.payrun_month == month)
    records = q.order_by(PayrollRecord.payrun_month, PayrollRecord.employee_name).all()
    output = io.StringIO()
    writer = csv_mod.writer(output)
    writer.writerow([
        "Period", "Employee Name", "ID Number",
        "Basic Pay", "Other Earnings", "Total Earnings",
        "PAYE", "UIF (Employee)", "UIF (Employer)", "SDL", "Pension", "Medical Aid",
        "Total Deductions", "Net Pay", "Status",
    ])
    for r in records:
        writer.writerow([
            r.payrun_period, r.employee_name, r.employee_id_no or "",
            r.basic_pay, r.other_earnings, r.total_earnings,
            r.paye, r.uif_employee, r.uif_employer, r.sdl, r.pension, r.medical,
            r.total_deductions, r.net_pay, r.status or "approved",
        ])
    output.seek(0)
    period_str = f"{year}-{month:02d}" if month else str(year)
    safe_name = (company.name if company else "payroll").replace(" ", "_")
    filename = f"payroll_{safe_name}_{period_str}.csv"
    return StreamingResponse(
        io.BytesIO(output.read().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ------------------ Compliance ------------------

@router.get("/compliance/emp201")
def emp201_report(
    company_id: int = Query(...),
    year: int = Query(...),
    month: int = Query(...),
    user: User = Depends(require_permission("VIEW_PAYROLL_REPORTS")),
    db: Session = Depends(get_db),
):
    import calendar
    get_company(company_id, db, user)
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    records = db.query(PayrollRecord).filter(
        PayrollRecord.company_id == company_id,
        PayrollRecord.payrun_year == year,
        PayrollRecord.payrun_month == month,
    ).all()
    total_paye = round(sum(r.paye for r in records), 2)
    total_uif_employee = round(sum(r.uif_employee for r in records), 2)
    total_uif_employer = round(sum(r.uif_employer for r in records), 2)
    total_uif = round(total_uif_employee + total_uif_employer, 2)
    total_sdl = round(sum(r.sdl for r in records), 2)
    total_remuneration = round(sum(r.total_earnings for r in records), 2)
    total_net = round(sum(r.net_pay for r in records), 2)
    employee_count = len({r.employee_id for r in records if r.employee_id})
    month_name = calendar.month_name[month]
    return {
        "period": f"{year}-{month:02d}", "month_name": month_name,
        "year": year, "month": month,
        "company": {
            "id": company.id, "name": company.name,
            "registration_number": company.registration_number or "",
            "uif_reference": company.uif_reference or "",
            "address": company.address or "",
        },
        "employee_count": employee_count,
        "total_remuneration": total_remuneration,
        "paye": total_paye,
        "uif_employee": total_uif_employee, "uif_employer": total_uif_employer, "uif_total": total_uif,
        "sdl": total_sdl,
        "total_liability": round(total_paye + total_uif + total_sdl, 2),
        "total_net_pay": total_net,
        "record_count": len(records),
    }


@router.get("/compliance/emp201/download")
def emp201_download(
    company_id: int = Query(...),
    year: int = Query(...),
    month: int = Query(...),
    user: User = Depends(require_permission("VIEW_PAYROLL_REPORTS")),
    db: Session = Depends(get_db),
):
    import csv as csv_mod
    data = emp201_report(company_id=company_id, year=year, month=month, user=user, db=db)
    output = io.StringIO()
    w = csv_mod.writer(output)
    w.writerow(["EMP201 Monthly Employer Declaration"])
    w.writerow(["Company", data["company"]["name"]])
    w.writerow(["Registration Number", data["company"]["registration_number"]])
    w.writerow(["UIF Reference", data["company"]["uif_reference"]])
    w.writerow(["Period", data["period"]])
    w.writerow(["Employees", data["employee_count"]])
    w.writerow([])
    w.writerow(["Description", "Amount (ZAR)"])
    w.writerow(["Total Remuneration", f"{data['total_remuneration']:.2f}"])
    w.writerow(["PAYE (Code 4102)", f"{data['paye']:.2f}"])
    w.writerow(["UIF — Employee (Code 4142)", f"{data['uif_employee']:.2f}"])
    w.writerow(["UIF — Employer", f"{data['uif_employer']:.2f}"])
    w.writerow(["SDL (Code 4149)", f"{data['sdl']:.2f}"])
    w.writerow(["Total Monthly Liability", f"{data['total_liability']:.2f}"])
    output.seek(0)
    safe = data["company"]["name"].replace(" ", "_")
    return StreamingResponse(
        io.BytesIO(output.read().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="EMP201_{safe}_{data["period"]}.csv"'},
    )


@router.get("/compliance/irp5/download")
def irp5_download(
    company_id: int = Query(...),
    year: int = Query(...),
    user: User = Depends(require_permission("VIEW_PAYROLL_REPORTS")),
    db: Session = Depends(get_db),
):
    import csv as csv_mod
    get_company(company_id, db, user)
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    records = db.query(PayrollRecord).filter(
        PayrollRecord.company_id == company_id,
        PayrollRecord.payrun_year == year,
    ).all()
    emp_totals: dict = defaultdict(lambda: {
        "name": "", "id_no": "", "tax_ref": "",
        "code_3601": 0.0, "code_3605": 0.0, "code_4102": 0.0,
        "code_4142_emp": 0.0, "code_4142_er": 0.0, "code_4115": 0.0,
        "net_pay": 0.0, "months": 0,
    })
    for r in records:
        emp = db.get(Employee, r.employee_id) if r.employee_id else None
        key = r.employee_id or r.employee_name
        d = emp_totals[key]
        d["name"] = r.employee_name
        d["id_no"] = r.employee_id_no or (emp.id_no if emp else "") or ""
        d["tax_ref"] = (emp.tax_ref or emp.tax_number if emp else "") or ""
        d["code_3601"] += r.basic_pay
        d["code_3605"] += r.other_earnings
        d["code_4102"] += r.paye
        d["code_4142_emp"] += r.uif_employee
        d["code_4142_er"] += r.uif_employer
        d["code_4115"] += r.pension
        d["net_pay"] += r.net_pay
        d["months"] += 1
    output = io.StringIO()
    w = csv_mod.writer(output)
    w.writerow(["Employer", company.name, "Registration No.", company.registration_number or "", "Tax Year", year])
    w.writerow([])
    w.writerow([
        "Employee Name", "ID Number", "Tax Reference",
        "Code 3601 — Basic Salary", "Code 3605 — Other Income", "Total Remuneration",
        "Code 4102 — PAYE", "Code 4142 — UIF (Employee)", "UIF (Employer)",
        "Code 4115 — Pension", "Net Pay", "Months Worked",
    ])
    for d in emp_totals.values():
        total_rem = round(d["code_3601"] + d["code_3605"], 2)
        w.writerow([
            d["name"], d["id_no"], d["tax_ref"],
            f"{d['code_3601']:.2f}", f"{d['code_3605']:.2f}", f"{total_rem:.2f}",
            f"{d['code_4102']:.2f}", f"{d['code_4142_emp']:.2f}", f"{d['code_4142_er']:.2f}",
            f"{d['code_4115']:.2f}", f"{d['net_pay']:.2f}", d["months"],
        ])
    output.seek(0)
    safe = company.name.replace(" ", "_")
    return StreamingResponse(
        io.BytesIO(output.read().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="IRP5_{safe}_{year}.csv"'},
    )


@router.get("/compliance/irp5/preview")
def irp5_preview(
    company_id: int = Query(...),
    year: int = Query(...),
    user: User = Depends(require_permission("VIEW_PAYROLL_REPORTS")),
    db: Session = Depends(get_db),
):
    get_company(company_id, db, user)
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    records = db.query(PayrollRecord).filter(
        PayrollRecord.company_id == company_id,
        PayrollRecord.payrun_year == year,
    ).all()
    emp_totals: dict = defaultdict(lambda: {
        "name": "", "id_no": "", "tax_ref": "",
        "basic_salary": 0.0, "other_income": 0.0,
        "paye": 0.0, "uif_employee": 0.0, "uif_employer": 0.0,
        "pension": 0.0, "net_pay": 0.0, "months": 0,
    })
    for r in records:
        emp = db.get(Employee, r.employee_id) if r.employee_id else None
        key = r.employee_id or r.employee_name
        d = emp_totals[key]
        d["name"] = r.employee_name
        d["id_no"] = r.employee_id_no or (emp.id_no if emp else "") or ""
        d["tax_ref"] = (emp.tax_ref or emp.tax_number if emp else "") or ""
        d["basic_salary"] += r.basic_pay
        d["other_income"] += r.other_earnings
        d["paye"] += r.paye
        d["uif_employee"] += r.uif_employee
        d["uif_employer"] += r.uif_employer
        d["pension"] += r.pension
        d["net_pay"] += r.net_pay
        d["months"] += 1
    employees = []
    for d in emp_totals.values():
        total_rem = round(d["basic_salary"] + d["other_income"], 2)
        employees.append({
            "name": d["name"], "id_no": d["id_no"], "tax_ref": d["tax_ref"],
            "basic_salary": round(d["basic_salary"], 2),
            "other_income": round(d["other_income"], 2),
            "total_remuneration": total_rem,
            "paye": round(d["paye"], 2),
            "uif_employee": round(d["uif_employee"], 2),
            "uif_employer": round(d["uif_employer"], 2),
            "pension": round(d["pension"], 2),
            "net_pay": round(d["net_pay"], 2),
            "months": d["months"],
        })
    return {
        "company_id": company_id, "company_name": company.name,
        "year": year, "employee_count": len(employees),
        "totals": {
            "total_remuneration": round(sum(e["total_remuneration"] for e in employees), 2),
            "paye": round(sum(e["paye"] for e in employees), 2),
            "uif_employee": round(sum(e["uif_employee"] for e in employees), 2),
            "uif_employer": round(sum(e["uif_employer"] for e in employees), 2),
            "pension": round(sum(e["pension"] for e in employees), 2),
            "net_pay": round(sum(e["net_pay"] for e in employees), 2),
        },
        "employees": employees,
    }


@router.get("/compliance/ui19/download")
def ui19_download(
    company_id: int = Query(...),
    year: int = Query(...),
    month: int = Query(...),
    user: User = Depends(require_permission("VIEW_PAYROLL_REPORTS")),
    db: Session = Depends(get_db),
):
    import csv as csv_mod
    get_company(company_id, db, user)
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    records = db.query(PayrollRecord).filter(
        PayrollRecord.company_id == company_id,
        PayrollRecord.payrun_year == year,
        PayrollRecord.payrun_month == month,
    ).all()
    output = io.StringIO()
    w = csv_mod.writer(output)
    w.writerow(["UI-19 UIF Monthly Declaration"])
    w.writerow(["Employer Name", company.name])
    w.writerow(["UIF Reference Number", company.uif_reference or ""])
    w.writerow(["Registration Number", company.registration_number or ""])
    w.writerow(["Declaration Period", f"{year}-{month:02d}"])
    w.writerow([])
    w.writerow(["Employee Name", "ID Number", "Income Type", "Gross Remuneration", "UIF Employee Contribution", "UIF Employer Contribution", "Total UIF"])
    for r in records:
        emp = db.get(Employee, r.employee_id) if r.employee_id else None
        income_type = (emp.salary_type.capitalize() if emp and emp.salary_type else "Monthly")
        uif_total = round(r.uif_employee + r.uif_employer, 2)
        w.writerow([
            r.employee_name,
            r.employee_id_no or (emp.id_no if emp else "") or "",
            income_type,
            f"{r.total_earnings:.2f}", f"{r.uif_employee:.2f}", f"{r.uif_employer:.2f}", f"{uif_total:.2f}",
        ])
    w.writerow([])
    w.writerow([
        "TOTALS", "", "",
        f"{round(sum(r.total_earnings for r in records), 2):.2f}",
        f"{round(sum(r.uif_employee for r in records), 2):.2f}",
        f"{round(sum(r.uif_employer for r in records), 2):.2f}",
        f"{round(sum(r.uif_employee + r.uif_employer for r in records), 2):.2f}",
    ])
    output.seek(0)
    safe = company.name.replace(" ", "_")
    return StreamingResponse(
        io.BytesIO(output.read().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="UI19_{safe}_{year}-{month:02d}.csv"'},
    )


@router.get("/compliance/eft/download")
def eft_download(
    company_id: int = Query(...),
    year: int = Query(...),
    month: int = Query(...),
    user: User = Depends(require_permission("VIEW_PAYROLL_REPORTS")),
    db: Session = Depends(get_db),
):
    import csv as csv_mod
    import calendar as cal_mod
    get_company(company_id, db, user)
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    records = db.query(PayrollRecord).filter(
        PayrollRecord.company_id == company_id,
        PayrollRecord.payrun_year == year,
        PayrollRecord.payrun_month == month,
    ).all()
    if not records:
        raise HTTPException(status_code=404, detail=f"No payroll records for {year}-{month:02d}")
    output = io.StringIO()
    w = csv_mod.writer(output)
    w.writerow(["Account Name", "Bank Name", "Account Number", "Branch Code", "Account Type", "Amount", "Reference", "Payment Date"])
    _, last_day = cal_mod.monthrange(year, month)
    pay_date = date(year, month, last_day).isoformat()
    period = f"{year}-{month:02d}"
    for r in records:
        emp = db.get(Employee, r.employee_id) if r.employee_id else None
        w.writerow([
            r.employee_name,
            (emp.bank_name if emp else "") or "",
            (emp.account_number if emp else "") or "",
            (emp.branch_code if emp else "") or "",
            (emp.account_type if emp else "") or "Current",
            f"{r.net_pay:.2f}",
            f"Salary {period}",
            pay_date,
        ])
    output.seek(0)
    safe = company.name.replace(" ", "_")
    return StreamingResponse(
        io.BytesIO(output.read().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="EFT_{safe}_{period}.csv"'},
    )
