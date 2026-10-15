"""Learning analytics and progress tracking router."""
from datetime import date, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import (
    User, Document, Quiz, QuizAttempt, QuizQuestion,
    Bookmark, ChatMessage, Conversation,
)
from app.core.dependencies import get_current_active_user
from app.schemas.analytics import (
    AnalyticsOverview, TopicPerformance, ActivityDataPoint, ProgressData,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
def get_overview(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return overall analytics counts for the current user."""
    total_documents = (
        db.query(Document).filter(Document.owner_id == current_user.id).count()
    )

    total_questions = (
        db.query(QuizQuestion)
        .join(Quiz, QuizQuestion.quiz_id == Quiz.id)
        .filter(Quiz.created_by == current_user.id)
        .count()
    )

    completed_attempts = (
        db.query(QuizAttempt).filter(QuizAttempt.student_id == current_user.id).all()
    )
    quizzes_completed = len(completed_attempts)
    avg_score = (
        sum(a.percentage for a in completed_attempts) / quizzes_completed
        if quizzes_completed > 0
        else 0.0
    )

    total_bookmarks = (
        db.query(Bookmark).filter(Bookmark.user_id == current_user.id).count()
    )

    return AnalyticsOverview(
        total_documents=total_documents,
        total_questions=total_questions,
        quizzes_completed=quizzes_completed,
        avg_score=round(avg_score, 2),
        total_bookmarks=total_bookmarks,
    )


@router.get("/progress", response_model=ProgressData)
def get_progress(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return quiz scores over time for progress visualization."""
    attempts = (
        db.query(QuizAttempt)
        .filter(
            QuizAttempt.student_id == current_user.id,
            QuizAttempt.completed == True,
        )
        .order_by(QuizAttempt.completed_at.asc())
        .all()
    )

    dates = []
    scores = []
    for attempt in attempts:
        if attempt.completed_at:
            dates.append(attempt.completed_at.date())
            scores.append(attempt.percentage)

    return ProgressData(dates=dates, scores=scores)


@router.get("/topics", response_model=List[TopicPerformance])
def get_topic_performance(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return average quiz score per subject/topic."""
    results = (
        db.query(
            Quiz.subject,
            func.avg(QuizAttempt.percentage).label("avg_score"),
            func.count(QuizAttempt.id).label("attempt_count"),
        )
        .join(QuizAttempt, Quiz.id == QuizAttempt.quiz_id)
        .filter(QuizAttempt.student_id == current_user.id)
        .group_by(Quiz.subject)
        .all()
    )

    return [
        TopicPerformance(
            topic=row.subject or "General",
            avg_score=round(row.avg_score or 0.0, 2),
            attempt_count=row.attempt_count or 0,
        )
        for row in results
    ]


@router.get("/activity", response_model=List[ActivityDataPoint])
def get_activity(
    days: int = 30,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return daily activity counts for the last N days."""
    start_date = date.today() - timedelta(days=days - 1)

    # Get all activity data
    activity_map: dict = {}

    # Initialize all dates
    for i in range(days):
        d = start_date + timedelta(days=i)
        activity_map[d] = {"questions": 0, "quizzes": 0, "documents": 0}

    # Count questions (chat messages)
    questions = (
        db.query(
            func.date(ChatMessage.created_at).label("day"),
            func.count(ChatMessage.id).label("count"),
        )
        .join(Conversation, ChatMessage.conversation_id == Conversation.id)
        .filter(
            Conversation.user_id == current_user.id,
            ChatMessage.role == "user",
            func.date(ChatMessage.created_at) >= start_date,
        )
        .group_by(func.date(ChatMessage.created_at))
        .all()
    )
    for row in questions:
        d = row.day if isinstance(row.day, date) else date.fromisoformat(str(row.day))
        if d in activity_map:
            activity_map[d]["questions"] = row.count

    # Count quizzes (attempts)
    quizzes = (
        db.query(
            func.date(QuizAttempt.created_at).label("day"),
            func.count(QuizAttempt.id).label("count"),
        )
        .filter(
            QuizAttempt.student_id == current_user.id,
            func.date(QuizAttempt.created_at) >= start_date,
        )
        .group_by(func.date(QuizAttempt.created_at))
        .all()
    )
    for row in quizzes:
        d = row.day if isinstance(row.day, date) else date.fromisoformat(str(row.day))
        if d in activity_map:
            activity_map[d]["quizzes"] = row.count

    # Count documents
    documents = (
        db.query(
            func.date(Document.created_at).label("day"),
            func.count(Document.id).label("count"),
        )
        .filter(
            Document.owner_id == current_user.id,
            func.date(Document.created_at) >= start_date,
        )
        .group_by(func.date(Document.created_at))
        .all()
    )
    for row in documents:
        d = row.day if isinstance(row.day, date) else date.fromisoformat(str(row.day))
        if d in activity_map:
            activity_map[d]["documents"] = row.count

    return [
        ActivityDataPoint(
            date=d,
            questions=data["questions"],
            quizzes=data["quizzes"],
            documents=data["documents"],
        )
        for d, data in sorted(activity_map.items())
    ]
