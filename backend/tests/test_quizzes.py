"""Tests for quiz generation, validation, and scoring."""
import json
import uuid

import pytest
from fastapi.testclient import TestClient

from app.models import (
    User, UserRole, Quiz, QuizQuestion, QuizAttempt, StudentAnswer,
    Document, ProcessingStatus,
)
from app.core.security import hash_password


class TestQuizGeneration:
    """Tests for quiz generation endpoint."""

    def test_generate_quiz_without_document(self, client, test_user_token):
        """Test generating a quiz without a document (subject-only)."""
        response = client.post(
            "/api/quizzes/generate",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={
                "subject": "Mathematics",
                "num_questions": 3,
                "difficulty": "medium",
                "question_types": ["multiple_choice"],
            },
        )
        # Should succeed with mock LLM
        assert response.status_code == 201
        data = response.json()
        assert data["subject"] == "Mathematics"
        assert data["question_count"] > 0

    def test_generate_quiz_with_document(self, client, test_user, test_user_token, db_session):
        """Test generating a quiz based on a document."""
        doc = Document(
            id=uuid.uuid4().hex,
            owner_id=test_user.id,
            title="Biology Textbook",
            filename="biology.pdf",
            file_type="pdf",
            file_size=5000,
            processing_status=ProcessingStatus.completed,
        )
        db_session.add(doc)
        db_session.commit()

        response = client.post(
            "/api/quizzes/generate",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={
                "document_id": doc.id,
                "subject": "Biology",
                "num_questions": 2,
                "difficulty": "easy",
                "question_types": ["true_false"],
            },
        )
        assert response.status_code == 201

    def test_generate_quiz_invalid_question_type(self, client, test_user_token):
        """Test that invalid question types are rejected."""
        response = client.post(
            "/api/quizzes/generate",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={
                "subject": "History",
                "num_questions": 3,
                "question_types": ["invalid_type"],
            },
        )
        assert response.status_code == 400
        assert "Invalid question type" in response.json()["detail"]

    def test_generate_quiz_unprocessed_document(self, client, test_user, test_user_token, db_session):
        """Test that quizzes can't be generated from unprocessed documents."""
        doc = Document(
            id=uuid.uuid4().hex,
            owner_id=test_user.id,
            title="Pending Doc",
            filename="pending.pdf",
            file_type="pdf",
            file_size=5000,
            processing_status=ProcessingStatus.pending,
        )
        db_session.add(doc)
        db_session.commit()

        response = client.post(
            "/api/quizzes/generate",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={
                "document_id": doc.id,
                "subject": "Math",
                "num_questions": 3,
            },
        )
        assert response.status_code == 400
        assert "not fully processed" in response.json()["detail"]

    def test_generate_quiz_requires_auth(self, client):
        """Test that quiz generation requires authentication."""
        response = client.post(
            "/api/quizzes/generate",
            json={
                "subject": "Math",
                "num_questions": 3,
            },
        )
        assert response.status_code == 401


