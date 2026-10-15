"""Document upload, listing, and management router."""
import os
import logging
import uuid
from typing import Optional

from fastapi import (
    APIRouter, Depends, HTTPException, UploadFile, File,
    BackgroundTasks, Query, status,
)
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Document, ProcessingStatus, User
from app.core.dependencies import get_current_active_user
from app.rag.ingestion import get_ingestion_service
from app.schemas.documents import (
    DocumentUploadResponse,
    DocumentResponse,
    DocumentListResponse,
    DocumentStatusResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}


async def _process_document_background(
    file_path: str,
    document_id: str,
    owner_id: int,
    title: str,
    file_type: str,
):
    """Background task to process an uploaded document."""
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return

        document.processing_status = ProcessingStatus.processing
        db.commit()

        ingestion = get_ingestion_service()
        chunks, chunk_count = ingestion.process_document(
            file_path=file_path,
            document_id=document_id,
            owner_id=owner_id,
            title=title,
            file_type=file_type,
        )

        # Save extracted text and chunks
        document.extracted_text = "\n\n".join(c.text for c in chunks)
        document.chunk_count = chunk_count
        document.processing_status = ProcessingStatus.completed
        db.commit()
        logger.info(f"Document {document_id} processed successfully ({chunk_count} chunks)")

    except Exception as e:
        logger.error(f"Background processing failed for document {document_id}: {e}")
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.processing_status = ProcessingStatus.failed
            document.processing_error = str(e)
            db.commit()
    finally:
        db.close()


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    subject: str = "",
    description: str = "",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Upload a document for processing.

    Accepts pdf/docx/txt files, saves to disk, creates a database record,
    and triggers background processing (text extraction, chunking, embedding).
    """
    # Validate file extension
    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Read and validate file size
    content = await file.read()
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum of {settings.MAX_UPLOAD_SIZE_MB}MB",
        )
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    # Save file to upload directory
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)

    document_id = uuid.uuid4().hex
    safe_filename = f"{document_id}_{filename}"
    file_path = os.path.join(upload_dir, safe_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    # Create document record
    title = filename.rsplit(".", 1)[0]
    document = Document(
        id=document_id,
        owner_id=current_user.id,
        title=title,
        filename=safe_filename,
        file_type=ext,
        file_size=len(content),
        subject=subject,
        description=description,
        processing_status=ProcessingStatus.pending,
    )
    db.add(document)
    db.commit()

    # Trigger background processing
    background_tasks.add_task(
        _process_document_background,
        file_path=file_path,
        document_id=document_id,
        owner_id=current_user.id,
        title=title,
        file_type=ext,
    )

    return DocumentUploadResponse(
        id=document_id,
        title=title,
        filename=safe_filename,
        file_type=ext,
        processing_status=ProcessingStatus.pending.value,
    )


@router.get("/", response_model=DocumentListResponse)
def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List the current user's documents with pagination."""
    query = db.query(Document).filter(Document.owner_id == current_user.id)
    total = query.count()

    documents = (
        query.order_by(Document.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return DocumentListResponse(
        items=[DocumentResponse.model_validate(d) for d in documents],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get document details. Only the owner can view."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if document.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
def get_document_status(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get processing status of a document."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if document.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    return DocumentStatusResponse(
        id=document.id,
        status=document.processing_status.value,
        error=document.processing_error or None,
        chunk_count=document.chunk_count,
    )


@router.get("/{document_id}/preview")
def get_document_preview(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get a preview of the extracted text (first 5000 characters)."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if document.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if document.processing_status != ProcessingStatus.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document is not ready (status: {document.processing_status.value})",
        )

    preview_text = document.extracted_text[:5000]
    return {
        "id": document.id,
        "title": document.title,
        "preview": preview_text,
        "total_length": len(document.extracted_text),
        "truncated": len(document.extracted_text) > 5000,
    }


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a document, its vector store entries, and its file."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if document.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Remove from vector store
    try:
        ingestion = get_ingestion_service()
        ingestion.delete_document(document_id)
    except Exception as e:
        logger.warning(f"Failed to delete document {document_id} from vector store: {e}")

    # Delete file from disk
    try:
        file_path = os.path.join(settings.UPLOAD_DIR, document.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logger.warning(f"Failed to delete file for document {document_id}: {e}")

    # Delete database record (cascades to chunks)
    db.delete(document)
    db.commit()
