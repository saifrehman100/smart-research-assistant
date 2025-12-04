"""Document schemas for API validation."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, field_validator


class DocumentType(str, Enum):
    """Document type enumeration."""

    URL = "url"
    PDF = "pdf"
    YOUTUBE = "youtube"
    TEXT = "text"


class DocumentCreate(BaseModel):
    """Schema for creating a document."""

    type: DocumentType
    url: Optional[str] = None
    text: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: Optional[str], info) -> Optional[str]:
        """Validate URL based on document type."""
        doc_type = info.data.get("type")
        if doc_type in [DocumentType.URL, DocumentType.YOUTUBE] and not v:
            raise ValueError(f"URL is required for {doc_type} documents")
        return v

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: Optional[str], info) -> Optional[str]:
        """Validate text for TEXT type documents."""
        doc_type = info.data.get("type")
        if doc_type == DocumentType.TEXT and not v:
            raise ValueError("Text is required for TEXT documents")
        return v


class ChunkResponse(BaseModel):
    """Schema for chunk response."""

    id: UUID
    document_id: UUID
    content: str
    chunk_index: int
    metadata: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    """Schema for document response."""

    id: UUID
    user_id: Optional[UUID] = None
    type: str
    title: str
    author: Optional[str] = None
    source_url: Optional[str] = None
    metadata: Dict[str, Any]
    processed: bool
    created_at: datetime
    chunk_count: int = 0

    class Config:
        from_attributes = True


class DocumentDetail(DocumentResponse):
    """Schema for detailed document response with chunks."""

    chunks: List[ChunkResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True
