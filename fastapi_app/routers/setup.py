import os

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from auth import hash_password
from core.audit import log_audit
from db import get_db
from orm_models import Role, SystemConfig, User, UserRole
from schemas import AdminSetupRequest

router = APIRouter(prefix="/auth/admin", tags=["setup"])


@router.get("/setup-status")
def setup_status(db: Session = Depends(get_db)):
    config = db.get(SystemConfig, "admin_setup_complete")
    return {"setup_complete": config is not None and config.value == "true"}


@router.post("/setup", status_code=201)
def admin_setup(
    body: AdminSetupRequest,
    x_setup_secret: str = Header(default=None, alias="X-Setup-Secret"),
    db: Session = Depends(get_db),
):
    expected = os.environ.get("ADMIN_SETUP_SECRET", "")
    if not expected or x_setup_secret != expected:
        raise HTTPException(status_code=403, detail="Forbidden")

    config = db.get(SystemConfig, "admin_setup_complete")
    if config and config.value == "true":
        raise HTTPException(status_code=410, detail="Setup has already been completed.")

    if not body.full_name or not body.email or not body.password or not body.confirm_password:
        raise HTTPException(status_code=422, detail="All fields are required")
    if body.password != body.confirm_password:
        raise HTTPException(status_code=422, detail="Passwords do not match")

    if db.query(User).filter(User.email == body.email.lower()).first():
        raise HTTPException(status_code=400, detail="Email already in use")

    role = db.query(Role).filter(Role.name == "super_admin").first()
    if not role:
        raise HTTPException(status_code=500, detail="super_admin role not seeded")

    name_parts = body.full_name.strip().split(" ", 1)
    new_user = User(
        email=body.email.lower(),
        password_hash=hash_password(body.password),
        first_name=name_parts[0],
        last_name=name_parts[1] if len(name_parts) > 1 else None,
        is_active=True,
        force_password_change=False,
    )
    db.add(new_user)
    db.flush()
    db.add(UserRole(user_id=new_user.id, role_id=role.id))

    if config:
        config.value = "true"
    else:
        db.add(SystemConfig(key="admin_setup_complete", value="true"))

    log_audit(db, new_user.id, "super_admin.created_via_setup", "user", new_user.id,
              payload='{"setup_route": true}')
    db.commit()
    return {"message": "Super Admin created successfully."}
