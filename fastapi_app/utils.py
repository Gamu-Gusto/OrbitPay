from datetime import date
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import simpleSplit

# ---------------  TAX CONSTANTS  --------------------------
TAX_BRACKETS = [
    (237100, 0, 0.18),
    (370500, 42678, 0.26),
    (512800, 77362, 0.31),
    (673000, 121475, 0.36),
    (857900, 179147, 0.39),
    (1817000, 251258, 0.41),
    (float('inf'), 644489, 0.45),
]
PRIMARY_REBATE = 17235
UIF_MONTHLY_CAP = 177.12

# ---------------  SDL CONSTANTS  --------------------------
SDL_RATE = 0.01  # 1% of total remuneration
SDL_ANNUAL_THRESHOLD = 500000.0  # R500,000 annual payroll threshold

# ---------------  HELPERS  --------------------------------
def safe_float(value, default=0.0, min_val=0.0):
    try:
        if value is None or value == '':
            return default
        result = float(value)
        return max(result, min_val) if min_val is not None else result
    except (ValueError, TypeError):
        return default

def calculate_annual_tax(annual_income: float) -> float:
    if annual_income <= 0:
        return 0.0
    lower = 0.0
    for upper, base, rate in TAX_BRACKETS:
        if annual_income <= upper:
            if base == 0:
                return max(annual_income * rate, 0.0)
            return max(base + (annual_income - lower) * rate, 0.0)
        lower = upper
    return 0.0

def apply_rebates(annual_tax: float) -> float:
    return max(annual_tax - PRIMARY_REBATE, 0.0)

def monthly_paye_from_gross(gross_monthly: float) -> float:
    annual_income = gross_monthly * 12.0
    annual_tax = calculate_annual_tax(annual_income)
    annual_tax_after_rebate = apply_rebates(annual_tax)
    return round(annual_tax_after_rebate / 12.0, 2)

def uif_employee(gross_monthly: float) -> float:
    return round(min(gross_monthly * 0.01, UIF_MONTHLY_CAP), 2)

def calculate_net_pay(gross_monthly: float, pension: float, medical: float) -> float:
    """Calculate net pay from gross salary and fixed deductions"""
    paye = monthly_paye_from_gross(gross_monthly)
    uif = uif_employee(gross_monthly)
    total_deductions = paye + uif + pension + medical
    return round(gross_monthly - total_deductions, 2)

def gross_from_net_pay(target_net_pay: float, pension: float, medical: float, precision: float = 0.01, max_iterations: int = 1000) -> float:
    """
    Calculate gross salary from desired net pay using iterative approach.

    Args:
        target_net_pay: The desired net pay amount
        pension: Fixed pension deduction
        medical: Fixed medical aid deduction
        precision: Precision for convergence (default 0.01)
        max_iterations: Maximum iterations to prevent infinite loops

    Returns:
        The gross salary that results in the target net pay
    """
    if target_net_pay <= 0:
        return 0.0

    estimated_gross = target_net_pay * 1.3

    for iteration in range(max_iterations):
        current_net = calculate_net_pay(estimated_gross, pension, medical)

        if abs(current_net - target_net_pay) <= precision:
            return round(estimated_gross, 2)

        difference = target_net_pay - current_net

        if difference > 0:
            estimated_gross += difference * 1.2
        else:
            estimated_gross += difference * 1.1

        estimated_gross = max(estimated_gross, target_net_pay)

    return round(estimated_gross, 2)

def calculate_sdl(total_remuneration: float, annual_payroll: float, excluded_amounts: float = 0.0) -> dict:
    """
    Calculates SDL in compliance with the Skills Development Levies Act (Act No. 9 of 1999).
    """
    sdl_remuneration = max(total_remuneration - excluded_amounts, 0.0)
    exceeds_threshold = annual_payroll > SDL_ANNUAL_THRESHOLD
    sdl_amount = sdl_remuneration * SDL_RATE if exceeds_threshold else 0.0

    return {
        'sdl_amount': round(sdl_amount, 2),
        'total_remuneration': round(total_remuneration, 2),
        'excluded_amounts': round(excluded_amounts, 2),
        'sdl_remuneration': round(sdl_remuneration, 2),
        'annual_payroll': round(annual_payroll, 2),
        'exceeds_threshold': exceeds_threshold,
        'threshold_amount': SDL_ANNUAL_THRESHOLD,
        'sdl_rate': SDL_RATE,
        'breakdown': {
            'basic_salary': 0.0,
            'leave_pay': 0.0,
            'bonuses': 0.0,
            'overtime': 0.0,
            'commissions': 0.0,
            'taxable_allowances': 0.0,
            'excluded_reimbursements': 0.0,
            'excluded_non_taxable_allowances': 0.0,
            'excluded_retirement_contributions': 0.0
        }
    }

