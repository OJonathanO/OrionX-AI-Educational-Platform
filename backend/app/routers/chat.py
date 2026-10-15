"""Chat router for conversations with RAG-powered answers."""
import json
import logging
import uuid
from typing import AsyncGenerator, List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    User, Conversation, ChatMessage, SourceReference, Document,
    ProcessingStatus, Feedback,
)
from app.core.dependencies import get_current_active_user
from app.rag.retrieval import get_retrieval_service
from app.rag.generation import get_generation_service, AnswerStyle
from app.schemas.chat import (
    ChatRequest, ChatResponse, SourceResponse, FeedbackRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# Map user-facing style strings to AnswerStyle enum
STYLE_MAP = {
    "detailed": AnswerStyle.DETAILED,
    "concise": AnswerStyle.CONCISE,
    "simple": AnswerStyle.BEGINNER,
    "beginner": AnswerStyle.BEGINNER,
    "exam_prep": AnswerStyle.EXAM_PREP,
    "step_by_step": AnswerStyle.STEP_BY_STEP,
}


async def _generate_sse_stream(
    question: str,
    context_chunks: List[dict],
    style: AnswerStyle,
) -> AsyncGenerator[str, None]:
    """Generate SSE stream by chunking the LLM response."""
    generation = get_generation_service()
    result = generation.generate_answer(question, context_chunks, style)

    # Stream the answer in chunks
    words = result.text.split()
    chunk_size = 5  # words per SSE event
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i : i + chunk_size])
        data = json.dumps({"content": chunk, "done": False})
        yield f"data: {data}\n\n"

    # Send sources as final event
    sources_data = json.dumps({"sources": result.citations, "done": True})
    yield f"data: {sources_data}\n\n"
    yield "data: [DONE]\n\n"


