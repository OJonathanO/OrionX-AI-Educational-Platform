"""Conversation management router."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Conversation, ChatMessage, SourceReference
from app.core.dependencies import get_current_active_user
from app.schemas.chat import ConversationResponse, MessageResponse, SourceResponse

router = APIRouter(prefix="/conversations", tags=["conversations"])


class ConversationRename(BaseModel):
    """Schema for renaming a conversation."""
    title: str = Field(..., min_length=1, max_length=255)


def _conversation_to_response(conv: Conversation, db: Session) -> ConversationResponse:
    """Convert a Conversation model to response schema."""
    message_count = (
        db.query(ChatMessage)
        .filter(ChatMessage.conversation_id == conv.id)
        .count()
    )
    return ConversationResponse(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=message_count,
    )


def _message_to_response(msg: ChatMessage, db: Session) -> MessageResponse:
    """Convert a ChatMessage model to response schema."""
    sources = (
        db.query(SourceReference)
        .filter(SourceReference.message_id == msg.id)
        .all()
    )
    return MessageResponse(
        id=msg.id,
        role=msg.role,
        content=msg.content,
        sources=[
            SourceResponse(
                document_title=s.document_title,
                page_number=s.page_number,
                section_heading=s.section_heading,
                excerpt=s.excerpt,
                relevance_score=s.relevance_score,
            )
            for s in sources
        ],
        created_at=msg.created_at,
    )


@router.get("/")
def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List the current user's conversations with pagination."""
    query = db.query(Conversation).filter(Conversation.user_id == current_user.id)
    total = query.count()

    conversations = (
        query.order_by(Conversation.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "items": [_conversation_to_response(c, db) for c in conversations],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{conversation_id}")
def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get a conversation with all its messages and sources."""
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
        .first()
    )
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "messages": [_message_to_response(m, db) for m in messages],
    }


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a conversation and all its messages."""
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
        .first()
    )
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    db.delete(conversation)
    db.commit()


@router.patch("/{conversation_id}")
def rename_conversation(
    conversation_id: str,
    rename_data: ConversationRename,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Rename a conversation."""
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
        .first()
    )
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    conversation.title = rename_data.title
    db.commit()
    db.refresh(conversation)

    return _conversation_to_response(conversation, db)
