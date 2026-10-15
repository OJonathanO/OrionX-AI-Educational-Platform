"""Tests for document upload, extraction, chunking, and deletion."""
import io
import os
import uuid

import pytest
from fastapi.testclient import TestClient

from app.models import Document, ProcessingStatus, User, UserRole
from app.core.security import hash_password


class TestDocumentUpload:
    """Tests for document upload validation."""

    def test_upload_txt_success(self, client, test_user_token):
        """Test successful upload of a text file."""
        content = b"This is a test document with some educational content about mathematics."
        response = client.post(
            "/api/documents/upload",
            headers={"Authorization": f"Bearer {test_user_token}"},
            files={"file": ("test.txt", io.BytesIO(content), "text/plain")},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "test"
        assert data["file_type"] == "txt"
        assert data["processing_status"] == "pending"

    def test_upload_unsupported_file_type(self, client, test_user_token):
        """Test upload of an unsupported file type."""
        content = b"Some content"
        response = client.post(
            "/api/documents/upload",
            headers={"Authorization": f"Bearer {test_user_token}"},
            files={"file": ("test.exe", io.BytesIO(content), "application/octet-stream")},
        )
        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]

    def test_upload_empty_file(self, client, test_user_token):
        """Test upload of an empty file."""
        response = client.post(
            "/api/documents/upload",
            headers={"Authorization": f"Bearer {test_user_token}"},
            files={"file": ("empty.txt", io.BytesIO(b""), "text/plain")},
        )
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_upload_requires_auth(self, client):
        """Test that upload requires authentication."""
        content = b"Some content"
        response = client.post(
            "/api/documents/upload",
            files={"file": ("test.txt", io.BytesIO(content), "text/plain")},
        )
        assert response.status_code == 401

    def test_upload_with_subject_and_description(self, client, test_user_token):
        """Test upload with optional subject and description fields."""
        content = b"Physics content about Newton's laws of motion."
        response = client.post(
            "/api/documents/upload",
            headers={"Authorization": f"Bearer {test_user_token}"},
            files={"file": ("physics.txt", io.BytesIO(content), "text/plain")},
            data={"subject": "Physics", "description": "Newton's laws"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "physics"


class TestDocumentListing:
    """Tests for document listing and retrieval."""

    def test_list_documents_empty(self, client, test_user_token):
        """Test listing documents when user has none."""
        response = client.get(
            "/api/documents/",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_documents_with_items(self, client, test_user, test_user_token, db_session):
        """Test listing documents when user has uploaded some."""
        for i in range(3):
            doc = Document(
                id=uuid.uuid4().hex,
                owner_id=test_user.id,
                title=f"Document {i}",
                filename=f"doc_{i}.txt",
                file_type="txt",
                file_size=100,
                processing_status=ProcessingStatus.completed,
            )
            db_session.add(doc)
        db_session.commit()

        response = client.get(
            "/api/documents/",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    def test_list_documents_pagination(self, client, test_user, test_user_token, db_session):
        """Test document listing pagination."""
        for i in range(5):
            doc = Document(
                id=uuid.uuid4().hex,
                owner_id=test_user.id,
                title=f"Doc {i}",
                filename=f"doc_{i}.txt",
                file_type="txt",
                file_size=100,
                processing_status=ProcessingStatus.completed,
            )
            db_session.add(doc)
        db_session.commit()

        # Page 1
        response = client.get(
            "/api/documents/?page=1&page_size=2",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5

        # Page 2
        response = client.get(
            "/api/documents/?page=2&page_size=2",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        data = response.json()
        assert len(data["items"]) == 2

        # Page 3 (only 1 item left)
        response = client.get(
            "/api/documents/?page=3&page_size=2",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        data = response.json()
        assert len(data["items"]) == 1


class TestDocumentStatus:
    """Tests for document processing status."""

    def test_get_document_status(self, client, test_user, test_user_token, db_session):
        """Test getting processing status of a document."""
        doc = Document(
            id=uuid.uuid4().hex,
            owner_id=test_user.id,
            title="Test Doc",
            filename="test.txt",
            file_type="txt",
            file_size=100,
            processing_status=ProcessingStatus.completed,
            chunk_count=5,
        )
        db_session.add(doc)
        db_session.commit()

        response = client.get(
            f"/api/documents/{doc.id}/status",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["chunk_count"] == 5

    def test_get_status_nonexistent_document(self, client, test_user_token):
        """Test getting status of a document that doesn't exist."""
        response = client.get(
            f"/api/documents/{uuid.uuid4().hex}/status",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 404


class TestDocumentPreview:
    """Tests for document preview."""

    def test_get_preview(self, client, test_user, test_user_token, db_session):
        """Test getting a preview of extracted text."""
        doc = Document(
            id=uuid.uuid4().hex,
            owner_id=test_user.id,
            title="Preview Test",
            filename="preview.txt",
            file_type="txt",
            file_size=100,
            processing_status=ProcessingStatus.completed,
            extracted_text="This is the full extracted text from the document.",
        )
        db_session.add(doc)
        db_session.commit()

        response = client.get(
            f"/api/documents/{doc.id}/preview",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "preview" in data
        assert data["total_length"] > 0

    def test_get_preview_not_processed(self, client, test_user, test_user_token, db_session):
        """Test getting preview of a document that hasn't been processed."""
        doc = Document(
            id=uuid.uuid4().hex,
            owner_id=test_user.id,
            title="Pending Doc",
            filename="pending.txt",
            file_type="txt",
            file_size=100,
            processing_status=ProcessingStatus.pending,
        )
        db_session.add(doc)
        db_session.commit()

        response = client.get(
            f"/api/documents/{doc.id}/preview",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 400
        assert "not ready" in response.json()["detail"]


class TestDocumentDeletion:
    """Tests for document deletion."""

    def test_delete_document(self, client, test_user, test_user_token, db_session):
        """Test successful document deletion."""
        doc = Document(
            id=uuid.uuid4().hex,
            owner_id=test_user.id,
            title="Delete Me",
            filename="delete_me.txt",
            file_type="txt",
            file_size=100,
            processing_status=ProcessingStatus.completed,
        )
        db_session.add(doc)
        db_session.commit()

        doc_id = doc.id
        response = client.delete(
            f"/api/documents/{doc_id}",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 204

        # Verify it's gone
        deleted = db_session.query(Document).filter(Document.id == doc_id).first()
        assert deleted is None

    def test_delete_nonexistent_document(self, client, test_user_token):
        """Test deleting a document that doesn't exist."""
        response = client.delete(
            f"/api/documents/{uuid.uuid4().hex}",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 404

    def test_delete_requires_auth(self, client):
        """Test that deletion requires authentication."""
        response = client.delete(f"/api/documents/{uuid.uuid4().hex}")
        assert response.status_code == 401
