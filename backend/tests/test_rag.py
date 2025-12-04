"""RAG service tests."""

import pytest

from app.utils.citation_formatter import format_citation, validate_citation_format
from app.utils.text_processing import clean_whitespace, truncate_text


def test_format_citation():
    """Test citation formatting."""
    citation = format_citation(
        title="Machine Learning Basics",
        doc_type="pdf",
        page_number=5,
        author="John Doe",
    )

    assert "Machine Learning Basics" in citation
    assert "Page 5" in citation
    assert "John Doe" in citation


def test_format_citation_youtube():
    """Test YouTube citation formatting."""
    citation = format_citation(
        title="How AI Works",
        doc_type="youtube",
        timestamp="03:45",
    )

    assert "How AI Works" in citation
    assert "03:45" in citation


def test_validate_citation_format():
    """Test citation validation."""
    valid_citation = "Source: Test Document, Page 1"
    invalid_citation = "Not a citation"

    assert validate_citation_format(valid_citation) is True
    assert validate_citation_format(invalid_citation) is False


def test_clean_whitespace():
    """Test whitespace cleaning."""
    text = "This  has   extra    spaces.\n\n\n\nAnd newlines."
    cleaned = clean_whitespace(text)

    assert "  " not in cleaned
    assert "\n\n\n" not in cleaned


def test_truncate_text():
    """Test text truncation."""
    text = "This is a long text that needs to be truncated for display purposes."
    truncated = truncate_text(text, max_length=20)

    assert len(truncated) <= 20
    assert truncated.endswith("...")


def test_truncate_short_text():
    """Test truncation of short text."""
    text = "Short text"
    truncated = truncate_text(text, max_length=100)

    assert truncated == text
    assert not truncated.endswith("...")
