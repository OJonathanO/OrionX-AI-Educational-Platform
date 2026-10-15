"""Pydantic schemas for document management."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    """Schema returned after a document is uploaded."""
    id: str
    title: str
    filename: str
    file_type: str
    processing_status: str
    chunk_count: int = 0


class DocumentResponse(BaseModel):
    """Full document schema."""
    id: str
    owner_id: int
    title: str
    filename: str
    file_type: str
    file_size: int
    subject: str = ""
    description: str = ""
    processing_status: str
    processing_error: str = ""
    chunk_count: int = 0
    is_public: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Paginated list of documents."""
    items: List[DocumentResponse]
    total: int
    page: int
    page_size: int


class DocumentStatusResponse(BaseModel):
    """Schema for checking document processing status."""
    id: str
    status: str
    error: Optional[str] = None
    chunk_count: int = 0
