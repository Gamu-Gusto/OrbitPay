import json
from typing import Optional

from sqlalchemy.orm import Session

from orm_models import AuditEvent


def log_audit(
    db: Session,
    user_id: Optional[int],
    action: str,
    entity_type: str = None,
    entity_id: int = None,
    payload: dict = None,
    company_id: int = None,
    ip_address: str = None,
):
    """Write an audit event. Never raises — audit failures must not break business logic."""
    try:
        db.add(AuditEvent(
            user_id=user_id,
            company_id=company_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=json.dumps(payload) if payload else None,
            ip_address=ip_address,
        ))
    except Exception:
        pass
