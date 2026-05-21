from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.guards import require_permission
from db import get_db
from orm_models import AccountantAssignment, AuditEvent, User

router = APIRouter(tags=["audit"])


@router.get("/audit")
def list_audit_events(
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    action: str = Query(None),
    user: User = Depends(require_permission("VIEW_AUDIT_LOGS")),
    db: Session = Depends(get_db),
):
    q = db.query(AuditEvent).order_by(AuditEvent.timestamp.desc())
    if action:
        q = q.filter(AuditEvent.action == action)

    # Accountants only see events for their assigned companies
    roles = getattr(user, "role_names", [])
    if "accountant" in roles and "super_admin" not in roles:
        assigned_ids = [
            a.company_id
            for a in db.query(AccountantAssignment).filter_by(accountant_user_id=user.id).all()
        ]
        q = q.filter(AuditEvent.company_id.in_(assigned_ids))

    total = q.count()
    events = q.offset(offset).limit(limit).all()
    result = []
    for e in events:
        event_user = db.get(User, e.user_id) if e.user_id else None
        result.append({
            "id": e.id,
            "action": e.action,
            "entity_type": e.entity_type,
            "entity_id": e.entity_id,
            "company_id": e.company_id,
            "payload": e.payload,
            "ip_address": e.ip_address,
            "user_name": f"{event_user.first_name or ''} {event_user.last_name or ''}".strip() if event_user else "System",
            "user_email": event_user.email if event_user else None,
            "timestamp": e.timestamp.isoformat(),
        })
    return {"total": total, "events": result}
