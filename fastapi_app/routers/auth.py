import os
import secrets
import hashlib
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from auth import (
    REFRESH_TOKEN_DAYS,
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from core.audit import log_audit
from core.guards import get_current_user
from core.limiter import limiter
from db import get_db
from orm_models import (
    AccountantAssignment,
    EmployeeUser,
    PasswordResetToken,
    RefreshToken,
    Role,
    User,
    UserCompany,
    UserRole,
)
from schemas import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserRead,
)

# NOTE: Access tokens are returned to the frontend. If stored in localStorage they are
# vulnerable to XSS. Prefer httpOnly cookie storage in future iterations.

PASSWORD_RESET_MINUTES = 30

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _send_reset_email(to_email: str, token: str, frontend_url: str) -> None:
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")
    smtp_from = os.environ.get("SMTP_FROM", smtp_user)
    if not smtp_host or not smtp_user:
        return  # Email not configured — token is still valid; admin can retrieve via audit log
    reset_link = f"{frontend_url}/reset-password?token={token}"
    msg = MIMEMultipart("alternative")
    msg["From"] = smtp_from
    msg["To"] = to_email
    msg["Subject"] = "OrbitPay — Password Reset Request"
    body = (
        f"You requested a password reset.\n\n"
        f"Click the link below (valid for {PASSWORD_RESET_MINUTES} minutes):\n{reset_link}\n\n"
        f"If you did not request this, you can ignore this email."
    )
    msg.attach(MIMEText(body, "plain"))
    with smtplib.SMTP(smtp_host, smtp_port) as srv:
        srv.starttls()
        srv.login(smtp_user, smtp_pass)
        srv.send_message(msg)


@router.post("/register", response_model=UserRead)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    try:
        role_name = (req.role or "").strip().lower()
        if role_name not in ["super_admin", "accountant", "client_admin", "employee"]:
            raise HTTPException(status_code=400, detail="Invalid role")
        if db.query(User).filter(User.email == req.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        password_hash = hash_password(req.password)
        user = User(
            email=req.email,
            password_hash=password_hash,
            first_name=req.first_name,
            last_name=req.last_name,
        )
        db.add(user)
        db.flush()
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            raise HTTPException(status_code=400, detail="Invalid role")
        db.add(UserRole(user_id=user.id, role_id=role.id))
        if req.company_id and role_name in ("client_admin", "employee"):
            db.add(UserCompany(user_id=user.id, company_id=req.company_id))
        if req.employee_id and role_name == "employee":
            db.add(EmployeeUser(user_id=user.id, employee_id=req.employee_id))
        db.commit()
        return UserRead(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            roles=[role_name],
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, req: LoginRequest, db: Session = Depends(get_db)):
    ip = _client_ip(request)
    try:
        user = db.query(User).filter(User.email == req.email).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if not user.is_active:
            raise HTTPException(status_code=401, detail="Account is inactive")
        if not verify_password(req.password, user.password_hash):
            log_audit(db, user.id, "user.login_failed", "user", user.id, ip_address=ip)
            db.commit()
            raise HTTPException(status_code=401, detail="Invalid credentials")
        roles = [db.get(Role, ur.role_id).name for ur in user.roles]
        company_ids = []
        if "accountant" in roles:
            company_ids = [
                a.company_id
                for a in db.query(AccountantAssignment).filter_by(accountant_user_id=user.id).all()
            ]
        token = create_access_token(str(user.id), roles, company_ids)
        raw_refresh, refresh_hash = create_refresh_token()
        db.add(RefreshToken(
            token_hash=refresh_hash,
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_DAYS),
        ))
        log_audit(db, user.id, "user.login", "user", user.id, ip_address=ip)
        db.commit()
        return TokenResponse(
            access_token=token,
            refresh_token=raw_refresh,
            user=UserRead(
                id=user.id,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                is_active=user.is_active,
                roles=roles,
                assigned_company_ids=company_ids,
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.get("/me", response_model=UserRead)
def get_current_user_info(user: User = Depends(get_current_user)):
    return UserRead(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        roles=getattr(user, "role_names", []),
    )


@router.post("/logout")
def logout(
    body: Optional[LogoutRequest] = Body(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body and body.refresh_token:
        token_hash = hash_refresh_token(body.refresh_token)
        rt = db.query(RefreshToken).filter_by(token_hash=token_hash, user_id=user.id).first()
        if rt:
            rt.revoked = True
            db.commit()
    return {"ok": True}


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("20/minute")
def refresh_access_token(request: Request, body: RefreshRequest, db: Session = Depends(get_db)):
    token_hash = hash_refresh_token(body.refresh_token)
    rt = db.query(RefreshToken).filter_by(token_hash=token_hash).first()
    if not rt or rt.revoked or rt.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    user = db.get(User, rt.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    rt.revoked = True
    roles = [db.get(Role, ur.role_id).name for ur in user.roles]
    company_ids = []
    if "accountant" in roles:
        company_ids = [
            a.company_id
            for a in db.query(AccountantAssignment).filter_by(accountant_user_id=user.id).all()
        ]
    new_access = create_access_token(str(user.id), roles, company_ids)
    raw_refresh, refresh_hash = create_refresh_token()
    db.add(RefreshToken(
        token_hash=refresh_hash,
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_DAYS),
    ))
    db.commit()
    return TokenResponse(
        access_token=new_access,
        refresh_token=raw_refresh,
        user=UserRead(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            roles=roles,
            assigned_company_ids=company_ids,
        ),
    )


@router.post("/forgot-password")
def forgot_password(
    request: Request,
    body: dict = Body(...),
    db: Session = Depends(get_db),
):
    """
    Accepts {"email": "..."}.
    Always returns 200 to avoid leaking whether an account exists.
    """
    email = (body.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(status_code=422, detail="email is required")

    user = db.query(User).filter(User.email == email).first()
    if user and user.is_active:
        # Invalidate any existing unused tokens for this user
        db.query(PasswordResetToken).filter_by(user_id=user.id, used=False).update({"used": True})

        raw_token = secrets.token_urlsafe(48)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        db.add(PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(minutes=PASSWORD_RESET_MINUTES),
        ))
        log_audit(db, user.id, "user.password_reset_requested", "user", user.id,
                  ip_address=_client_ip(request))
        db.commit()

        frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
        try:
            _send_reset_email(user.email, raw_token, frontend_url)
        except Exception:
            pass  # Email failure must not expose token or break the flow

    return {"message": "If that email exists, a password reset link has been sent."}


@router.post("/reset-password")
def reset_password(
    request: Request,
    body: dict = Body(...),
    db: Session = Depends(get_db),
):
    """Accepts {"token": "...", "new_password": "..."}."""
    raw_token = (body.get("token") or "").strip()
    new_password = body.get("new_password") or ""
    if not raw_token or not new_password:
        raise HTTPException(status_code=422, detail="token and new_password are required")
    if len(new_password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")

    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    prt = db.query(PasswordResetToken).filter_by(token_hash=token_hash).first()
    if not prt or prt.used or prt.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user = db.get(User, prt.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user.password_hash = hash_password(new_password)
    prt.used = True
    # Revoke all refresh tokens on password change
    db.query(RefreshToken).filter_by(user_id=user.id, revoked=False).update({"revoked": True})
    log_audit(db, user.id, "user.password_reset", "user", user.id, ip_address=_client_ip(request))
    db.commit()

    return {"message": "Password has been reset successfully."}
