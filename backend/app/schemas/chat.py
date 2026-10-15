"""Pydantic schemas for chat/conversation features."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SourceResponse(BaseModel):
    """Schema for a source reference in a chat response."""
    document_title: str
    page_number: Optional[int] = None
    section_heading: str = ""
    excerpt: str = ""
    relevance_score: float = 0.0


class ChatRequest(BaseModel):
    """Schema for sending a chat message."""
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_id: Optional[str] = None
    answer_style: str = Field(default="detailed", pattern="^(detailed|concise|simple)$")
    document_ids: Optional[List[str]] = None


class ChatResponse(BaseModel):
    """Schema for a chat message response."""
    message_id: str
    conversation_id: str
    content: str
    sources: List[SourceResponse] = []
    created_at: datetime


class MessageResponse(BaseModel):
    """Schema for a message in a conversation."""
    id: str
    role: str  # user, assistant, system
    content: str
    sources: List[SourceResponse] = []
    created_at: datetime


class ConversationResponse(BaseModel):
    """Schema for a conversation."""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class FeedbackRequest(BaseModel):
    """Schema for submitting feedback on a message."""
    message_id: str
    is_helpful: bool
    comment: Optional[str] = Field(None, max_length=2000)
