"""Pydantic schemas for analytics and progress tracking."""
from datetime import date
from typing import List

from pydantic import BaseModel


class AnalyticsOverview(BaseModel):
    """Schema for overall analytics dashboard."""
    total_documents: int = 0
    total_questions: int = 0
    quizzes_completed: int = 0
    avg_score: float = 0.0
    total_bookmarks: int = 0


class TopicPerformance(BaseModel):
    """Schema for performance on a specific topic."""
    topic: str
    avg_score: float = 0.0
    attempt_count: int = 0


class ActivityDataPoint(BaseModel):
    """Schema for a single day's activity."""
    date: date
    questions: int = 0
    quizzes: int = 0
    documents: int = 0


class ProgressData(BaseModel):
    """Schema for progress over time."""
    dates: List[date] = []
    scores: List[float] = []
