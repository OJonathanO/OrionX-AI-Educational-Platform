"""Admin dashboard and management router."""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Document, UserRole, ProcessingStatus
from app.core.dependencies import get_admin_user
from app.schemas.admin import AdminOverview, UserSummary, DocumentJobSummary

router = APIRouter(prefix="/admin", tags=["admin"])


class UserStatusUpdate(BaseModel):
    """Schema for updating a user's active status."""
    is_active: bool


@router.get("/overview", response_model=AdminOverview)
def get_admin_overview(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Return admin dashboard overview counts."""
    total_users = db.query(User).count()
    total_documents = db.query(Document).count()

    # Active today: users with activity in last 24 hours
    since = datetime.utcnow() - timedelta(hours=24)
    active_today = (
        db.query(User)
        .filter(User.updated_at >= since)
        .count()
    )

    processing_failed = (
        db.query(Document)
        .filter(Document.processing_status == ProcessingStatus.failed)
        .count()
    )

    return AdminOverview(
        total_users=total_users,
        total_documents=total_documents,
        active_today=active_today,
        processing_failed=processing_failed,
    )


@router.get("/document-jobs")
def list_document_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """List all document processing jobs with their current status."""
    query = db.query(Document, User.email).join(User, Document.owner_id == User.id)

    if status_filter:
        try:
            status_enum = ProcessingStatus(status_filter)
            query = query.filter(Document.processing_status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status filter. Valid: {', '.join(s.value for s in ProcessingStatus)}",
            )

    total = query.count()
    results = (
        query.order_by(Document.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "items": [
            DocumentJobSummary(
                id=doc.id,
                title=doc.title,
                owner_email=email,
                status=doc.processing_status.value,
                error=doc.processing_error or None,
                created_at=doc.created_at,
            )
            for doc, email in results
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/users")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """List all users with pagination."""
    query = db.query(User)
    total = query.count()

    users = (
        query.order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    results = []
    for user in users:
        doc_count = (
            db.query(Document).filter(Document.owner_id == user.id).count()
        )
        results.append(
            UserSummary(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                role=user.role.value,
                is_active=user.is_active,
                document_count=doc_count,
                created_at=user.created_at,
            )
        )

    return {
        "items": results,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.patch("/users/{user_id}/status")
def update_user_status(
    user_id: int,
    status_data: UserStatusUpdate,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Activate or deactivate a user account."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own status",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_active = status_data.is_active
    db.commit()

    return {"id": user.id, "is_active": user.is_active}


@router.get("/errors")
def list_processing_errors(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """List recent document processing errors."""
    query = (
        db.query(Document)
        .filter(Document.processing_status == ProcessingStatus.failed)
    )
    total = query.count()

    errors = (
        query.order_by(Document.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "items": [
            {
                "document_id": doc.id,
                "title": doc.title,
                "error": doc.processing_error or "Unknown error",
                "timestamp": doc.updated_at,
            }
            for doc in errors
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
