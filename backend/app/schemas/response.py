"""Common response schemas."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class StatusResponse(BaseModel):
    """Generic status response."""

    status: str
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Operation completed",
                "data": {},
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="healthy")
    version: str
    database: str = Field(default="unknown")
    vector_store: str = Field(default="unknown")
    gemini_api: str = Field(default="unknown")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "database": "connected",
                "vector_store": "connected",
                "gemini_api": "connected",
            }
        }
