"""PDF parser for extracting text from PDF files."""

import logging
from pathlib import Path
from typing import Dict, List

import pdfplumber

logger = logging.getLogger(__name__)


class PDFParser:
    """Parser for extracting text from PDF files."""

    def __init__(self):
        """Initialize PDF parser."""
        pass

    def _extract_metadata(self, pdf) -> Dict:
        """
        Extract metadata from PDF.

        Args:
            pdf: pdfplumber PDF object

        Returns:
            Metadata dictionary
        """
        metadata = {
            "page_count": len(pdf.pages),
            "parser": "pdfplumber",
        }

        # Extract PDF metadata
        if pdf.metadata:
            pdf_meta = pdf.metadata
            if pdf_meta.get("Title"):
                metadata["title"] = pdf_meta["Title"]
            if pdf_meta.get("Author"):
                metadata["author"] = pdf_meta["Author"]
            if pdf_meta.get("Creator"):
                metadata["creator"] = pdf_meta["Creator"]
            if pdf_meta.get("Producer"):
                metadata["producer"] = pdf_meta["Producer"]
            if pdf_meta.get("CreationDate"):
                metadata["creation_date"] = pdf_meta["CreationDate"]

        return metadata

    def _extract_text_from_page(self, page, page_num: int) -> Dict:
        """
        Extract text from a single page.

        Args:
            page: pdfplumber page object
            page_num: Page number (1-indexed)

        Returns:
            Dictionary with page number and text
        """
        try:
            text = page.extract_text()
            if not text:
                text = ""

            return {
                "page_number": page_num,
                "text": text.strip(),
                "char_count": len(text),
            }
        except Exception as e:
            logger.warning(f"Error extracting text from page {page_num}: {e}")
            return {
                "page_number": page_num,
                "text": "",
                "char_count": 0,
            }

    async def parse(self, file_path: str) -> Dict:
        """
        Parse PDF file and extract text.

        Args:
            file_path: Path to PDF file

        Returns:
            Dictionary with title, content, pages, and metadata

        Raises:
            FileNotFoundError: If file doesn't exist
            Exception: If parsing fails
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        try:
            logger.info(f"Parsing PDF: {file_path}")

            with pdfplumber.open(file_path) as pdf:
                # Extract metadata
                metadata = self._extract_metadata(pdf)

                # Extract text from all pages
                pages = []
                full_text_parts = []

                for i, page in enumerate(pdf.pages, start=1):
                    page_data = self._extract_text_from_page(page, i)
                    pages.append(page_data)

                    if page_data["text"]:
                        full_text_parts.append(
                            f"[Page {i}]\n{page_data['text']}"
                        )

                # Combine all text
                full_text = "\n\n".join(full_text_parts)

                if not full_text or len(full_text) < 50:
                    raise Exception("Insufficient text extracted from PDF")

                # Generate title from filename if not in metadata
                title = metadata.get("title", path.stem.replace("_", " ").title())

                result = {
                    "title": title,
                    "content": full_text,
                    "author": metadata.get("author"),
                    "pages": pages,
                    "metadata": metadata,
                }

                logger.info(
                    f"Successfully parsed PDF with {len(pages)} pages, "
                    f"{len(full_text)} characters"
                )
                return result

        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {e}")
            raise
