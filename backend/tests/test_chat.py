"""Tests for chat functionality with mock LLM, conversation history, and citations."""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.models import (
    User, UserRole, Conversation, ChatMessage, SourceReference,
    Document, ProcessingStatus,
)
from app.core.security import hash_password


class TestChatBasic:
    """Tests for basic chat functionality."""

    def test_chat_creates_conversation(self, client, test_user, test_user_token, db_session):
        """Test that sending a chat message creates a new conversation."""
        response = client.post(
            "/api/chat/",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={"message": "What is calculus?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "message_id" in data
        assert "conversation_id" in data
        assert "content" in data
        assert len(data["content"]) > 0

    def test_chat_saves_messages(self, client, test_user, test_user_token, db_session):
        """Test that chat messages are saved to the database."""
        response = client.post(
            "/api/chat/",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={"message": "Explain photosynthesis"},
        )
        assert response.status_code == 200
        data = response.json()
        conversation_id = data["conversation_id"]

        # Check messages were saved
        messages = (
            db_session.query(ChatMessage)
            .filter(ChatMessage.conversation_id == conversation_id)
            .all()
        )
        assert len(messages) == 2  # user message + assistant response

        roles = [m.role for m in messages]
        assert "user" in roles
        assert "assistant" in roles

    def test_chat_with_existing_conversation(self, client, test_user, test_user_token, db_session):
        """Test sending a message to an existing conversation."""
        # Create a conversation first
        conv = Conversation(
            id=uuid.uuid4().hex,
            user_id=test_user.id,
            title="Test Conversation",
        )
        db_session.add(conv)
        db_session.commit()

        response = client.post(
            "/api/chat/",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={
                "message": "Follow up question",
                "conversation_id": conv.id,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == conv.id

    def test_chat_invalid_conversation_id(self, client, test_user_token):
        """Test sending a message to a non-existent conversation."""
        response = client.post(
            "/api/chat/",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={
                "message": "Hello",
                "conversation_id": uuid.uuid4().hex,
            },
        )
        assert response.status_code == 404

    def test_chat_requires_auth(self, client):
        """Test that chat requires authentication."""
        response = client.post(
            "/api/chat/",
            json={"message": "Hello"},
        )
        assert response.status_code == 401

    def test_chat_empty_message(self, client, test_user_token):
        """Test that empty messages are rejected."""
        response = client.post(
            "/api/chat/",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={"message": ""},
        )
        assert response.status_code == 422


class TestChatResponse:
    """Tests for chat response structure and content."""

    def test_chat_response_has_sources(self, client, test_user, test_user_token, db_session):
        """Test that chat response includes source references."""
        # Create a document with chunks for retrieval
        doc = Document(
            id=uuid.uuid4().hex,
            owner_id=test_user.id,
            title="Math Textbook",
            filename="math.pdf",
            file_type="pdf",
            file_size=5000,
            processing_status=ProcessingStatus.completed,
            extracted_text="Calculus is a branch of mathematics.",
        )
        db_session.add(doc)
        db_session.commit()

        response = client.post(
            "/api/chat/",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={"message": "What is calculus?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "sources" in data
        assert isinstance(data["sources"], list)

    def test_chat_response_has_timestamps(self, client, test_user_token):
        """Test that chat response includes creation timestamp."""
        response = client.post(
            "/api/chat/",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={"message": "Hello"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "created_at" in data

    def test_chat_with_answer_style(self, client, test_user_token):
        """Test chat with different answer styles."""
        for style in ["detailed", "concise", "simple"]:
            response = client.post(
                "/api/chat/",
                headers={"Authorization": f"Bearer {test_user_token}"},
                json={
                    "message": "Explain gravity",
                    "answer_style": style,
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data["content"]) > 0


class TestChatFeedback:
    """Tests for chat feedback submission."""

    def test_submit_feedback(self, client, test_user, test_user_token, db_session):
        """Test submitting feedback on a chat message."""
        # First create a chat message
        response = client.post(
            "/api/chat/",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={"message": "What is 2+2?"},
        )
        assert response.status_code == 200
        message_id = response.json()["message_id"]

        # Submit feedback
        feedback_response = client.post(
            "/api/chat/feedback",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={
                "message_id": message_id,
                "is_helpful": True,
                "comment": "Great answer!",
            },
        )
        assert feedback_response.status_code == 201
        assert feedback_response.json()["status"] == "recorded"

    def test_feedback_on_nonexistent_message(self, client, test_user_token):
        """Test submitting feedback on a message that doesn't exist."""
        response = client.post(
            "/api/chat/feedback",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={
                "message_id": uuid.uuid4().hex,
                "is_helpful": False,
            },
        )
        assert response.status_code == 404


class TestConversationHistory:
    """Tests for conversation history retrieval."""

    def test_get_conversation_with_messages(self, client, test_user, test_user_token, db_session):
        """Test retrieving a conversation with all its messages."""
        # Create a conversation with messages
        conv = Conversation(
            id=uuid.uuid4().hex,
            user_id=test_user.id,
            title="History Test",
        )
        db_session.add(conv)
        db_session.flush()

        msg1 = ChatMessage(
            id=uuid.uuid4().hex,
            conversation_id=conv.id,
            role="user",
            content="First question",
        )
        msg2 = ChatMessage(
            id=uuid.uuid4().hex,
            conversation_id=conv.id,
            role="assistant",
            content="First answer",
        )
        db_session.add_all([msg1, msg2])
        db_session.commit()

        response = client.get(
            f"/api/conversations/{conv.id}",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][1]["role"] == "assistant"

    def test_list_conversations(self, client, test_user, test_user_token, db_session):
        """Test listing all conversations for a user."""
        for i in range(3):
            conv = Conversation(
                id=uuid.uuid4().hex,
                user_id=test_user.id,
                title=f"Conversation {i}",
            )
            db_session.add(conv)
        db_session.commit()

        response = client.get(
            "/api/conversations/",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    def test_rename_conversation(self, client, test_user, test_user_token, db_session):
        """Test renaming a conversation."""
        conv = Conversation(
            id=uuid.uuid4().hex,
            user_id=test_user.id,
            title="Old Title",
        )
        db_session.add(conv)
        db_session.commit()

        response = client.patch(
            f"/api/conversations/{conv.id}",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={"title": "New Title"},
        )
        assert response.status_code == 200
        assert response.json()["title"] == "New Title"

    def test_delete_conversation(self, client, test_user, test_user_token, db_session):
        """Test deleting a conversation."""
        conv = Conversation(
            id=uuid.uuid4().hex,
            user_id=test_user.id,
            title="Delete Me",
        )
        db_session.add(conv)
        db_session.commit()

        conv_id = conv.id
        response = client.delete(
            f"/api/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 204

        # Verify deletion
        deleted = db_session.query(Conversation).filter(Conversation.id == conv_id).first()
        assert deleted is None
