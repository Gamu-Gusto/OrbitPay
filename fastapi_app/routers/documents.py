import base64
import io
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import insert
from sqlalchemy.orm import Session

from core.audit import log_audit
from core.guards import get_current_user, require_permission
from db import get_db
from orm_models import (
    AccountantAssignment, Company, Employee, EmployeeDocument,
    EmployeeUser, Notification, Role, User, UserRole,
)
from schemas import DocumentReviewRequest

router = APIRouter(tags=["documents"])

_ALLOWED_DOCUMENT_MIME = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def _admin_recipient_ids(employee_id: int, db: Session) -> list[int]:
    """Return user IDs of all super_admins and accountants assigned to the employee's company.
    Returned as a list for bulk notification insert."""
    emp = db.get(Employee, employee_id)
    if not emp:
        return []
    company_id = emp.company_id

    admin_role = db.query(Role).filter_by(name="super_admin").first()
    accountant_role = db.query(Role).filter_by(name="accountant").first()

    super_admin_ids = set()
    if admin_role:
        rows = db.query(UserRole.user_id).filter_by(role_id=admin_role.id).all()
        super_admin_ids = {r.user_id for r in rows}

    accountant_ids = set()
    if accountant_role:
        assigned = db.query(AccountantAssignment).filter_by(company_id=company_id).all()
        for a in assigned:
            accountant_ids.add(a.accountant_user_id)

    return list(super_admin_ids | accountant_ids)


@router.post("/me/documents")
async def upload_my_document(
    document_type: str = Form(...),
    description: str = Form(""),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    link = db.query(EmployeeUser).filter_by(user_id=user.id).first()
    if not link:
        raise HTTPException(status_code=400, detail="No employee profile linked to your account")
    content_type = file.content_type or ""
    if content_type not in _ALLOWED_DOCUMENT_MIME:
        raise HTTPException(status_code=400, detail="File type not allowed. Upload PDF, JPEG, PNG, or Word documents only.")
    safe_name = (file.filename or "document").replace("/", "_").replace("\\", "_")
    raw = await file.read()
    if len(raw) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5 MB)")
    encoded = base64.b64encode(raw).decode()
    doc = EmployeeDocument(
        employee_id=link.employee_id,
        uploaded_by=user.id,
        document_type=document_type,
        description=description or None,
        file_name=safe_name,
        file_data=encoded,
        file_size=len(raw),
        status="pending",
    )
    db.add(doc)
    db.flush()

    emp = db.get(Employee, link.employee_id)
    log_audit(db, user.id, "document.upload", "employee", link.employee_id,
              {"type": document_type, "file": safe_name},
              company_id=emp.company_id if emp else None)

    # Bulk-notify all super_admins and assigned accountants
    emp_name = f"{emp.first_names} {emp.last_name}" if emp else "An employee"
    recipient_ids = _admin_recipient_ids(link.employee_id, db)
    if recipient_ids:
        db.execute(
            insert(Notification),
            [
                {
                    "recipient_user_id": uid,
                    "type": "DOCUMENT_UPLOADED",
                    "message": f"{emp_name} uploaded a {document_type} document.",
                    "entity_type": "employee",
                    "entity_id": link.employee_id,
                    "is_read": False,
                }
                for uid in recipient_ids
            ],
        )

    db.commit()
    db.refresh(doc)
    return {"ok": True, "id": doc.id, "status": doc.status}