class TestQuizListing:
    """Tests for quiz listing and detail."""

    def test_list_quizzes(self, client, test_user, test_user_token, db_session):
        """Test listing quizzes for the current user."""
        for i in range(3):
            quiz = Quiz(
                id=uuid.uuid4().hex,
                subject=f"Subject {i}",
                title=f"Quiz {i}",
                created_by=test_user.id,
            )
            db_session.add(quiz)
        db_session.commit()

        response = client.get(
            "/api/quizzes/",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3

    def test_get_quiz_detail(self, client, test_user, test_user_token, db_session):
        """Test getting quiz with all questions."""
        quiz = Quiz(
            id=uuid.uuid4().hex,
            subject="Physics",
            title="Physics Quiz",
            created_by=test_user.id,
        )
        db_session.add(quiz)
        db_session.flush()

        for i in range(3):
            q = QuizQuestion(
                id=uuid.uuid4().hex,
                quiz_id=quiz.id,
                question_type="multiple_choice",
                question_text=f"Question {i}?",
                options=json.dumps(["A", "B", "C", "D"]),
                correct_answer="A",
                order_index=i,
            )
            db_session.add(q)
        db_session.commit()

        response = client.get(
            f"/api/quizzes/{quiz.id}",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["question_count"] == 3
        assert len(data["questions"]) == 3


class TestQuizSubmission:
    """Tests for quiz submission and scoring."""

    def _create_quiz_with_questions(self, db_session, user_id, question_type="multiple_choice"):
        """Helper to create a quiz with questions."""
        quiz = Quiz(
            id=uuid.uuid4().hex,
            subject="Math",
            title="Test Quiz",
            created_by=user_id,
        )
        db_session.add(quiz)
        db_session.flush()

        questions = []
        for i in range(3):
            q = QuizQuestion(
                id=uuid.uuid4().hex,
                quiz_id=quiz.id,
                question_type=question_type,
                question_text=f"Question {i}?",
                options=json.dumps(["A", "B", "C", "D"]) if question_type == "multiple_choice" else "[]",
                correct_answer="A" if question_type == "multiple_choice" else "answer",
                order_index=i,
            )
            db_session.add(q)
            questions.append(q)
        db_session.commit()
        return quiz, questions

    def test_submit_quiz_correct_answers(self, client, test_user, test_user_token, db_session):
        """Test submitting a quiz with all correct answers."""
        quiz, questions = self._create_quiz_with_questions(db_session, test_user.id)

        answers = [
            {"question_id": q.id, "answer_text": "A"}
            for q in questions
        ]

        response = client.post(
            f"/api/quizzes/{quiz.id}/submit",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={"answers": answers},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 3.0
        assert data["max_score"] == 3.0
        assert data["percentage"] == 100.0

    def test_submit_quiz_wrong_answers(self, client, test_user, test_user_token, db_session):
        """Test submitting a quiz with wrong answers."""
        quiz, questions = self._create_quiz_with_questions(db_session, test_user.id)

        answers = [
            {"question_id": q.id, "answer_text": "B"}  # All wrong
            for q in questions
        ]

        response = client.post(
            f"/api/quizzes/{quiz.id}/submit",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={"answers": answers},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 0.0
        assert data["percentage"] == 0.0

    def test_submit_quiz_partial_score(self, client, test_user, test_user_token, db_session):
        """Test submitting a quiz with some correct and some wrong answers."""
        quiz, questions = self._create_quiz_with_questions(db_session, test_user.id)

        answers = [
            {"question_id": questions[0].id, "answer_text": "A"},   # Correct
            {"question_id": questions[1].id, "answer_text": "B"},   # Wrong
            {"question_id": questions[2].id, "answer_text": "A"},   # Correct
        ]

        response = client.post(
            f"/api/quizzes/{quiz.id}/submit",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={"answers": answers},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 2.0
        assert data["max_score"] == 3.0
        assert 66.0 < data["percentage"] < 67.0

    def test_submit_quiz_case_insensitive(self, client, test_user, test_user_token, db_session):
        """Test that answer grading is case-insensitive."""
        quiz, questions = self._create_quiz_with_questions(db_session, test_user.id)

        answers = [
            {"question_id": q.id, "answer_text": "a"}  # lowercase
            for q in questions
        ]

        response = client.post(
            f"/api/quizzes/{quiz.id}/submit",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={"answers": answers},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 3.0

    def test_get_quiz_results(self, client, test_user, test_user_token, db_session):
        """Test retrieving quiz results after submission."""
        quiz, questions = self._create_quiz_with_questions(db_session, test_user.id)

        answers = [{"question_id": q.id, "answer_text": "A"} for q in questions]
        submit_response = client.post(
            f"/api/quizzes/{quiz.id}/submit",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={"answers": answers},
        )
        assert submit_response.status_code == 200

        # Get results
        response = client.get(
            f"/api/quizzes/{quiz.id}/results",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 3.0
        assert data["completed"] is True
        assert len(data["answers"]) == 3

    def test_submit_quiz_requires_auth(self, client):
        """Test that quiz submission requires authentication."""
        response = client.post(
            f"/api/quizzes/{uuid.uuid4().hex}/submit",
            json={"answers": []},
        )
        assert response.status_code == 401
