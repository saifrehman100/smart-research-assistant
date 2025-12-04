"""Query and chat schemas for API validation."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SourceReference(BaseModel):
    """Schema for source citation reference."""

    document_id: UUID
    title: str
    type: str
    author: Optional[str] = None
    url: Optional[str] = None
    chunk_content: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    page_number: Optional[int] = None
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    """Schema for chat request."""

    question: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[UUID] = None
    include_sources: bool = Field(default=True)

    class Config:
        json_schema_extra = {
            "example": {
                "question": "What are the main benefits of using RAG systems?",
                "conversation_id": None,
                "include_sources": True,
            }
        }


class ChatResponse(BaseModel):
    """Schema for chat response."""

    answer: str
    sources: List[SourceReference] = Field(default_factory=list)
    conversation_id: UUID
    message_id: UUID
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "RAG systems provide several key benefits...",
                "sources": [],
                "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
                "message_id": "123e4567-e89b-12d3-a456-426614174001",
                "created_at": "2024-01-01T00:00:00",
            }
        }


class SearchRequest(BaseModel):
    """Schema for semantic search request."""

    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=10, ge=1, le=50)
    filters: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "query": "machine learning embeddings",
                "top_k": 10,
                "filters": {"type": "url"},
            }
        }


class SearchResult(BaseModel):
    """Schema for search result."""

    chunk_id: UUID
    document_id: UUID
    document_title: str
    content: str
    relevance_score: float
    metadata: Dict[str, Any]


class SearchResponse(BaseModel):
    """Schema for search response."""

    results: List[SearchResult]
    query: str
    total_results: int

    class Config:
        json_schema_extra = {
            "example": {
                "results": [],
                "query": "machine learning embeddings",
                "total_results": 0,
            }
        }