def calculate_leave_income(annual_salary: float, leave_days_taken: int, total_leave_days_available: int = 21) -> dict:
    """
    Calculates leave income in compliance with the Basic Conditions of Employment Act
    (Act No. 75 of 1997, Sections 20-21).
    """
    if annual_salary <= 0 or leave_days_taken <= 0:
        return {
            'leave_income': 0.0,
            'daily_rate': 0.0,
            'leave_days_taken': leave_days_taken,
            'total_leave_days_available': total_leave_days_available,
            'annual_salary': annual_salary,
            'calculation_method': 'none'
        }

    working_days_per_year = 260
    daily_rate = annual_salary / working_days_per_year
    leave_income = daily_rate * leave_days_taken
    actual_leave_days = min(leave_days_taken, total_leave_days_available)
    actual_leave_income = daily_rate * actual_leave_days if actual_leave_days > 0 else 0.0

    return {
        'leave_income': round(actual_leave_income, 2),
        'daily_rate': round(daily_rate, 2),
        'leave_days_taken': leave_days_taken,
        'actual_leave_days_paid': actual_leave_days,
        'total_leave_days_available': total_leave_days_available,
        'annual_salary': annual_salary,
        'working_days_per_year': working_days_per_year,
        'calculation_method': 'daily_rate',
        'exceeded_available_leave': leave_days_taken > total_leave_days_available,
        'unpaid_leave_days': max(0, leave_days_taken - total_leave_days_available)
    }


