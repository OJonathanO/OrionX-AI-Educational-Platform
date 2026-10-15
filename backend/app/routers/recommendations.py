"""Personalized study resource recommendations using TF-IDF content similarity."""
import uuid
from typing import List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    User, Document, StudyResource, Bookmark, QuizAttempt, Quiz,
    RecommendationInteraction, ChatMessage, Conversation,
)
from app.core.dependencies import get_current_active_user
from app.schemas.recommendations import RecommendationResponse, BookmarkResponse

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/")
def get_recommendations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get personalized content-based recommendations using TF-IDF cosine similarity.

    Builds a user profile from their preferred subjects, recent chat topics,
    quiz performance, and bookmarked resources. Compares against all public
    resources using TF-IDF + cosine similarity.
    """
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="sklearn is required for recommendations",
        )

    # Gather all public resources
    resources = db.query(StudyResource).filter(StudyResource.is_public == True).all()
    if not resources:
        return []

    # Build user profile text from multiple signals
    profile_parts = []

    # 1. Preferred subjects
    if current_user.preferences and current_user.preferences.preferred_subjects:
        import json
        subjects = json.loads(current_user.preferences.preferred_subjects or "[]")
        profile_parts.extend(subjects)

    # 2. Recent chat topics (from message content, last 7 days)
    recent_chats = (
        db.query(ChatMessage)
        .join(Conversation, ChatMessage.conversation_id == Conversation.id)
        .filter(
            Conversation.user_id == current_user.id,
            ChatMessage.role == "user",
            ChatMessage.created_at >= datetime.utcnow() - timedelta(days=7),
        )
        .limit(20)
        .all()
    )
    for chat in recent_chats:
        profile_parts.append(chat.content[:200])

    # 3. Quiz subjects attempted
    quiz_attempts = (
        db.query(Quiz)
        .join(QuizAttempt, Quiz.id == QuizAttempt.quiz_id)
        .filter(QuizAttempt.student_id == current_user.id)
        .distinct()
        .all()
    )
    for quiz in quiz_attempts:
        profile_parts.append(quiz.subject)

    # 4. Bookmarked resource titles and topics
    bookmarked = (
        db.query(StudyResource)
        .join(Bookmark, StudyResource.id == Bookmark.resource_id)
        .filter(Bookmark.user_id == current_user.id)
        .all()
    )
    for res in bookmarked:
        profile_parts.append(res.title)
        profile_parts.append(res.subject)
        profile_parts.append(res.topic)

    # Cold start: user has no activity signals (no chats, no quiz attempts, no bookmarks)
    has_activity = bool(recent_chats or quiz_attempts or bookmarked)
    if not has_activity:
        return [
            RecommendationResponse(
                id=r.id,
                title=r.title,
                description=r.description,
                subject=r.subject,
                topic=r.topic,
                reason="Popular resource",
                relevance_score=0.5,
                resource_type=r.source_type,
            )
            for r in resources[:10]
        ]

    user_profile = " ".join(profile_parts)

    # Build corpus: user profile + all resource texts
    resource_texts = []
    for r in resources:
        text_parts = [r.title, r.subject, r.topic, r.description, r.content_summary]
        resource_texts.append(" ".join(p for p in text_parts if p))

    corpus = [user_profile] + resource_texts

    # Compute TF-IDF and cosine similarity
    vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(corpus)

    user_vector = tfidf_matrix[0]
    resource_vectors = tfidf_matrix[1:]

    similarities = cosine_similarity(user_vector, resource_vectors).flatten()

    # Build recommendations with reasons
    recommendations = []
    for i, resource in enumerate(resources):
        score = float(similarities[i])
        if score < 0.01:
            continue

        # Determine reason based on which signal matched
        reason = "Matches your learning interests"
        if resource.subject and resource.subject.lower() in user_profile.lower():
            reason = f"Matches your interest in {resource.subject}"
        elif resource.topic and resource.topic.lower() in user_profile.lower():
            reason = f"Related to {resource.topic}"
        elif any(resource.id == b.resource_id for b in bookmarked):
            reason = "Similar to your bookmarks"

        recommendations.append(
            RecommendationResponse(
                id=resource.id,
                title=resource.title,
                description=resource.description,
                subject=resource.subject,
                topic=resource.topic,
                reason=reason,
                relevance_score=round(score, 4),
                resource_type=resource.source_type,
            )
        )

    # Sort by relevance score descending
    recommendations.sort(key=lambda x: x.relevance_score, reverse=True)

    # Save interactions
    for rec in recommendations[:10]:
        interaction = RecommendationInteraction(
            user_id=current_user.id,
            resource_id=rec.id,
            reason=rec.reason,
            relevance_score=rec.relevance_score,
        )
        db.add(interaction)
    db.commit()

    return recommendations[:20]


@router.post("/refresh")
def refresh_recommendations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Regenerate recommendations by clearing interaction history and recomputing."""
    # Clear past interactions for this user
    db.query(RecommendationInteraction).filter(
        RecommendationInteraction.user_id == current_user.id
    ).delete()
    db.commit()

    # Return fresh recommendations
    return get_recommendations(current_user, db)


@router.post("/{resource_id}/bookmark", response_model=BookmarkResponse)
def add_bookmark(
    resource_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Add a resource to the user's bookmarks."""
    resource = db.query(StudyResource).filter(StudyResource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    existing = (
        db.query(Bookmark)
        .filter(
            Bookmark.user_id == current_user.id,
            Bookmark.resource_id == resource_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already bookmarked")

    bookmark = Bookmark(
        user_id=current_user.id,
        resource_id=resource_id,
    )
    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)

    return BookmarkResponse(
        id=bookmark.id,
        resource_id=bookmark.resource_id,
        created_at=bookmark.created_at,
    )


@router.delete("/{resource_id}/bookmark", status_code=status.HTTP_204_NO_CONTENT)
def remove_bookmark(
    resource_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Remove a resource from the user's bookmarks."""
    bookmark = (
        db.query(Bookmark)
        .filter(
            Bookmark.user_id == current_user.id,
            Bookmark.resource_id == resource_id,
        )
        .first()
    )
    if not bookmark:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found")

    db.delete(bookmark)
    db.commit()
