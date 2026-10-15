"""Pydantic schemas for admin endpoints."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


class AdminOverview(BaseModel):
    """Schema for admin dashboard overview."""
    total_users: int = 0
    total_documents: int = 0
    active_today: int = 0
    processing_failed: int = 0


class UserSummary(BaseModel):
    """Schema for a user in admin user list."""
    id: int
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    document_count: int = 0
    created_at: datetime


class DocumentJobSummary(BaseModel):
    """Schema for a document processing job in admin view."""
    id: str
    title: str
    owner_email: str
    status: str
    error: Optional[str] = None
    created_at: datetime
