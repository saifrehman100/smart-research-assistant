"""Text chunking service with semantic splitting."""

import logging
import re
from typing import Dict, List

from app.config import settings

logger = logging.getLogger(__name__)


class TextChunker:
    """Service for intelligently chunking text documents."""

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
    ):
        """
        Initialize text chunker.

        Args:
            chunk_size: Target size for each chunk in characters
            chunk_overlap: Overlap between chunks in characters
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        # Simple sentence splitter - could be improved with NLTK
        sentence_endings = r'(?<=[.!?])\s+(?=[A-Z])'
        sentences = re.split(sentence_endings, text)
        return [s.strip() for s in sentences if s.strip()]

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """
        Split text into paragraphs.

        Args:
            text: Text to split

        Returns:
            List of paragraphs
        """
        # Split on double newlines
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]

    def _create_chunks_from_paragraphs(
        self, paragraphs: List[str], metadata: Dict
    ) -> List[Dict]:
        """
        Create chunks from paragraphs, respecting size limits.

        Args:
            paragraphs: List of paragraphs
            metadata: Source metadata

        Returns:
            List of chunk dictionaries
        """
        chunks = []
        current_chunk = ""
        current_paragraphs = []

        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size
            if len(current_chunk) + len(paragraph) > self.chunk_size:
                # Save current chunk if it's not empty
                if current_chunk:
                    chunks.append({
                        "content": current_chunk.strip(),
                        "metadata": {
                            **metadata,
                            "paragraph_count": len(current_paragraphs),
                        }
                    })

                # Start new chunk
                # If paragraph itself is larger than chunk_size, split it
                if len(paragraph) > self.chunk_size:
                    # Split into sentences
                    sentences = self._split_into_sentences(paragraph)
                    temp_chunk = ""

                    for sentence in sentences:
                        if len(temp_chunk) + len(sentence) > self.chunk_size:
                            if temp_chunk:
                                chunks.append({
                                    "content": temp_chunk.strip(),
                                    "metadata": metadata,
                                })
                            temp_chunk = sentence
                        else:
                            temp_chunk += " " + sentence if temp_chunk else sentence

                    # Handle overlap - keep last part for next chunk
                    if temp_chunk:
                        overlap_start = max(0, len(temp_chunk) - self.chunk_overlap)
                        current_chunk = temp_chunk[overlap_start:]
                        current_paragraphs = [current_chunk]
                else:
                    current_chunk = paragraph
                    current_paragraphs = [paragraph]
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
                current_paragraphs.append(paragraph)

        # Add final chunk
        if current_chunk:
            chunks.append({
                "content": current_chunk.strip(),
                "metadata": {
                    **metadata,
                    "paragraph_count": len(current_paragraphs),
                }
            })

        return chunks

    def chunk_text(
        self,
        text: str,
        source_metadata: Dict = None,
    ) -> List[Dict]:
        """
        Chunk text into overlapping segments.

        Args:
            text: Text to chunk
            source_metadata: Metadata about the source document

        Returns:
            List of dictionaries with content and metadata

        Example:
            [
                {
                    "content": "chunk text...",
                    "metadata": {
                        "source": "document.pdf",
                        "chunk_index": 0,
                        ...
                    }
                },
                ...
            ]
        """
        if not text or len(text.strip()) < 10:
            logger.warning("Text too short to chunk")
            return []

        metadata = source_metadata or {}

        logger.info(f"Chunking text of length {len(text)}")

        # First, try splitting by paragraphs
        paragraphs = self._split_into_paragraphs(text)

        # Create chunks from paragraphs
        chunks = self._create_chunks_from_paragraphs(paragraphs, metadata)

        # Add chunk indices
        for i, chunk in enumerate(chunks):
            chunk["metadata"]["chunk_index"] = i
            chunk["metadata"]["total_chunks"] = len(chunks)
            chunk["metadata"]["char_count"] = len(chunk["content"])

        logger.info(f"Created {len(chunks)} chunks from text")
        return chunks

    def chunk_document_with_pages(
        self,
        pages: List[Dict],
        source_metadata: Dict = None,
    ) -> List[Dict]:
        """
        Chunk document that has page information (e.g., PDF).

        Args:
            pages: List of page dictionaries with 'page_number' and 'text'
            source_metadata: Metadata about the source document

        Returns:
            List of chunk dictionaries
        """
        all_chunks = []
        metadata = source_metadata or {}

        for page_data in pages:
            page_num = page_data.get("page_number", 0)
            page_text = page_data.get("text", "")

            if not page_text or len(page_text.strip()) < 10:
                continue

            # Add page number to metadata
            page_metadata = {
                **metadata,
                "page_number": page_num,
            }

            # Chunk the page text
            page_chunks = self.chunk_text(page_text, page_metadata)
            all_chunks.extend(page_chunks)

        # Re-index all chunks
        for i, chunk in enumerate(all_chunks):
            chunk["metadata"]["chunk_index"] = i
            chunk["metadata"]["total_chunks"] = len(all_chunks)

        logger.info(f"Created {len(all_chunks)} chunks from {len(pages)} pages")
        return all_chunks


def get_chunker() -> TextChunker:
    """Get text chunker instance."""
    return TextChunker()