# ---------------  PDF GENERATION  -------------------------
def generate_payslip_pdf(data: dict) -> bytes:
    import os
    from datetime import datetime as _dt, date as _date
    from reportlab.lib.colors import HexColor, white

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    W, H = A4
    LM = 20 * mm       # left margin x
    RM = W - 20 * mm   # right edge x
    TW = RM - LM       # usable width

    # ── Design tokens ──────────────────────────────────────────────────────────
    C_NAVY   = HexColor('#1a2744')
    C_ACCENT = HexColor('#3b82f6')
    C_BG     = HexColor('#f1f5f9')
    C_BORDER = HexColor('#e2e8f0')
    C_TEXT   = HexColor('#1e293b')
    C_MUTED  = HexColor('#64748b')
    C_SLATE  = HexColor('#94a3b8')
    C_BLUE_L = HexColor('#93c5fd')
    C_ALT    = HexColor('#fafbfd')
    WHITE    = white

    # ── Helpers ────────────────────────────────────────────────────────────────
    def _parse(d):
        if not d:
            return None
        if isinstance(d, str):
            try:
                return _dt.strptime(d[:10], '%Y-%m-%d').date()
            except Exception:
                return None
        if isinstance(d, _date):
            return d
        return None

    def _fmt(d, fmt='%d %B %Y'):
        d = _parse(d)
        return d.strftime(fmt) if d else '—'

    def R(v):
        try:
            return f"R {float(v or 0):,.2f}"
        except Exception:
            return "R 0.00"

    # ── Data extraction ────────────────────────────────────────────────────────
    emp  = data.get('employee', {})
    comp = data.get('company', {})
    ps   = _parse(data.get('period_start'))
    pe   = _parse(data.get('period_end'))
    pd   = _parse(data.get('payment_date'))

    period_lbl   = ps.strftime('%B %Y') if ps else ''
    period_range = (f"{ps.strftime('%d %b')} – {pe.strftime('%d %b %Y')}" if ps and pe else '')
    pay_date_str = _fmt(pd)
    leave_det    = data.get('leave_income_details') or {}

    acc_last4 = emp.get('bank_account_last4') or "4821"

    ROW_H = 17   # table data row height
    SEC_H = 20   # section bar height

    # ══════════════════════════════════════════════════════════════════════════
    # 1. HEADER BAND  — dark navy (#1a2744), white text
    # ══════════════════════════════════════════════════════════════════════════
    HDR_H = 125
    c.setFillColor(C_NAVY)
    c.rect(0, H - HDR_H, W, HDR_H, stroke=0, fill=1)
    # Accent stripe at bottom of header
    c.setFillColor(C_ACCENT)
    c.rect(0, H - HDR_H, W, 3, stroke=0, fill=1)

    # Company name — large, prominent
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(WHITE)
    c.drawString(LM, H - 28, comp.get('company_name', 'Company'))

    # Company sub-details (left column)
    cy = H - 46
    c.setFont("Helvetica", 9)
    c.setFillColor(C_SLATE)
    reg = comp.get('company_reg_no', '')
    uif = comp.get('uif_ref', '')
    if reg or uif:
        parts = []
        if reg:
            parts.append(f"Reg No: {reg}")
        if uif:
            parts.append(f"UIF Ref: {uif}")
        c.drawString(LM, cy, "   ·   ".join(parts))
        cy -= 13
    addr = comp.get('company_address', '')
    if addr:
        for ln in simpleSplit(addr, "Helvetica", 9, TW * 0.55):
            c.drawString(LM, cy, ln)
            cy -= 12
    email = comp.get('email', '')
    phone = comp.get('phone', '')
    if email or phone:
        contact_parts = []
        if email:
            contact_parts.append(f"Email: {email}")
        if phone:
            contact_parts.append(f"Tel: {phone}")
        c.drawString(LM, cy, "   ·   ".join(contact_parts))

    # PAYSLIP label + period info (right column)
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(WHITE)
    c.drawRightString(RM, H - 28, "PAYSLIP")
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(C_BLUE_L)
    c.drawRightString(RM, H - 48, period_lbl)
    c.setFont("Helvetica", 9)
    c.setFillColor(C_SLATE)
    if period_range:
        c.drawRightString(RM, H - 63, f"Period: {period_range}")
    c.drawRightString(RM, H - 77, f"Payment Date: {pay_date_str}")

    # ══════════════════════════════════════════════════════════════════════════
    # 2. EMPLOYEE DETAILS — 2-column grid
    # ══════════════════════════════════════════════════════════════════════════
    EMP_TOP = H - HDR_H - 12
    EMP_H   = 78
    c.setFillColor(C_BG)
    c.roundRect(LM, EMP_TOP - EMP_H, TW, EMP_H, 4, stroke=0, fill=1)

    # Section label (small uppercase)
    c.setFont("Helvetica-Bold", 6.5)
    c.setFillColor(C_MUTED)
    c.drawString(LM + 8, EMP_TOP - 11, "EMPLOYEE  DETAILS")
    c.setLineWidth(0.3)
    c.setStrokeColor(C_BORDER)
    c.line(LM + 6, EMP_TOP - 15, RM - 6, EMP_TOP - 15)

    c1x = LM + 8
    c2x = LM + TW / 2 + 4
    gy  = EMP_TOP - 28
    emp_rows = [
        ("Full Name",         f"{emp.get('first_names', '')} {emp.get('last_name', '')}",
         "Employee No.",      emp.get('employee_no', '—')),
        ("ID / Passport No.", emp.get('id_no', '—'),
         "Tax Ref No.",       emp.get('tax_ref', '—')),
        ("Employment Date",   _fmt(emp.get('emp_date'), '%d %B %Y'),
         "Payment Method",    f"EFT  ····  {acc_last4}"),  # PLACEHOLDER_ACCOUNT_LAST4
    ]
    for lbl1, val1, lbl2, val2 in emp_rows:
        c.setFont("Helvetica", 7)
        c.setFillColor(C_MUTED)
        c.drawString(c1x, gy, lbl1)
        c.drawString(c2x, gy, lbl2)
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(C_TEXT)
        c.drawString(c1x, gy - 9, val1)
        c.drawString(c2x, gy - 9, val2)
        gy -= 17

    # ══════════════════════════════════════════════════════════════════════════
    # 3. EARNINGS & DEDUCTIONS — side by side, Current Month + YTD columns
    # ══════════════════════════════════════════════════════════════════════════
    TABLES_TOP = EMP_TOP - EMP_H - 12
    GAP_W = 8
    col_w = (TW - GAP_W) / 2

    earn_raw = data.get('earnings', [])

    pension_fund   = emp.get('pension_fund_name') or "Momentum Provident Fund"
    medical_scheme = emp.get('medical_aid_scheme_name') or "Discovery Health"

    ded_items = []
    for lbl, amt in data.get('deductions', []):
        if lbl == 'UIF':
            ded_items.append(("UIF  (ceiling applied)", amt))
        elif lbl == 'Pension':
            ded_items.append((f"Pension  ({pension_fund})", amt))
        elif lbl == 'Medical Aid':
            ded_items.append((f"Medical Aid  ({medical_scheme})", amt))
        else:
            ded_items.append((lbl, amt))

    def draw_table(title, items, ttl_lbl, ttl_val, tx, t_top, t_w):
        """Draw one earnings or deductions table. Returns y of table bottom."""
        CHEADER_H = 20
        ytd_rx  = tx + t_w - 6          # YTD column right edge
        curr_rx = ytd_rx - 52           # Current Month column right edge

        # Section header bar
        c.setFillColor(C_NAVY)
        c.rect(tx, t_top - SEC_H, t_w, SEC_H, stroke=0, fill=1)
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(WHITE)
        c.drawString(tx + 6, t_top - 13, title.upper())

        # Column header row
        ch_bot = t_top - SEC_H - CHEADER_H
        c.setFillColor(HexColor('#f8fafc'))
        c.rect(tx, ch_bot, t_w, CHEADER_H, stroke=0, fill=1)
        c.setFont("Helvetica-Bold", 6.5)
        c.setFillColor(C_MUTED)
        c.drawString(tx + 6, ch_bot + 7, "DESCRIPTION")
        c.drawRightString(curr_rx, ch_bot + 7, "CURRENT MONTH")
        c.drawRightString(ytd_rx,  ch_bot + 7, "YTD")
        c.setLineWidth(0.3)
        c.setStrokeColor(C_BORDER)
        c.line(tx, ch_bot, tx + t_w, ch_bot)

        # Data rows (alternating row shade)
        ry = ch_bot
        for i, (row_lbl, row_amt) in enumerate(items):
            c.setFillColor(WHITE if i % 2 == 0 else C_ALT)
            c.rect(tx, ry - ROW_H, t_w, ROW_H, stroke=0, fill=1)
            c.setFont("Helvetica", 8.5)
            c.setFillColor(C_TEXT)
            c.drawString(tx + 6, ry - 11, row_lbl)
            c.drawRightString(curr_rx, ry - 11, R(row_amt))
            # YTD not yet in data model — placeholder dash
            c.setFont("Helvetica", 8)
            c.setFillColor(C_SLATE)
            c.drawRightString(ytd_rx, ry - 11, "—")  # PLACEHOLDER_YTD
            c.setStrokeColor(C_BORDER)
            c.line(tx, ry - ROW_H, tx + t_w, ry - ROW_H)
            ry -= ROW_H

        # Total row (bold, shaded)
        c.setFillColor(C_BG)
        c.rect(tx, ry - ROW_H, t_w, ROW_H, stroke=0, fill=1)
        c.setFont("Helvetica-Bold", 8.5)
        c.setFillColor(C_TEXT)
        c.drawString(tx + 6, ry - 11, ttl_lbl.upper())
        c.drawRightString(curr_rx, ry - 11, R(ttl_val))
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(C_SLATE)
        c.drawRightString(ytd_rx, ry - 11, "—")  # PLACEHOLDER_YTD_TOTAL
        bot = ry - ROW_H

        # Outer border
        tbl_h = SEC_H + CHEADER_H + (len(items) + 1) * ROW_H
        c.setStrokeColor(C_BORDER)
        c.setLineWidth(0.5)
        c.rect(tx, t_top - tbl_h, t_w, tbl_h, stroke=1, fill=0)
        return bot

    earn_bot = draw_table(
        "Earnings", earn_raw,
        "Total Earnings", data.get('total_earnings', 0),
        LM, TABLES_TOP, col_w
    )
    ded_bot = draw_table(
        "Deductions", ded_items,
        "Total Deductions", data.get('total_deductions', 0),
        LM + col_w + GAP_W, TABLES_TOP, col_w
    )
    BELOW = min(earn_bot, ded_bot) - 14

    # ══════════════════════════════════════════════════════════════════════════
    # 4. LEAVE BALANCE
    # ══════════════════════════════════════════════════════════════════════════
    LV_BODY_H = 44
    c.setFillColor(C_NAVY)
    c.rect(LM, BELOW - SEC_H, TW, SEC_H, stroke=0, fill=1)
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(WHITE)
    c.drawString(LM + 6, BELOW - 13, "LEAVE BALANCE")

    c.setFillColor(C_BG)
    c.rect(LM, BELOW - SEC_H - LV_BODY_H, TW, LV_BODY_H, stroke=0, fill=1)
    c.setLineWidth(0.3)
    c.setStrokeColor(C_BORDER)
    c.rect(LM, BELOW - SEC_H - LV_BODY_H, TW, LV_BODY_H, stroke=1, fill=0)

    # TODO: source these from the leave_balances DB table for the relevant employee + year.
    #       Currently uses leave_income_details from payroll calc as a best-effort fallback.
    #       PLACEHOLDER_LEAVE_BALANCE
    ent  = int(leave_det.get('total_leave_days_available', 21))
    tkn  = int(leave_det.get('leave_days_taken', 0))
    clos = max(ent - tkn, 0)

    lv_y  = BELOW - SEC_H - 15
    third = TW / 3
    for i, (lbl, val) in enumerate([
        ("Annual Entitlement", f"{ent} days"),
        ("Taken This Period",  f"{tkn} days"),
        ("Closing Balance",    f"{clos} days"),
    ]):
        lx = LM + 8 + i * third
        c.setFont("Helvetica", 7)
        c.setFillColor(C_MUTED)
        c.drawString(lx, lv_y, lbl)
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(C_TEXT)
        c.drawString(lx, lv_y - 16, val)

    LV_BOT = BELOW - SEC_H - LV_BODY_H

    # ══════════════════════════════════════════════════════════════════════════
    # 5. NET PAY — visually prominent navy box, large font
    # ══════════════════════════════════════════════════════════════════════════
    NET_TOP = LV_BOT - 12
    NET_H   = 74
    c.setFillColor(C_NAVY)
    c.roundRect(LM, NET_TOP - NET_H, TW, NET_H, 6, stroke=0, fill=1)

    # "NET PAY" label (small, light blue)
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(C_BLUE_L)
    c.drawString(LM + 14, NET_TOP - 18, "NET PAY")

    # Amount — large and prominent
    c.setFont("Helvetica-Bold", 30)
    c.setFillColor(WHITE)
    c.drawString(LM + 14, NET_TOP - 50, R(data.get('net_pay', 0)))

    # Account line — PLACEHOLDER_ACCOUNT_LAST4
    c.setFont("Helvetica", 8.5)
    c.setFillColor(C_SLATE)
    c.drawRightString(RM - 10, NET_TOP - 26, f"Paid to account  ····  {acc_last4}  on  {pay_date_str}")

    # ══════════════════════════════════════════════════════════════════════════
    # 6. FOOTER — fixed at bottom; OrbitPay logo + legal text
    # ══════════════════════════════════════════════════════════════════════════
    FTR_BOT = 15 * mm
    FTR_TOP = FTR_BOT + 58

    c.setLineWidth(0.4)
    c.setStrokeColor(C_BORDER)
    c.line(LM, FTR_TOP + 4, RM, FTR_TOP + 4)

    # OrbitPay JPEG logo via ReportLab native drawImage
    jpeg_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'OrbitPayfinal.jpeg'
    )
    LOGO_Y     = FTR_BOT + 28
    logo_right = LM
    logo_drawn = False
    try:
        abs_logo = os.path.abspath(jpeg_path)
        if os.path.exists(abs_logo):
            logo_h = 40
            logo_w = 140
            c.drawImage(abs_logo, LM, LOGO_Y - 10, width=logo_w, height=logo_h,
                        preserveAspectRatio=True)
            logo_right = LM + logo_w + 10
            logo_drawn = True
    except Exception as _logo_err:
        print(f"[payslip] logo draw failed: {_logo_err}")

    if not logo_drawn:
        # Fallback: text-only branding
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(C_NAVY)
        c.drawString(LM, LOGO_Y + 8, "OrbitPay")
        logo_right = LM + 70

    c.setFont("Helvetica", 8)
    c.setFillColor(C_MUTED)
    c.drawString(logo_right, LOGO_Y + 14, "Powered by OrbitPay")
    c.drawString(logo_right, LOGO_Y + 2,  "Professional Payroll Services")

    c.setFont("Helvetica", 7.5)
    c.setFillColor(C_SLATE)
    c.drawRightString(RM, FTR_BOT + 38, "This is a computer-generated document.")
    c.drawRightString(RM, FTR_BOT + 26, "Does not require a signature.")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()
