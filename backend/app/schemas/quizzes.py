"""Pydantic schemas for quiz generation and management."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class QuizGenerateRequest(BaseModel):
    """Schema for requesting quiz generation."""
    document_id: Optional[str] = None
    subject: str = Field(..., min_length=1, max_length=100)
    num_questions: int = Field(default=5, ge=1, le=50)
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")
    question_types: List[str] = Field(default=["multiple_choice"])


class QuestionResponse(BaseModel):
    """Schema for a quiz question."""
    id: str
    question_type: str  # multiple_choice, true_false, short_answer, fill_blank
    question_text: str
    options: List[str] = []
    order_index: int = 0


class QuizResponse(BaseModel):
    """Schema for quiz metadata (without questions)."""
    id: str
    title: str
    subject: str
    difficulty: str
    question_count: int
    created_at: datetime


class QuizDetailResponse(BaseModel):
    """Schema for full quiz detail including questions."""
    id: str
    title: str
    subject: str
    difficulty: str
    question_count: int
    created_at: datetime
    questions: List[QuestionResponse]


class QuizSubmitAnswer(BaseModel):
    """Schema for a single answer in a quiz submission."""
    question_id: str
    answer_text: str


class QuizSubmitRequest(BaseModel):
    """Schema for submitting quiz answers."""
    answers: List[QuizSubmitAnswer]


class QuizAnswerResult(BaseModel):
    """Schema for a single answer result."""
    question_id: str
    answer_text: str
    is_correct: bool
    correct_answer: str
    explanation: str = ""


class QuizResultResponse(BaseModel):
    """Schema for quiz submission results."""
    score: float
    max_score: float
    percentage: float
    answers: List[QuizAnswerResult]
