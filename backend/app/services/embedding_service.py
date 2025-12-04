"""Embedding service for generating and managing embeddings."""

import logging
from typing import List

from app.services.gemini_client import get_gemini_client

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings using Gemini."""

    def __init__(self):
        """Initialize embedding service."""
        self.gemini_client = get_gemini_client()

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector

        Raises:
            Exception: If embedding generation fails
        """
        try:
            return await self.gemini_client.generate_embedding(text)
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    async def generate_embeddings(
        self, texts: List[str], batch_size: int = 100
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing

        Returns:
            List of embedding vectors
        """
        try:
            return await self.gemini_client.generate_embeddings_batch(
                texts, batch_size
            )
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise

    async def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for search query.

        Args:
            query: Query text

        Returns:
            Query embedding vector
        """
        try:
            return await self.gemini_client.generate_query_embedding(query)
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            raise


def get_embedding_service() -> EmbeddingService:
    """Get embedding service instance."""
    return EmbeddingService()
