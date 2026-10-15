"""Pydantic schemas for recommendations and bookmarks."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RecommendationResponse(BaseModel):
    """Schema for a study resource recommendation."""
    id: str
    title: str
    description: str = ""
    subject: str = ""
    topic: str = ""
    reason: str = ""
    relevance_score: float = 0.0
    resource_type: str = "document"  # document, external, generated


class BookmarkResponse(BaseModel):
    """Schema for a bookmark."""
    id: int
    resource_id: str
    created_at: datetime
