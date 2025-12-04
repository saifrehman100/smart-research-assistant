"""Google Gemini API client with retry logic and error handling."""

import logging
from typing import AsyncGenerator, List

import google.generativeai as genai
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for interacting with Google Gemini API."""

    def __init__(self):
        """Initialize Gemini client with API key."""
        genai.configure(api_key=settings.google_api_key)
        self.chat_model = genai.GenerativeModel(settings.gemini_chat_model)
        self.embedding_model = settings.gemini_embedding_model
        logger.info(
            f"Gemini client initialized with chat model: {settings.gemini_chat_model}"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using Gemini.

        Args:
            text: Text to embed

        Returns:
            List of embedding values

        Raises:
            Exception: If embedding generation fails
        """
        try:
            result = genai.embed_content(
                model=f"models/{self.embedding_model}",
                content=text,
                task_type="retrieval_document",
            )
            return result["embedding"]
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for search query.

        Args:
            query: Query text to embed

        Returns:
            List of embedding values

        Raises:
            Exception: If embedding generation fails
        """
        try:
            result = genai.embed_content(
                model=f"models/{self.embedding_model}",
                content=query,
                task_type="retrieval_query",
            )
            return result["embedding"]
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            raise

    async def generate_embeddings_batch(
        self, texts: List[str], batch_size: int = 100
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process at once

        Returns:
            List of embedding vectors
        """
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            logger.info(f"Processing batch {i // batch_size + 1} of {len(texts) // batch_size + 1}")

            for text in batch:
                try:
                    embedding = await self.generate_embedding(text)
                    embeddings.append(embedding)
                except Exception as e:
                    logger.error(f"Failed to generate embedding for text: {e}")
                    # Use zero vector as fallback
                    embeddings.append([0.0] * 768)

        return embeddings

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def generate_response(
        self, prompt: str, context: str = "", max_tokens: int = None
    ) -> str:
        """
        Generate text response using Gemini.

        Args:
            prompt: User prompt/question
            context: Additional context for the response
            max_tokens: Maximum tokens in response

        Returns:
            Generated response text

        Raises:
            Exception: If generation fails
        """
        try:
            full_prompt = f"{context}\n\n{prompt}" if context else prompt

            response = self.chat_model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens or settings.gemini_max_tokens,
                    temperature=settings.gemini_temperature,
                ),
            )

            return response.text
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    async def generate_response_stream(
        self, prompt: str, context: str = ""
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming text response using Gemini.

        Args:
            prompt: User prompt/question
            context: Additional context for the response

        Yields:
            Chunks of generated text

        Raises:
            Exception: If generation fails
        """
        try:
            full_prompt = f"{context}\n\n{prompt}" if context else prompt

            response = self.chat_model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=settings.gemini_max_tokens,
                    temperature=settings.gemini_temperature,
                ),
                stream=True,
            )

            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error(f"Error in streaming response: {e}")
            raise

    async def generate_summary(self, text: str, max_length: int = 200) -> str:
        """
        Generate a concise summary of text.

        Args:
            text: Text to summarize
            max_length: Maximum summary length in characters

        Returns:
            Summary text
        """
        try:
            prompt = f"Provide a concise summary (max {max_length} characters) of the following text:\n\n{text}"
            summary = await self.generate_response(prompt, max_tokens=100)
            return summary.strip()
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return text[:max_length] + "..." if len(text) > max_length else text


# Global Gemini client instance
_gemini_client: GeminiClient | None = None


def get_gemini_client() -> GeminiClient:
    """Get or create Gemini client instance."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client
