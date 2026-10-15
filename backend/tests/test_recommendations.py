"""Tests for recommendation generation and bookmark functionality."""
import json
import uuid

import pytest
from fastapi.testclient import TestClient

from app.models import (
    User, UserRole, StudyResource, Bookmark, RecommendationInteraction,
    Quiz, QuizAttempt, ChatMessage, Conversation,
)
from app.core.security import hash_password


class TestRecommendations:
    """Tests for the recommendation endpoint."""

    def test_recommendations_empty_resources(self, client, test_user_token):
        """Test recommendations when no public resources exist."""
        response = client.get(
            "/api/recommendations/",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_recommendations_cold_start(self, client, test_user, test_user_token, db_session):
        """Test recommendations for a new user with no activity (cold start)."""
        # Create some public resources
        for i in range(3):
            resource = StudyResource(
                id=uuid.uuid4().hex,
                title=f"Resource {i}",
                description=f"Description {i}",
                subject="Mathematics",
                topic=f"Topic {i}",
                is_public=True,
            )
            db_session.add(resource)
        db_session.commit()

        response = client.get(
            "/api/recommendations/",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        # Cold start should return resources with default score
        assert len(data) > 0
        assert data[0]["reason"] == "Popular resource"

    def test_recommendations_with_user_activity(self, client, test_user, test_user_token, db_session):
        """Test recommendations based on user preferences and activity."""
        # Create resources
        math_resource = StudyResource(
            id=uuid.uuid4().hex,
            title="Calculus Guide",
            description="Learn calculus",
            subject="Mathematics",
            topic="Calculus",
            is_public=True,
        )
        history_resource = StudyResource(
            id=uuid.uuid4().hex,
            title="World History",
            description="Ancient civilizations",
            subject="History",
            topic="Ancient Rome",
            is_public=True,
        )
        db_session.add_all([math_resource, history_resource])
        db_session.commit()

        # User has mathematics preference (set in fixture)
        response = client.get(
            "/api/recommendations/",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0

    def test_recommendations_sorted_by_relevance(self, client, test_user, test_user_token, db_session):
        """Test that recommendations are sorted by relevance score."""
        # Create resources with varying relevance
        for i in range(5):
            resource = StudyResource(
                id=uuid.uuid4().hex,
                title=f"Math Resource {i}",
                description="Mathematics content",
                subject="Mathematics",
                topic="Algebra",
                is_public=True,
            )
            db_session.add(resource)
        db_session.commit()

        response = client.get(
            "/api/recommendations/",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        if len(data) > 1:
            # Scores should be in descending order
            scores = [r["relevance_score"] for r in data]
            assert scores == sorted(scores, reverse=True)

    def test_recommendations_require_auth(self, client):
        """Test that recommendations require authentication."""
        response = client.get("/api/recommendations/")
        assert response.status_code == 401

    def test_refresh_recommendations(self, client, test_user, test_user_token, db_session):
        """Test refreshing recommendations clears history and recomputes."""
        resource = StudyResource(
            id=uuid.uuid4().hex,
            title="Test Resource",
            description="Test",
            subject="Math",
            topic="Algebra",
            is_public=True,
        )
        db_session.add(resource)
        db_session.commit()

        # First call
        response1 = client.get(
            "/api/recommendations/",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response1.status_code == 200

        # Refresh
        response2 = client.post(
            "/api/recommendations/refresh",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response2.status_code == 200
        assert isinstance(response2.json(), list)


class TestBookmarks:
    """Tests for bookmark functionality."""

    def _create_resource(self, db_session, title="Test Resource"):
        resource = StudyResource(
            id=uuid.uuid4().hex,
            title=title,
            description="Test description",
            subject="Mathematics",
            topic="Algebra",
            is_public=True,
        )
        db_session.add(resource)
        db_session.commit()
        return resource

    def test_add_bookmark(self, client, test_user, test_user_token, db_session):
        """Test adding a resource to bookmarks."""
        resource = self._create_resource(db_session)

        response = client.post(
            f"/api/recommendations/{resource.id}/bookmark",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["resource_id"] == resource.id

    def test_add_duplicate_bookmark(self, client, test_user, test_user_token, db_session):
        """Test that duplicate bookmarks are rejected."""
        resource = self._create_resource(db_session)

        # First bookmark
        client.post(
            f"/api/recommendations/{resource.id}/bookmark",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        # Duplicate
        response = client.post(
            f"/api/recommendations/{resource.id}/bookmark",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 400
        assert "Already bookmarked" in response.json()["detail"]

    def test_remove_bookmark(self, client, test_user, test_user_token, db_session):
        """Test removing a bookmark."""
        resource = self._create_resource(db_session)

        # Add bookmark
        client.post(
            f"/api/recommendations/{resource.id}/bookmark",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        # Remove it
        response = client.delete(
            f"/api/recommendations/{resource.id}/bookmark",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 204

        # Verify it's gone
        bookmark = db_session.query(Bookmark).filter(
            Bookmark.resource_id == resource.id,
            Bookmark.user_id == test_user.id,
        ).first()
        assert bookmark is None

    def test_remove_nonexistent_bookmark(self, client, test_user_token):
        """Test removing a bookmark that doesn't exist."""
        response = client.delete(
            f"/api/recommendations/{uuid.uuid4().hex}/bookmark",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 404

    def test_bookmark_requires_auth(self, client):
        """Test that bookmarking requires authentication."""
        response = client.post(f"/api/recommendations/{uuid.uuid4().hex}/bookmark")
        assert response.status_code == 401
