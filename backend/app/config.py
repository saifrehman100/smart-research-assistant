"""Application configuration management."""

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_env: str = Field(default="development", alias="APP_ENV")
    app_name: str = Field(default="Smart Research Assistant", alias="APP_NAME")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # API
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_workers: int = Field(default=4, alias="API_WORKERS")

    # Google Gemini API
    google_api_key: str = Field(alias="GOOGLE_API_KEY")

    # Database
    database_url: str = Field(alias="DATABASE_URL")
    database_pool_size: int = Field(default=20, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=10, alias="DATABASE_MAX_OVERFLOW")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # Celery
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1", alias="CELERY_BROKER_URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2", alias="CELERY_RESULT_BACKEND"
    )

    # ChromaDB
    chroma_persist_directory: str = Field(
        default="./chroma_data", alias="CHROMA_PERSIST_DIRECTORY"
    )
    chroma_collection_name: str = Field(
        default="research_docs", alias="CHROMA_COLLECTION_NAME"
    )

    # File Upload
    max_upload_size_mb: int = Field(default=50, alias="MAX_UPLOAD_SIZE_MB")
    upload_dir: str = Field(default="./uploads", alias="UPLOAD_DIR")
    allowed_file_types: str = Field(default="pdf,txt,md", alias="ALLOWED_FILE_TYPES")

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    rate_limit_per_minute: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")

    # CORS
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8000", alias="CORS_ORIGINS"
    )

    # JWT
    jwt_secret_key: str = Field(
        default="change_this_secret_key", alias="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expiration_minutes: int = Field(default=10080, alias="JWT_EXPIRATION_MINUTES")

    # RAG Configuration
    chunk_size: int = Field(default=800, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=100, alias="CHUNK_OVERLAP")
    top_k_retrieval: int = Field(default=10, alias="TOP_K_RETRIEVAL")
    top_k_context: int = Field(default=5, alias="TOP_K_CONTEXT")
    relevance_threshold: float = Field(default=0.3, alias="RELEVANCE_THRESHOLD")

    # Gemini Model Configuration
    gemini_chat_model: str = Field(
        default="gemini-2.0-flash-exp", alias="GEMINI_CHAT_MODEL"
    )
    gemini_embedding_model: str = Field(
        default="text-embedding-004", alias="GEMINI_EMBEDDING_MODEL"
    )
    gemini_max_tokens: int = Field(default=8192, alias="GEMINI_MAX_TOKENS")
    gemini_temperature: float = Field(default=0.7, alias="GEMINI_TEMPERATURE")

    # Conversation Settings
    max_conversation_history: int = Field(
        default=5, alias="MAX_CONVERSATION_HISTORY"
    )

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="allow"
    )

    @field_validator("cors_origins")
    @classmethod
    def parse_cors_origins(cls, v: str) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in v.split(",")]

    @field_validator("allowed_file_types")
    @classmethod
    def parse_file_types(cls, v: str) -> List[str]:
        """Parse allowed file types from comma-separated string."""
        return [ft.strip() for ft in v.split(",")]

    @property
    def max_upload_size_bytes(self) -> int:
        """Convert max upload size from MB to bytes."""
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
