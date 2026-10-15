"""Quiz generation, submission, and results router."""
import json
import logging
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    User, Quiz, QuizQuestion, QuizAttempt, StudentAnswer,
    Document, ProcessingStatus,
)
from app.core.dependencies import get_current_active_user
from app.rag.retrieval import get_retrieval_service
from app.rag.generation import get_generation_service, AnswerStyle, GeneratedAnswer
from app.schemas.quizzes import (
    QuizGenerateRequest, QuizResponse, QuizDetailResponse,
    QuizSubmitRequest, QuizResultResponse, QuestionResponse,
    QuizAnswerResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/quizzes", tags=["quizzes"])

VALID_QUESTION_TYPES = {"multiple_choice", "true_false", "short_answer", "fill_blank"}


@router.get("/quiz-attempts")
def list_quiz_attempts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List the current user's quiz attempts with pagination."""
    query = db.query(QuizAttempt).filter(QuizAttempt.student_id == current_user.id)
    total = query.count()

    attempts = (
        query.order_by(QuizAttempt.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    results = []
    for attempt in attempts:
        quiz = db.query(Quiz).filter(Quiz.id == attempt.quiz_id).first()
        results.append({
            "id": attempt.id,
            "quiz_id": attempt.quiz_id,
            "quiz_title": quiz.title if quiz else "Unknown",
            "score": attempt.score,
            "max_score": attempt.max_score,
            "percentage": attempt.percentage,
            "completed": attempt.completed,
            "created_at": attempt.created_at,
            "completed_at": attempt.completed_at,
        })

    return {
        "items": results,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/generate", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
def generate_quiz(
    request: QuizGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Generate a quiz using LLM based on document content or subject.

    Retrieves relevant document chunks, asks the LLM to produce questions
    in JSON format, parses and validates the response, then saves to DB.
    """
    # Validate question types
    for qt in request.question_types:
        if qt not in VALID_QUESTION_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid question type '{qt}'. Valid: {', '.join(VALID_QUESTION_TYPES)}",
            )

    # Retrieve relevant chunks if document_id provided
    context_chunks = []
    if request.document_id:
        document = db.query(Document).filter(Document.id == request.document_id).first()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        if document.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        if document.processing_status != ProcessingStatus.completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document is not fully processed yet",
            )

        retrieval = get_retrieval_service()
        results = retrieval.retrieve(
            query=f"{request.subject} quiz questions",
            owner_id=current_user.id,
            document_ids=[request.document_id],
            top_k=10,
        )
        context_chunks = [
            {
                "text": r.text,
                "document_title": r.document_title,
                "page_number": r.page_number,
                "section_heading": r.section_heading,
            }
            for r in results
        ]

    # Build prompt for LLM
    context_text = "\n\n".join(
        f"[Source {i+1}] {c['document_title']}:\n{c['text']}"
        for i, c in enumerate(context_chunks)
    ) if context_chunks else f"Subject: {request.subject}"

    question_types_str = ", ".join(request.question_types)
    prompt = f"""Generate {request.num_questions} quiz questions for the subject "{request.subject}".
Difficulty: {request.difficulty}.
Question types allowed: {question_types_str}.

Return your response as a JSON array of objects with this exact structure:
[
  {{
    "question_type": "multiple_choice",
    "question_text": "What is...?",
    "options": ["A", "B", "C", "D"],
    "correct_answer": "A",
    "explanation": "Because..."
  }},
  {{
    "question_type": "true_false",
    "question_text": "The sky is blue.",
    "options": ["True", "False"],
    "correct_answer": "True",
    "explanation": "..."
  }},
  {{
    "question_type": "short_answer",
    "question_text": "Explain...",
    "options": [],
    "correct_answer": "Expected answer",
    "explanation": "..."
  }}
]

For multiple_choice: provide 4 options, correct_answer is the letter (A, B, C, or D).
For true_false: options are ["True", "False"].
For short_answer and fill_blank: options is empty array, correct_answer is the expected text.

Context from documents:
{context_text}

Return ONLY the JSON array, no other text."""

    # Generate quiz questions via LLM
    generation = get_generation_service()
    try:
        result = generation.generate_answer(
            question=prompt,
            context_chunks=context_chunks or [{"text": f"Generate questions about {request.subject}", "document_title": ""}],
            style=AnswerStyle.DETAILED,
        )
    except Exception as e:
        logger.error(f"Quiz generation LLM call failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM service unavailable. Please try again later.",
        )

    # Parse JSON response
    questions_data = _parse_quiz_questions(result.text)

    if not questions_data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate valid quiz questions. Please try again.",
        )

    # Create quiz record
    quiz_id = uuid.uuid4().hex
    quiz = Quiz(
        id=quiz_id,
        document_id=request.document_id,
        subject=request.subject,
        title=f"{request.subject} Quiz ({request.difficulty})",
        difficulty=request.difficulty,
        question_types=json.dumps(request.question_types),
        created_by=current_user.id,
    )
    db.add(quiz)
    db.flush()

    # Create question records
    for i, q_data in enumerate(questions_data):
        question = QuizQuestion(
            id=uuid.uuid4().hex,
            quiz_id=quiz_id,
            question_type=q_data["question_type"],
            question_text=q_data["question_text"],
            options=json.dumps(q_data.get("options", [])),
            correct_answer=q_data["correct_answer"],
            explanation=q_data.get("explanation", ""),
            source_chunk_id=None,
            source_excerpt="",
            difficulty=request.difficulty,
            order_index=i,
        )
        db.add(question)

    db.commit()

    return QuizResponse(
        id=quiz_id,
        title=quiz.title,
        subject=quiz.subject,
        difficulty=quiz.difficulty,
        question_count=len(questions_data),
        created_at=quiz.created_at,
    )


def _parse_quiz_questions(text: str) -> List[dict]:
    """Parse LLM JSON response into validated question dicts."""
    # Try to extract JSON array from the response
    json_text = text.strip()

    # Remove markdown code fences if present
    if json_text.startswith("```"):
        lines = json_text.split("\n")
        json_text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    # Try to find the JSON array
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError:
        # Try to extract the array portion
        start = json_text.find("[")
        end = json_text.rfind("]")
        if start != -1 and end != -1:
            try:
                data = json_text[start : end + 1]
                data = json.loads(data)
            except json.JSONDecodeError:
                return []
        else:
            return []

    if not isinstance(data, list):
        return []

    questions = []
    for item in data:
        if not isinstance(item, dict):
            continue
        q_type = item.get("question_type", "")
        if q_type not in VALID_QUESTION_TYPES:
            continue
        if not item.get("question_text") or not item.get("correct_answer"):
            continue
        if q_type in ("multiple_choice", "true_false") and not item.get("options"):
            continue

        questions.append({
            "question_type": q_type,
            "question_text": item["question_text"],
            "options": item.get("options", []),
            "correct_answer": item["correct_answer"],
            "explanation": item.get("explanation", ""),
        })

    return questions


@router.get("/")
def list_quizzes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List the current user's quizzes."""
    query = db.query(Quiz).filter(Quiz.created_by == current_user.id)
    total = query.count()

    quizzes = (
        query.order_by(Quiz.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    results = []
    for quiz in quizzes:
        question_count = (
            db.query(QuizQuestion)
            .filter(QuizQuestion.quiz_id == quiz.id)
            .count()
        )
        results.append(
            QuizResponse(
                id=quiz.id,
                title=quiz.title,
                subject=quiz.subject,
                difficulty=quiz.difficulty,
                question_count=question_count,
                created_at=quiz.created_at,
            )
        )

    return {
        "items": results,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{quiz_id}", response_model=QuizDetailResponse)
def get_quiz(
    quiz_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get quiz with all questions. Owner or public access only."""
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")

    # Check ownership
    if quiz.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")

    questions = (
        db.query(QuizQuestion)
        .filter(QuizQuestion.quiz_id == quiz_id)
        .order_by(QuizQuestion.order_index.asc())
        .all()
    )

    return QuizDetailResponse(
        id=quiz.id,
        title=quiz.title,
        subject=quiz.subject,
        difficulty=quiz.difficulty,
        question_count=len(questions),
        created_at=quiz.created_at,
        questions=[
            QuestionResponse(
                id=q.id,
                question_type=q.question_type,
                question_text=q.question_text,
                options=json.loads(q.options or "[]"),
                order_index=q.order_index,
            )
            for q in questions
        ],
    )


@router.post("/{quiz_id}/submit", response_model=QuizResultResponse)
def submit_quiz(
    quiz_id: str,
    submission: QuizSubmitRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Submit quiz answers and get graded results.

    Objective questions (multiple_choice, true_false, fill_blank) are graded
    deterministically. Short-answer questions are graded by the LLM.
    """
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
    if quiz.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")

    questions = (
        db.query(QuizQuestion)
        .filter(QuizQuestion.quiz_id == quiz_id)
        .all()
    )
    question_map = {q.id: q for q in questions}

    # Grade answers
    answer_results = []
    total_score = 0.0
    max_score = len(questions)

    generation = get_generation_service()

    for ans in submission.answers:
        question = question_map.get(ans.question_id)
        if not question:
            continue

        is_correct = False
        ai_feedback = ""

        if question.question_type in ("multiple_choice", "true_false", "fill_blank"):
            # Deterministic grading
            is_correct = ans.answer_text.strip().lower() == question.correct_answer.strip().lower()
        elif question.question_type == "short_answer":
            # LLM-based grading
            is_correct, ai_feedback = _grade_short_answer(
                generation, question, ans.answer_text
            )

        if is_correct:
            total_score += 1.0

        answer_results.append(
            QuizAnswerResult(
                question_id=question.id,
                answer_text=ans.answer_text,
                is_correct=is_correct,
                correct_answer=question.correct_answer,
                explanation=question.explanation + ("\n\nAI Feedback: " + ai_feedback if ai_feedback else ""),
            )
        )

    # Create attempt record
    attempt_id = uuid.uuid4().hex
    percentage = (total_score / max_score * 100) if max_score > 0 else 0.0
    attempt = QuizAttempt(
        id=attempt_id,
        quiz_id=quiz_id,
        student_id=current_user.id,
        score=total_score,
        max_score=float(max_score),
        percentage=percentage,
        completed=True,
    )
    db.add(attempt)
    db.flush()

    # Save student answers
    for ans in submission.answers:
        question = question_map.get(ans.question_id)
        if not question:
            continue

        is_correct = ans.answer_text.strip().lower() == question.correct_answer.strip().lower()
        if question.question_type == "short_answer":
            # Find the graded result
            for ar in answer_results:
                if ar.question_id == question.id:
                    is_correct = ar.is_correct
                    break

        student_answer = StudentAnswer(
            id=uuid.uuid4().hex,
            attempt_id=attempt_id,
            question_id=question.id,
            answer_text=ans.answer_text,
            is_correct=is_correct,
        )
        db.add(student_answer)

    db.commit()

    return QuizResultResponse(
        score=total_score,
        max_score=float(max_score),
        percentage=percentage,
        answers=answer_results,
    )


def _grade_short_answer(
    generation, question: QuizQuestion, student_answer: str
) -> tuple:
    """Grade a short-answer question using the LLM. Returns (is_correct, feedback)."""
    prompt = f"""Grade the following student answer for a short-answer question.

Question: {question.question_text}
Correct answer: {question.correct_answer}
Student answer: {student_answer}

Determine if the student's answer is correct (conveyed the same meaning as the correct answer).
Return ONLY a JSON object with this structure:
{{"is_correct": true/false, "feedback": "brief explanation"}}

Return ONLY the JSON object, no other text."""

    try:
        result = generation.generate_answer(
            question=prompt,
            context_chunks=[{"text": prompt, "document_title": ""}],
            style=AnswerStyle.CONCISE,
        )
        # Parse the JSON response
        text = result.text.strip()
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            data = json.loads(text[start : end + 1])
            return data.get("is_correct", False), data.get("feedback", "")
    except Exception as e:
        logger.error(f"Short-answer grading failed: {e}")

    # Fallback: simple keyword matching
    correct_keywords = set(question.correct_answer.lower().split())
    answer_keywords = set(student_answer.lower().split())
    overlap = len(correct_keywords & answer_keywords)
    is_correct = overlap >= len(correct_keywords) * 0.5
    return is_correct, ""


@router.get("/{quiz_id}/results")
def get_quiz_results(
    quiz_id: str,
    attempt_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get results for a specific quiz attempt or the latest attempt."""
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
    if quiz.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")

    if attempt_id:
        attempt = (
            db.query(QuizAttempt)
            .filter(
                QuizAttempt.id == attempt_id,
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.student_id == current_user.id,
            )
            .first()
        )
    else:
        attempt = (
            db.query(QuizAttempt)
            .filter(
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.student_id == current_user.id,
            )
            .order_by(QuizAttempt.created_at.desc())
            .first()
        )

    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No quiz attempt found",
        )

    # Get answers with question details
    answers = (
        db.query(StudentAnswer)
        .filter(StudentAnswer.attempt_id == attempt.id)
        .all()
    )

    answer_details = []
    for ans in answers:
        question = db.query(QuizQuestion).filter(QuizQuestion.id == ans.question_id).first()
        if question:
            answer_details.append(
                QuizAnswerResult(
                    question_id=question.id,
                    answer_text=ans.answer_text,
                    is_correct=ans.is_correct,
                    correct_answer=question.correct_answer,
                    explanation=question.explanation,
                )
            )

    return {
        "attempt_id": attempt.id,
        "quiz_id": quiz.id,
        "quiz_title": quiz.title,
        "score": attempt.score,
        "max_score": attempt.max_score,
        "percentage": attempt.percentage,
        "completed": attempt.completed,
        "created_at": attempt.created_at,
        "completed_at": attempt.completed_at,
        "answers": answer_details,
    }
