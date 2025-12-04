"""Health check router."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app import __version__
from app.database import get_db
from app.schemas.response import HealthResponse
from app.services.gemini_client import get_gemini_client
from app.services.vector_store import get_vector_store

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint.

    Returns system status and component health.
    """
    health_status = {
        "status": "healthy",
        "version": __version__,
        "database": "unknown",
        "vector_store": "unknown",
        "gemini_api": "unknown",
    }

    # Check database
    try:
        await db.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["database"] = "disconnected"
        health_status["status"] = "unhealthy"

    # Check vector store
    try:
        vector_store = get_vector_store()
        vector_store.get_collection_stats()
        health_status["vector_store"] = "connected"
    except Exception as e:
        logger.error(f"Vector store health check failed: {e}")
        health_status["vector_store"] = "disconnected"
        health_status["status"] = "degraded"

    # Check Gemini API (basic check - just initialize client)
    try:
        gemini_client = get_gemini_client()
        if gemini_client:
            health_status["gemini_api"] = "configured"
    except Exception as e:
        logger.error(f"Gemini API health check failed: {e}")
        health_status["gemini_api"] = "error"
        health_status["status"] = "degraded"

    return HealthResponse(**health_status)
