"""Conversation schemas for API validation."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    """Schema for message response."""

    id: UUID
    role: str
    content: str
    sources: List[dict] = Field(default_factory=list)
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    """Schema for creating a conversation."""

    title: Optional[str] = None


class ConversationResponse(BaseModel):
    """Schema for conversation response."""

    id: UUID
    user_id: Optional[UUID] = None
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True


class ConversationDetail(ConversationResponse):
    """Schema for detailed conversation with messages."""

    messages: List[MessageResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True
