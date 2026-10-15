"""Tests for authentication: register, login, unauthorized access, ownership."""
import pytest
from fastapi.testclient import TestClient

from app.models import User, UserRole
from app.core.security import verify_password


class TestRegister:
    """Tests for user registration."""

    def test_register_success(self, client):
        """Test successful user registration."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
                "full_name": "New User",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    def test_register_duplicate_email(self, client, test_user):
        """Test registration with an already registered email."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "anotherpassword123",
                "full_name": "Duplicate User",
            },
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_register_invalid_email(self, client):
        """Test registration with an invalid email format."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "not-an-email",
                "password": "securepassword123",
                "full_name": "Invalid Email User",
            },
        )
        assert response.status_code == 422

    def test_register_short_password(self, client):
        """Test registration with a password that is too short."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "shortpass@example.com",
                "password": "short",
                "full_name": "Short Password User",
            },
        )
        assert response.status_code == 422

    def test_register_missing_fields(self, client):
        """Test registration with missing required fields."""
        response = client.post(
            "/api/auth/register",
            json={"email": "missing@example.com"},
        )
        assert response.status_code == 422


class TestLogin:
    """Tests for user login."""

    def test_login_success(self, client, test_user):
        """Test successful login with correct credentials."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, test_user):
        """Test login with incorrect password."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, client):
        """Test login with an email that doesn't exist."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "somepassword123",
            },
        )
        assert response.status_code == 401

    def test_login_inactive_user(self, client, db_session):
        """Test login with a deactivated account."""
        from app.core.security import hash_password

        inactive_user = User(
            email="inactive@example.com",
            hashed_password=hash_password("password123"),
            full_name="Inactive User",
            role=UserRole.student,
            is_active=False,
        )
        db_session.add(inactive_user)
        db_session.commit()

        response = client.post(
            "/api/auth/login",
            json={
                "email": "inactive@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 403
        assert "deactivated" in response.json()["detail"]


class TestUnauthorizedAccess:
    """Tests for unauthorized access to protected endpoints."""

    def test_access_without_token(self, client):
        """Test accessing a protected endpoint without a token."""
        response = client.get("/api/users/me")
        assert response.status_code == 401

    def test_access_with_invalid_token(self, client):
        """Test accessing a protected endpoint with an invalid token."""
        response = client.get(
            "/api/users/me",
            headers={"Authorization": "Bearer invalid-token-here"},
        )
        assert response.status_code == 401

    def test_access_with_malformed_token(self, client):
        """Test accessing a protected endpoint with a malformed token."""
        response = client.get(
            "/api/users/me",
            headers={"Authorization": "Bearer not.a.valid.jwt"},
        )
        assert response.status_code == 401

    def test_documents_require_auth(self, client):
        """Test that document endpoints require authentication."""
        response = client.get("/api/documents/")
        assert response.status_code == 401

    def test_chat_requires_auth(self, client):
        """Test that chat endpoints require authentication."""
        response = client.post(
            "/api/chat/",
            json={"message": "Hello"},
        )
        assert response.status_code == 401

    def test_quizzes_require_auth(self, client):
        """Test that quiz endpoints require authentication."""
        response = client.get("/api/quizzes/")
        assert response.status_code == 401


class TestOwnershipEnforcement:
    """Tests that users can only access their own resources."""

    def test_cannot_view_other_users_document(self, client, test_user, test_user_2, test_user_token, db_session):
        """Test that a user cannot view another user's document."""
        import uuid
        from app.models import Document, ProcessingStatus

        # Create a document owned by test_user_2
        doc = Document(
            id=uuid.uuid4().hex,
            owner_id=test_user_2.id,
            title="Private Document",
            filename="private.pdf",
            file_type="pdf",
            file_size=1000,
            processing_status=ProcessingStatus.completed,
        )
        db_session.add(doc)
        db_session.commit()

        # Try to access as test_user
        response = client.get(
            f"/api/documents/{doc.id}",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        # Should get 404 (not 403) to avoid leaking existence
        assert response.status_code == 404

    def test_cannot_delete_other_users_document(self, client, test_user, test_user_2, test_user_token, db_session):
        """Test that a user cannot delete another user's document."""
        import uuid
        from app.models import Document, ProcessingStatus

        doc = Document(
            id=uuid.uuid4().hex,
            owner_id=test_user_2.id,
            title="Protected Document",
            filename="protected.pdf",
            file_type="pdf",
            file_size=1000,
            processing_status=ProcessingStatus.completed,
        )
        db_session.add(doc)
        db_session.commit()

        response = client.delete(
            f"/api/documents/{doc.id}",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 404

    def test_cannot_view_other_users_conversation(self, client, test_user, test_user_2, test_user_token, db_session):
        """Test that a user cannot view another user's conversation."""
        import uuid
        from app.models import Conversation

        conv = Conversation(
            id=uuid.uuid4().hex,
            user_id=test_user_2.id,
            title="Private Conversation",
        )
        db_session.add(conv)
        db_session.commit()

        response = client.get(
            f"/api/conversations/{conv.id}",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 404

    def test_cannot_view_other_users_quiz(self, client, test_user, test_user_2, test_user_token, db_session):
        """Test that a user cannot view another user's quiz."""
        import uuid
        from app.models import Quiz

        quiz = Quiz(
            id=uuid.uuid4().hex,
            subject="Mathematics",
            title="Private Quiz",
            created_by=test_user_2.id,
        )
        db_session.add(quiz)
        db_session.commit()

        response = client.get(
            f"/api/quizzes/{quiz.id}",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 404
