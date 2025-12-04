"""Citation formatting utilities."""

from typing import Dict, Optional


def format_citation(
    title: str,
    doc_type: str,
    page_number: Optional[int] = None,
    timestamp: Optional[str] = None,
    author: Optional[str] = None,
) -> str:
    """
    Format a citation string.

    Args:
        title: Document title
        doc_type: Type of document (pdf, url, youtube, text)
        page_number: Optional page number for PDFs
        timestamp: Optional timestamp for videos
        author: Optional author name

    Returns:
        Formatted citation string

    Examples:
        "Source: Machine Learning Basics, Page 5"
        "Source: How AI Works (by John Doe), 03:45"
        "Source: Introduction to Python"
    """
    citation_parts = ["Source:", title]

    if author:
        citation_parts.append(f"(by {author})")

    if doc_type == "pdf" and page_number:
        citation_parts.append(f"Page {page_number}")
    elif doc_type == "youtube" and timestamp:
        citation_parts.append(timestamp)

    return " ".join(citation_parts)


def extract_citations(text: str) -> list:
    """
    Extract citation markers from generated text.

    Args:
        text: Generated text with citations

    Returns:
        List of citation strings
    """
    import re

    # Match patterns like [Source: Title, Page X] or [Source: Title]
    pattern = r'\[Source:[^\]]+\]'
    return re.findall(pattern, text)


def validate_citation_format(citation: str) -> bool:
    """
    Validate if a citation string is properly formatted.

    Args:
        citation: Citation string to validate

    Returns:
        True if valid, False otherwise
    """
    import re

    # Basic validation: should start with "Source:" and contain title
    pattern = r'^Source:\s+.+$'
    return bool(re.match(pattern, citation))
