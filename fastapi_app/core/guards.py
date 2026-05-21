from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from auth import decode_token
from db import get_db
from orm_models import User
from core.permissions import get_permissions_for_roles

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    try:
        token = credentials.credentials
        payload = decode_token(token)
        user_id = int(payload.get("sub"))
        roles = payload.get("roles", [])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Inactive user")
    user.role_names = roles
    return user


def require_roles(*allowed: str):
    def dep(user: User = Depends(get_current_user)):
        if not any(r in allowed for r in getattr(user, "role_names", [])):
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return dep


def require_permission(permission: str):
    def dep(user: User = Depends(get_current_user)):
        role_names = getattr(user, "role_names", [])
        perms = get_permissions_for_roles(role_names)
        if permission not in perms:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return dep
