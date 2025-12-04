"""Document model for storing ingested content."""

import enum
import uuid
from datetime import datetime
from typing import List

from sqlalchemy import Boolean, Column, DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.inspection import inspect

from app.database import Base


class DocumentType(str, enum.Enum):
    """Document source type enumeration."""

    URL = "url"
    PDF = "pdf"
    YOUTUBE = "youtube"
    TEXT = "text"


class Document(Base):
    """Document model for storing source documents."""

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True)  # Optional for MVP
    type = Column(Enum(DocumentType), nullable=False)
    title = Column(String(500), nullable=False)
    author = Column(String(255), nullable=True)
    source_url = Column(Text, nullable=True)
    doc_metadata = Column(JSONB, nullable=False, default=dict)
    processed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    chunks = relationship(
        "Chunk", back_populates="document", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Document(id={self.id}, title='{self.title}', type={self.type})>"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        # Check if chunks relationship is loaded to avoid lazy loading in async context
        insp = inspect(self)
        chunks_loaded = 'chunks' not in insp.unloaded

        result = {
            "id": str(self.id),
            "user_id": str(self.user_id) if self.user_id else None,
            "type": self.type.value,
            "title": self.title,
            "author": self.author,
            "source_url": self.source_url,
            "metadata": self.doc_metadata,
            "processed": self.processed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        # Only include chunk_count if chunks are already loaded
        if chunks_loaded:
            result["chunk_count"] = len(self.chunks) if self.chunks else 0

        return result