@router.get("/me/documents")
def get_my_documents(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    link = db.query(EmployeeUser).filter_by(user_id=user.id).first()
    if not link:
        return []
    docs = db.query(EmployeeDocument).filter(
        EmployeeDocument.employee_id == link.employee_id
    ).order_by(EmployeeDocument.uploaded_at.desc()).all()
    return [{
        "id": d.id, "document_type": d.document_type, "description": d.description,
        "file_name": d.file_name, "file_size": d.file_size, "status": d.status,
        "rejection_reason": d.rejection_reason,
        "uploaded_at": d.uploaded_at.isoformat(),
    } for d in docs]


@router.get("/me/documents/{doc_id}/download")
def download_my_document(doc_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    link = db.query(EmployeeUser).filter_by(user_id=user.id).first()
    if not link:
        raise HTTPException(status_code=403, detail="Forbidden")
    doc = db.get(EmployeeDocument, doc_id)
    if not doc or doc.employee_id != link.employee_id:
        raise HTTPException(status_code=404, detail="Document not found")
    raw = base64.b64decode(doc.file_data)
    return StreamingResponse(
        io.BytesIO(raw), media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{doc.file_name}"'},
    )


@router.get("/documents/pending")
def get_pending_documents(
    user: User = Depends(require_permission("REVIEW_DOCUMENTS")),
    db: Session = Depends(get_db),
):
    roles = getattr(user, "role_names", [])
    is_super_admin = "super_admin" in roles

    docs = db.query(EmployeeDocument).filter(EmployeeDocument.status == "pending").order_by(EmployeeDocument.uploaded_at.asc()).all()
    result = []
    for d in docs:
        emp = db.get(Employee, d.employee_id)
        company = db.get(Company, emp.company_id) if emp else None

        # Scope accountants to their assigned companies
        if not is_super_admin and emp:
            assigned = db.query(AccountantAssignment).filter_by(
                accountant_user_id=user.id, company_id=emp.company_id
            ).first()
            if not assigned:
                continue

        result.append({
            "id": d.id,
            "employee_id": d.employee_id,
            "employee_name": f"{emp.first_names} {emp.last_name}" if emp else f"Employee #{d.employee_id}",
            "company_name": company.name if company else "—",
            "document_type": d.document_type,
            "description": d.description,
            "file_name": d.file_name,
            "file_size": d.file_size,
            "uploaded_at": d.uploaded_at.isoformat(),
            "status": d.status,
        })
    return result


@router.get("/documents/{doc_id}/download")
def download_document_admin(
    doc_id: int,
    user: User = Depends(require_permission("REVIEW_DOCUMENTS")),
    db: Session = Depends(get_db),
):
    doc = db.get(EmployeeDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    raw = base64.b64decode(doc.file_data)
    return StreamingResponse(
        io.BytesIO(raw), media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{doc.file_name}"'},
    )


@router.patch("/documents/{doc_id}/review")
def review_document(
    doc_id: int,
    body: DocumentReviewRequest,
    user: User = Depends(require_permission("APPROVE_DOCUMENTS")),
    db: Session = Depends(get_db),
):
    doc = db.get(EmployeeDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if body.status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="status must be 'approved' or 'rejected'")
    doc.status = body.status
    doc.reviewed_by = user.id
    doc.reviewed_at = datetime.utcnow()
    doc.rejection_reason = body.reason if body.status == "rejected" else None

    emp = db.get(Employee, doc.employee_id)
    log_audit(db, user.id, f"document.{body.status}", "employee", doc.employee_id,
              {"doc_id": doc_id, "reason": body.reason},
              company_id=emp.company_id if emp else None)

    # Notify the employee whose document was reviewed
    emp_link = db.query(EmployeeUser).filter_by(employee_id=doc.employee_id).first()
    if emp_link:
        notif_type = "DOCUMENT_APPROVED" if body.status == "approved" else "DOCUMENT_REJECTED"
        message = (
            f"Your {doc.document_type} document has been approved."
            if body.status == "approved"
            else f"Your {doc.document_type} document was rejected. {body.reason or ''}"
        ).strip()
        db.execute(
            insert(Notification),
            [{
                "recipient_user_id": emp_link.user_id,
                "type": notif_type,
                "message": message,
                "entity_type": "document",
                "entity_id": doc.id,
                "is_read": False,
            }],
        )

    db.commit()
    return {"ok": True, "status": doc.status}
