"""Tests for analytics calculations and reporting."""
import uuid
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.models import (
    User, UserRole, Document, ProcessingStatus, Quiz, QuizQuestion,
    QuizAttempt, Bookmark, StudyResource, ChatMessage, Conversation,
)
from app.core.security import hash_password


class TestAnalyticsOverview:
    """Tests for the analytics overview endpoint."""

    def test_overview_empty_user(self, client, test_user_token):
        """Test overview for a user with no activity."""
        response = client.get(
            "/api/analytics/overview",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_documents"] == 0
        assert data["total_questions"] == 0
        assert data["quizzes_completed"] == 0
        assert data["avg_score"] == 0.0
        assert data["total_bookmarks"] == 0

    def test_overview_with_activity(self, client, test_user, test_user_token, db_session):
        """Test overview with documents, quizzes, and bookmarks."""
        # Add documents
        for i in range(3):
            doc = Document(
                id=uuid.uuid4().hex,
                owner_id=test_user.id,
                title=f"Doc {i}",
                filename=f"doc_{i}.pdf",
                file_type="pdf",
                file_size=1000,
                processing_status=ProcessingStatus.completed,
            )
            db_session.add(doc)

        # Add quiz with questions
        quiz = Quiz(
            id=uuid.uuid4().hex,
            subject="Math",
            title="Math Quiz",
            created_by=test_user.id,
        )
        db_session.add(quiz)
        db_session.flush()

        for i in range(5):
            q = QuizQuestion(
                id=uuid.uuid4().hex,
                quiz_id=quiz.id,
                question_type="multiple_choice",
                question_text=f"Q{i}",
                correct_answer="A",
                order_index=i,
            )
            db_session.add(q)

        # Add quiz attempt
        attempt = QuizAttempt(
            id=uuid.uuid4().hex,
            quiz_id=quiz.id,
            student_id=test_user.id,
            score=4.0,
            max_score=5.0,
            percentage=80.0,
            completed=True,
        )
        db_session.add(attempt)

        # Add bookmark
        resource = StudyResource(
            id=uuid.uuid4().hex,
            title="Resource",
            is_public=True,
        )
        db_session.add(resource)
        db_session.flush()

        bookmark = Bookmark(
            user_id=test_user.id,
            resource_id=resource.id,
        )
        db_session.add(bookmark)
        db_session.commit()

        response = client.get(
            "/api/analytics/overview",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_documents"] == 3
        assert data["total_questions"] == 5
        assert data["quizzes_completed"] == 1
        assert data["avg_score"] == 80.0
        assert data["total_bookmarks"] == 1

    def test_overview_avg_score_calculation(self, client, test_user, test_user_token, db_session):
        """Test that average score is calculated correctly across multiple attempts."""
        quiz = Quiz(
            id=uuid.uuid4().hex,
            subject="Science",
            title="Science Quiz",
            created_by=test_user.id,
        )
        db_session.add(quiz)
        db_session.flush()

        # Multiple attempts with different scores
        scores = [60.0, 80.0, 100.0]
        for score in scores:
            attempt = QuizAttempt(
                id=uuid.uuid4().hex,
                quiz_id=quiz.id,
                student_id=test_user.id,
                score=score / 10,
                max_score=10.0,
                percentage=score,
                completed=True,
            )
            db_session.add(attempt)
        db_session.commit()

        response = client.get(
            "/api/analytics/overview",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        data = response.json()
        assert data["quizzes_completed"] == 3
        assert data["avg_score"] == 80.0  # (60 + 80 + 100) / 3


class TestAnalyticsProgress:
    """Tests for the progress tracking endpoint."""

    def test_progress_empty(self, client, test_user_token):
        """Test progress with no quiz attempts."""
        response = client.get(
            "/api/analytics/progress",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["dates"] == []
        assert data["scores"] == []

    def test_progress_with_attempts(self, client, test_user, test_user_token, db_session):
        """Test progress returns scores over time."""
        quiz = Quiz(
            id=uuid.uuid4().hex,
            subject="Math",
            title="Quiz",
            created_by=test_user.id,
        )
        db_session.add(quiz)
        db_session.flush()

        # Create attempts on different days
        for i, score in enumerate([50.0, 70.0, 90.0]):
            attempt = QuizAttempt(
                id=uuid.uuid4().hex,
                quiz_id=quiz.id,
                student_id=test_user.id,
                score=score / 10,
                max_score=10.0,
                percentage=score,
                completed=True,
                completed_at=datetime.utcnow() - timedelta(days=2 - i),
            )
            db_session.add(attempt)
        db_session.commit()

        response = client.get(
            "/api/analytics/progress",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["dates"]) == 3
        assert len(data["scores"]) == 3
        # Scores should be in chronological order
        assert data["scores"] == sorted(data["scores"])


class TestAnalyticsTopics:
    """Tests for topic performance endpoint."""

    def test_topics_empty(self, client, test_user_token):
        """Test topics with no quiz attempts."""
        response = client.get(
            "/api/analytics/topics",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_topics_with_scores(self, client, test_user, test_user_token, db_session):
        """Test topic performance with multiple subjects."""
        # Create quizzes in different subjects
        subjects = ["Mathematics", "Physics", "History"]
        for subject in subjects:
            quiz = Quiz(
                id=uuid.uuid4().hex,
                subject=subject,
                title=f"{subject} Quiz",
                created_by=test_user.id,
            )
            db_session.add(quiz)
            db_session.flush()

            attempt = QuizAttempt(
                id=uuid.uuid4().hex,
                quiz_id=quiz.id,
                student_id=test_user.id,
                score=8.0,
                max_score=10.0,
                percentage=80.0,
                completed=True,
            )
            db_session.add(attempt)
        db_session.commit()

        response = client.get(
            "/api/analytics/topics",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        topics = [d["topic"] for d in data]
        assert "Mathematics" in topics
        assert "Physics" in topics
        assert "History" in topics


class TestAnalyticsActivity:
    """Tests for the activity tracking endpoint."""

    def test_activity_empty(self, client, test_user_token):
        """Test activity with no user actions."""
        response = client.get(
            "/api/analytics/activity",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        # Should return data points for the default 30 days
        assert len(data) == 30
        # All counts should be zero
        for point in data:
            assert point["questions"] == 0
            assert point["quizzes"] == 0
            assert point["documents"] == 0

    def test_activity_with_actions(self, client, test_user, test_user_token, db_session):
        """Test activity counts user actions correctly."""
        # Add a document
        doc = Document(
            id=uuid.uuid4().hex,
            owner_id=test_user.id,
            title="Recent Doc",
            filename="recent.pdf",
            file_type="pdf",
            file_size=1000,
            processing_status=ProcessingStatus.completed,
            created_at=datetime.utcnow(),
        )
        db_session.add(doc)

        # Add a chat message
        conv = Conversation(
            id=uuid.uuid4().hex,
            user_id=test_user.id,
            title="Test Chat",
        )
        db_session.add(conv)
        db_session.flush()

        msg = ChatMessage(
            id=uuid.uuid4().hex,
            conversation_id=conv.id,
            role="user",
            content="Hello",
            created_at=datetime.utcnow(),
        )
        db_session.add(msg)

        # Add a quiz attempt
        quiz = Quiz(
            id=uuid.uuid4().hex,
            subject="Math",
            title="Quiz",
            created_by=test_user.id,
        )
        db_session.add(quiz)
        db_session.flush()

        attempt = QuizAttempt(
            id=uuid.uuid4().hex,
            quiz_id=quiz.id,
            student_id=test_user.id,
            score=5.0,
            max_score=5.0,
            percentage=100.0,
            completed=True,
            created_at=datetime.utcnow(),
        )
        db_session.add(attempt)
        db_session.commit()

        response = client.get(
            "/api/analytics/activity?days=7",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 7

        # Find today's data point
        today = datetime.utcnow().date()
        today_data = [d for d in data if str(d["date"]) == str(today)]
        assert len(today_data) == 1
        assert today_data[0]["documents"] == 1
        assert today_data[0]["questions"] == 1
        assert today_data[0]["quizzes"] == 1

    def test_activity_custom_days(self, client, test_user_token):
        """Test activity with custom number of days."""
        response = client.get(
            "/api/analytics/activity?days=14",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 14


class TestAnalyticsAuth:
    """Tests that analytics endpoints require authentication."""

    def test_overview_requires_auth(self, client):
        response = client.get("/api/analytics/overview")
        assert response.status_code == 401

    def test_progress_requires_auth(self, client):
        response = client.get("/api/analytics/progress")
        assert response.status_code == 401

    def test_topics_requires_auth(self, client):
        response = client.get("/api/analytics/topics")
        assert response.status_code == 401

    def test_activity_requires_auth(self, client):
        response = client.get("/api/analytics/activity")
        assert response.status_code == 401
