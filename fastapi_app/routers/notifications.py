from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.guards import get_current_user
from db import get_db
from orm_models import Notification, User

router = APIRouter(tags=["notifications"])


@router.get("/notifications/count")
def get_notification_count(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    count = db.query(Notification).filter_by(recipient_user_id=user.id, is_read=False).count()
    return {"unread_count": count}


@router.get("/notifications")
def get_notifications(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = (
        db.query(Notification)
        .filter_by(recipient_user_id=user.id, is_read=False)
        .order_by(Notification.created_at.desc())
        .limit(20)
        .all()
    )
    return [
        {
            "id": n.id,
            "type": n.type,
            "message": n.message,
            "entity_type": n.entity_type,
            "entity_id": n.entity_id,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat(),
        }
        for n in items
    ]


@router.patch("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    n = db.get(Notification, notification_id)
    if not n or n.recipient_user_id != user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.is_read = True
    db.commit()
    return {"ok": True}


@router.patch("/notifications/read-all")
def mark_all_read(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(Notification).filter_by(recipient_user_id=user.id, is_read=False).update({"is_read": True})
    db.commit()
    return {"ok": True}
