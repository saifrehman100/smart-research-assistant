"""Text processor for plain text input."""

import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class TextProcessor:
    """Processor for plain text input."""

    def __init__(self):
        """Initialize text processor."""
        pass

    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text.

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        lines = [line.strip() for line in text.split("\n")]
        # Remove empty lines but preserve paragraph breaks
        cleaned_lines = []
        prev_empty = False

        for line in lines:
            if line:
                cleaned_lines.append(line)
                prev_empty = False
            elif not prev_empty:
                cleaned_lines.append("")
                prev_empty = True

        return "\n".join(cleaned_lines).strip()

    async def process(
        self,
        text: str,
        title: Optional[str] = None,
        author: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """
        Process plain text input.

        Args:
            text: Text content
            title: Optional title
            author: Optional author
            metadata: Optional metadata dictionary

        Returns:
            Dictionary with title, content, author, and metadata

        Raises:
            ValueError: If text is empty or too short
        """
        if not text or len(text.strip()) < 10:
            raise ValueError("Text is too short or empty")

        try:
            logger.info(f"Processing text input ({len(text)} characters)")

            # Clean text
            cleaned_text = self._clean_text(text)

            # Generate title from first line if not provided
            if not title:
                first_line = cleaned_text.split("\n")[0]
                # Limit title length
                title = first_line[:100] if len(first_line) <= 100 else first_line[:97] + "..."

            # Build metadata
            meta = metadata or {}
            meta.update(
                {
                    "processed_at": datetime.utcnow().isoformat(),
                    "original_length": len(text),
                    "cleaned_length": len(cleaned_text),
                    "source_type": "text",
                }
            )

            result = {
                "title": title,
                "content": cleaned_text,
                "author": author,
                "metadata": meta,
            }

            logger.info(f"Successfully processed text: '{title}'")
            return result

        except Exception as e:
            logger.error(f"Error processing text: {e}")
            raise
