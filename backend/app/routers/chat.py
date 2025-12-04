"""Chat and Q&A router."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.query import ChatRequest, ChatResponse
from app.services.rag_service import get_rag_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("/ask", response_model=ChatResponse)
async def ask_question(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Ask a question and get an answer with citations.

    - **question**: The question to ask
    - **conversation_id**: Optional conversation ID to continue a conversation
    - **include_sources**: Whether to include source citations (default: true)

    Returns an answer with relevant source citations.
    """
    try:
        rag_service = get_rag_service()

        result = await rag_service.answer_question(
            question=request.question,
            conversation_id=request.conversation_id,
            db=db,
        )

        return ChatResponse(**result)

    except Exception as e:
        logger.error(f"Error answering question: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to answer question: {str(e)}",
        )


@router.post("/stream")
async def ask_question_stream(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Ask a question and get a streaming answer.

    - **question**: The question to ask
    - **conversation_id**: Optional conversation ID to continue a conversation

    Returns a Server-Sent Events (SSE) stream of the answer.
    """
    try:
        rag_service = get_rag_service()

        async def generate():
            """Generate SSE stream."""
            try:
                async for chunk in rag_service.answer_question_stream(
                    question=request.question,
                    conversation_id=request.conversation_id,
                    db=db,
                ):
                    # Format as SSE
                    yield f"data: {chunk}\n\n"

                # Send end signal
                yield "data: [DONE]\n\n"

            except Exception as e:
                logger.error(f"Error in streaming: {e}")
                yield f"data: [ERROR: {str(e)}]\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
        )

    except Exception as e:
        logger.error(f"Error setting up stream: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start streaming: {str(e)}",
        )
