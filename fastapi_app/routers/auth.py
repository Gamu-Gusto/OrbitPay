import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
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
from core.email import send_reset_email, send_welcome_email  # noqa: F401 (re-exported for employees router)
from core.logging_config import logger
from core.guards import get_current_user
from core.limiter import limiter
from db import get_db
from orm_models import (
    AccountantAssignment,
    ActivationToken,
    EmployeeUser,
    PasswordResetToken,
    RefreshToken,
    Role,
    User,
    UserCompany,
    UserRole,
)
from schemas import (
    ActivateAccountRequest,
    ChangePasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
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


def _user_read(user: User, roles: list[str], company_ids: list[int] | None = None) -> UserRead:
    return UserRead(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        force_password_change=bool(getattr(user, "force_password_change", False)),
        roles=roles,
        assigned_company_ids=company_ids or [],
    )


# Self-registration is disabled — accounts are created by Super Admin only.
@router.post("/register", status_code=410)
def register():
    raise HTTPException(
        status_code=410,
        detail="Self-registration is disabled. Contact your administrator.",
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, req: LoginRequest, db: Session = Depends(get_db)):
    ip = _client_ip(request)
    try:
        # Email addresses are stored lower-cased by both account creation flows.
        # Normalise login input as well so casing or pasted whitespace cannot lock
        # a valid user out.
        email = str(req.email).strip().lower()
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if not user.is_active:
            raise HTTPException(status_code=401, detail="Account is inactive")
        if not verify_password(req.password, user.password_hash):
            log_audit(db, user.id, "user.login_failed", "user", user.id, ip_address=ip)
            db.commit()
            logger.warning(f"Failed login attempt for {email} from {ip}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        roles = [db.get(Role, ur.role_id).name for ur in user.roles]
        company_ids = []
        if "accountant" in roles:
            company_ids = [
                a.company_id
                for a in db.query(AccountantAssignment).filter_by(accountant_user_id=user.id).all()
            ]
        user.last_login = datetime.utcnow()
        token = create_access_token(str(user.id), roles, company_ids)
        raw_refresh, refresh_hash = create_refresh_token()
        db.add(RefreshToken(
            token_hash=refresh_hash,
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_DAYS),
        ))
        log_audit(db, user.id, "user.login", "user", user.id, ip_address=ip)
        db.commit()
        logger.info(f"Successful login for user {user.id} from {ip}")
        token_resp = TokenResponse(
            access_token=token,
            refresh_token=raw_refresh,
            user=_user_read(user, roles, company_ids),
        )
        return JSONResponse(content=token_resp.model_dump(), headers={"Cache-Control": "no-store"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.get("/me", response_model=UserRead)
def get_current_user_info(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    roles = [db.get(Role, ur.role_id).name for ur in user.roles]
    company_ids = []
    if "accountant" in roles:
        company_ids = [
            a.company_id
            for a in db.query(AccountantAssignment).filter_by(accountant_user_id=user.id).all()
        ]
    return _user_read(user, roles, company_ids)


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
        user=_user_read(user, roles, company_ids),
    )


@router.post("/activate")
@limiter.limit("10/hour")
def activate_account(request: Request, body: ActivateAccountRequest, db: Session = Depends(get_db)):
    if body.new_password != body.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    token_hash = hash_refresh_token(body.token)
    record = db.query(ActivationToken).filter_by(token_hash=token_hash).first()
    if not record or record.used_at or record.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired activation link. Contact your administrator for a new invitation.",
        )
    user = db.get(User, record.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    user.password_hash = hash_password(body.new_password)
    user.is_active = True
    user.force_password_change = False
    record.used_at = datetime.utcnow()
    log_audit(db, user.id, "account.activated", "user", user.id)
    db.commit()
    return {"message": "Account activated. You can now log in."}


@router.post("/change-password")
def change_password(
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    user.password_hash = hash_password(body.new_password)
    user.force_password_change = False
    log_audit(db, user.id, "user.password_changed", "user", user.id)
    db.commit()
    return {"ok": True}


@router.post("/forgot-password")
@limiter.limit("5/minute")
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
        db.query(PasswordResetToken).filter_by(user_id=user.id, used=False).update({"used": True})

        raw_token = secrets.token_urlsafe(48)
        token_hash = hash_refresh_token(raw_token)
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
            send_reset_email(user.email, raw_token, frontend_url, PASSWORD_RESET_MINUTES)
        except Exception:
            pass  # Email failure must not expose token or break the flow

    return {"message": "If that email exists, a password reset link has been sent."}


@router.post("/reset-password")
@limiter.limit("5/minute")
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

    token_hash = hash_refresh_token(raw_token)
    prt = db.query(PasswordResetToken).filter_by(token_hash=token_hash).first()
    if not prt or prt.used or prt.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user = db.get(User, prt.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user.password_hash = hash_password(new_password)
    user.force_password_change = False
    prt.used = True
    db.query(RefreshToken).filter_by(user_id=user.id, revoked=False).update({"revoked": True})
    log_audit(db, user.id, "user.password_reset", "user", user.id, ip_address=_client_ip(request))
    db.commit()

    return {"message": "Password has been reset successfully."}
