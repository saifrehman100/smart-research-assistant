"""Document ingestion tests."""

import pytest

from app.services.ingestion import TextProcessor
from app.services.chunker import TextChunker


@pytest.mark.asyncio
async def test_text_processor():
    """Test text processor."""
    processor = TextProcessor()

    text = "This is a test document.\n\nIt has multiple paragraphs.\n\nAnd some content."
    result = await processor.process(
        text=text,
        title="Test Document",
        author="Test Author",
    )

    assert result["title"] == "Test Document"
    assert result["author"] == "Test Author"
    assert result["content"] is not None
    assert len(result["content"]) > 0
    assert "metadata" in result


def test_text_chunker():
    """Test text chunking."""
    chunker = TextChunker(chunk_size=100, chunk_overlap=20)

    text = """
    Machine learning is a subset of artificial intelligence.
    It focuses on building systems that learn from data.
    There are three main types: supervised, unsupervised, and reinforcement learning.
    Each type has its own applications and use cases.
    """

    chunks = chunker.chunk_text(text, source_metadata={"source": "test"})

    assert len(chunks) > 0
    for chunk in chunks:
        assert "content" in chunk
        assert "metadata" in chunk
        assert chunk["metadata"]["chunk_index"] >= 0
        assert len(chunk["content"]) > 0


def test_text_chunker_with_metadata():
    """Test text chunking preserves metadata."""
    chunker = TextChunker()

    text = "Short text for testing."
    metadata = {"title": "Test", "author": "Tester"}

    chunks = chunker.chunk_text(text, source_metadata=metadata)

    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk["metadata"]["title"] == "Test"
        assert chunk["metadata"]["author"] == "Tester"


def test_empty_text_chunking():
    """Test chunking empty text."""
    chunker = TextChunker()

    chunks = chunker.chunk_text("", source_metadata={})

    assert len(chunks) == 0