@router.post("/", response_model=ChatResponse)
def send_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Send a chat message and receive a RAG-generated answer.

    Retrieves relevant document chunks, generates an answer using the LLM,
    saves the conversation and message, and returns the response with sources.
    """
    # Get or create conversation
    conversation_id = request.conversation_id
    if conversation_id:
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == conversation_id,
                Conversation.user_id == current_user.id,
            )
            .first()
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
    else:
        conversation = Conversation(
            id=uuid.uuid4().hex,
            user_id=current_user.id,
            title=request.message[:50],
        )
        db.add(conversation)
        db.flush()
        conversation_id = conversation.id

    # Save user message
    user_message = ChatMessage(
        id=uuid.uuid4().hex,
        conversation_id=conversation_id,
        role="user",
        content=request.message,
        answer_style=request.answer_style,
    )
    db.add(user_message)

    # Retrieve relevant chunks
    retrieval = get_retrieval_service()
    context_chunks = []
    try:
        results = retrieval.retrieve(
            query=request.message,
            owner_id=current_user.id,
            document_ids=request.document_ids,
        )
        context_chunks = [
            {
                "text": r.text,
                "document_title": r.document_title,
                "page_number": r.page_number,
                "section_heading": r.section_heading,
                "score": r.score,
                "chunk_id": r.chunk_id,
            }
            for r in results
        ]
    except Exception as e:
        logger.error(f"Retrieval failed: {e}")

    # Generate answer
    style = STYLE_MAP.get(request.answer_style, AnswerStyle.DETAILED)
    generation = get_generation_service()

    try:
        answer = generation.generate_answer(request.message, context_chunks, style)
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM service unavailable. Please try again later.",
        )

    # Save assistant message
    assistant_message = ChatMessage(
        id=uuid.uuid4().hex,
        conversation_id=conversation_id,
        role="assistant",
        content=answer.text,
        answer_style=request.answer_style,
    )
    db.add(assistant_message)
    db.flush()

    # Save source references
    for i, chunk in enumerate(context_chunks[:5], 1):
        source = SourceReference(
            id=uuid.uuid4().hex,
            message_id=assistant_message.id,
            document_id=chunk.get("document_id", ""),
            document_title=chunk.get("document_title", "Unknown"),
            chunk_id=chunk.get("chunk_id", ""),
            page_number=chunk.get("page_number"),
            section_heading=chunk.get("section_heading", ""),
            excerpt=chunk["text"][:500],
            relevance_score=chunk.get("score", 0.0),
        )
        db.add(source)

    db.commit()

    # Build response
    sources = [
        SourceResponse(
            document_title=chunk.get("document_title", "Unknown"),
            page_number=chunk.get("page_number"),
            section_heading=chunk.get("section_heading", ""),
            excerpt=chunk["text"][:200],
            relevance_score=chunk.get("score", 0.0),
        )
        for chunk in context_chunks[:5]
    ]

    return ChatResponse(
        message_id=assistant_message.id,
        conversation_id=conversation_id,
        content=answer.text,
        sources=sources,
        created_at=assistant_message.created_at,
    )


@router.post("/stream")
async def stream_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Send a chat message and receive a streaming SSE response.

    Same logic as POST /chat but returns a Server-Sent Events stream.
    """
    # Get or create conversation
    conversation_id = request.conversation_id
    if conversation_id:
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == conversation_id,
                Conversation.user_id == current_user.id,
            )
            .first()
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
    else:
        conversation = Conversation(
            id=uuid.uuid4().hex,
            user_id=current_user.id,
            title=request.message[:50],
        )
        db.add(conversation)
        db.flush()
        conversation_id = conversation.id

    # Save user message
    user_message = ChatMessage(
        id=uuid.uuid4().hex,
        conversation_id=conversation_id,
        role="user",
        content=request.message,
        answer_style=request.answer_style,
    )
    db.add(user_message)

    # Retrieve relevant chunks
    retrieval = get_retrieval_service()
    context_chunks = []
    try:
        results = retrieval.retrieve(
            query=request.message,
            owner_id=current_user.id,
            document_ids=request.document_ids,
        )
        context_chunks = [
            {
                "text": r.text,
                "document_title": r.document_title,
                "page_number": r.page_number,
                "section_heading": r.section_heading,
                "score": r.score,
                "chunk_id": r.chunk_id,
            }
            for r in results
        ]
    except Exception as e:
        logger.error(f"Retrieval failed: {e}")

    # Generate the full answer (we need to save it to DB)
    style = STYLE_MAP.get(request.answer_style, AnswerStyle.DETAILED)
    generation = get_generation_service()

    try:
        answer = generation.generate_answer(request.message, context_chunks, style)
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM service unavailable. Please try again later.",
        )

    # Save assistant message
    assistant_message = ChatMessage(
        id=uuid.uuid4().hex,
        conversation_id=conversation_id,
        role="assistant",
        content=answer.text,
        answer_style=request.answer_style,
    )
    db.add(assistant_message)
    db.flush()

    # Save source references
    for chunk in context_chunks[:5]:
        source = SourceReference(
            id=uuid.uuid4().hex,
            message_id=assistant_message.id,
            document_id=chunk.get("document_id", ""),
            document_title=chunk.get("document_title", "Unknown"),
            chunk_id=chunk.get("chunk_id", ""),
            page_number=chunk.get("page_number"),
            section_heading=chunk.get("section_heading", ""),
            excerpt=chunk["text"][:500],
            relevance_score=chunk.get("score", 0.0),
        )
        db.add(source)

    db.commit()

    # Return SSE stream
    return StreamingResponse(
        _generate_sse_stream(request.message, context_chunks, style),
        media_type="text/event-stream",
    )


@router.post("/feedback", status_code=status.HTTP_201_CREATED)
def submit_feedback(
    feedback: FeedbackRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Submit feedback on a chat message."""
    # Verify the message exists and belongs to the user
    message = (
        db.query(ChatMessage)
        .join(Conversation, ChatMessage.conversation_id == Conversation.id)
        .filter(
            ChatMessage.id == feedback.message_id,
            Conversation.user_id == current_user.id,
        )
        .first()
    )
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )

    feedback_record = Feedback(
        id=uuid.uuid4().hex,
        user_id=current_user.id,
        message_id=feedback.message_id,
        is_helpful=feedback.is_helpful,
        comment=feedback.comment or "",
    )
    db.add(feedback_record)
    db.commit()

    return {"status": "recorded"}
