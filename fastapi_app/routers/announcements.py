"""
Admin CRUD for announcements and policy documents.
Employees read these via /portal/* endpoints in portal.py.
"""

import base64
import io
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from core.guards import get_current_user, require_permission
from core.tenant import get_company
from db import get_db
from orm_models import Announcement, PolicyDocument, User
from schemas import AnnouncementCreate, AnnouncementRead, AnnouncementUpdate

router = APIRouter(tags=["announcements"])

_ALLOWED_POLICY_DOC_MIME = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


# ── Announcements ─────────────────────────────────────────────────────────

@router.post("/announcements", response_model=AnnouncementRead)
def create_announcement(
    body: AnnouncementCreate,
    user: User = Depends(require_permission("MANAGE_ANNOUNCEMENTS")),
    db: Session = Depends(get_db),
):
    get_company(body.company_id, db, user)
    ann = Announcement(
        company_id=body.company_id,
        title=body.title,
        body=body.body,
        is_active=body.is_active,
        created_by=user.id,
    )
    db.add(ann)
    db.commit()
    db.refresh(ann)
    return AnnouncementRead(
        id=ann.id,
        company_id=ann.company_id,
        title=ann.title,
        body=ann.body,
        is_active=ann.is_active,
        created_at=ann.created_at.isoformat(),
    )


@router.get("/announcements")
def list_announcements(
    company_id: int,
    user: User = Depends(require_permission("MANAGE_ANNOUNCEMENTS")),
    db: Session = Depends(get_db),
):
    get_company(company_id, db, user)
    items = (
        db.query(Announcement)
        .filter(Announcement.company_id == company_id)
        .order_by(Announcement.created_at.desc())
        .all()
    )
    return [
        {
            "id": a.id,
            "title": a.title,
            "body": a.body,
            "is_active": a.is_active,
            "created_at": a.created_at.isoformat(),
        }
        for a in items
    ]


@router.patch("/announcements/{ann_id}", response_model=AnnouncementRead)
def update_announcement(
    ann_id: int,
    body: AnnouncementUpdate,
    user: User = Depends(require_permission("MANAGE_ANNOUNCEMENTS")),
    db: Session = Depends(get_db),
):
    ann = db.get(Announcement, ann_id)
    if not ann:
        raise HTTPException(status_code=404, detail="Announcement not found")
    get_company(ann.company_id, db, user)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(ann, k, v)
    db.commit()
    db.refresh(ann)
    return AnnouncementRead(
        id=ann.id,
        company_id=ann.company_id,
        title=ann.title,
        body=ann.body,
        is_active=ann.is_active,
        created_at=ann.created_at.isoformat(),
    )


@router.delete("/announcements/{ann_id}", status_code=204)
def delete_announcement(
    ann_id: int,
    user: User = Depends(require_permission("MANAGE_ANNOUNCEMENTS")),
    db: Session = Depends(get_db),
):
    ann = db.get(Announcement, ann_id)
    if not ann:
        raise HTTPException(status_code=404, detail="Announcement not found")
    get_company(ann.company_id, db, user)
    db.delete(ann)
    db.commit()
    return None


# ── Policy documents ──────────────────────────────────────────────────────

@router.post("/policy-documents")
async def upload_policy_document(
    company_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(""),
    file: UploadFile = File(...),
    user: User = Depends(require_permission("MANAGE_POLICY_DOCUMENTS")),
    db: Session = Depends(get_db),
):
    get_company(company_id, db, user)
    content_type = file.content_type or ""
    if content_type not in _ALLOWED_POLICY_DOC_MIME:
        raise HTTPException(status_code=400, detail="Only PDF, DOC, and DOCX files are accepted")
    raw = await file.read()
    if len(raw) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File must be under 10 MB")
    doc = PolicyDocument(
        company_id=company_id,
        title=title,
        description=description or None,
        file_data=base64.b64encode(raw).decode(),
        file_name=file.filename or "document",
        file_size=len(raw),
        uploaded_by=user.id,
        is_active=True,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return {"ok": True, "id": doc.id}


@router.get("/policy-documents/admin")
def list_policy_documents_admin(
    company_id: int,
    user: User = Depends(require_permission("MANAGE_POLICY_DOCUMENTS")),
    db: Session = Depends(get_db),
):
    get_company(company_id, db, user)
    docs = (
        db.query(PolicyDocument)
        .filter(PolicyDocument.company_id == company_id)
        .order_by(PolicyDocument.uploaded_at.desc())
        .all()
    )
    return [
        {
            "id": d.id,
            "title": d.title,
            "description": d.description,
            "file_name": d.file_name,
            "file_size": d.file_size,
            "is_active": d.is_active,
            "uploaded_at": d.uploaded_at.isoformat(),
        }
        for d in docs
    ]


@router.delete("/policy-documents/{doc_id}", status_code=204)
def delete_policy_document(
    doc_id: int,
    user: User = Depends(require_permission("MANAGE_POLICY_DOCUMENTS")),
    db: Session = Depends(get_db),
):
    doc = db.get(PolicyDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    get_company(doc.company_id, db, user)
    db.delete(doc)
    db.commit()
    return None
