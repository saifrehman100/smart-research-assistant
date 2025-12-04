"""Web article scraper for extracting content from URLs."""

import logging
import re
from datetime import datetime
from typing import Dict, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md

logger = logging.getLogger(__name__)


class WebScraper:
    """Scraper for extracting article content from web URLs."""

    def __init__(self, timeout: int = 30):
        """
        Initialize web scraper.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    def _is_valid_url(self, url: str) -> bool:
        """
        Validate URL for security.

        Args:
            url: URL to validate

        Returns:
            True if URL is valid and safe
        """
        try:
            parsed = urlparse(url)
            # Block localhost and private IPs
            if parsed.hostname in ["localhost", "127.0.0.1", "0.0.0.0"]:
                return False
            if parsed.hostname and parsed.hostname.startswith("192.168."):
                return False
            if parsed.hostname and parsed.hostname.startswith("10."):
                return False
            # Require http or https
            if parsed.scheme not in ["http", "https"]:
                return False
            return True
        except Exception:
            return False

    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text.

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)
        # Remove excessive newlines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict:
        """
        Extract metadata from HTML.

        Args:
            soup: BeautifulSoup object
            url: Source URL

        Returns:
            Metadata dictionary
        """
        metadata = {
            "url": url,
            "domain": urlparse(url).netloc,
            "scraped_at": datetime.utcnow().isoformat(),
        }

        # Try to extract title
        title_tag = soup.find("title")
        if title_tag:
            metadata["title"] = title_tag.text.strip()

        # Try Open Graph tags
        og_title = soup.find("meta", property="og:title")
        if og_title:
            metadata["title"] = og_title.get("content", "")

        # Try to extract author
        author_meta = soup.find("meta", attrs={"name": "author"})
        if author_meta:
            metadata["author"] = author_meta.get("content", "")

        # Try to extract publish date
        date_meta = soup.find("meta", property="article:published_time")
        if date_meta:
            metadata["publish_date"] = date_meta.get("content", "")

        # Try description
        description = soup.find("meta", attrs={"name": "description"})
        if description:
            metadata["description"] = description.get("content", "")

        return metadata

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """
        Extract main article content from HTML.

        Args:
            soup: BeautifulSoup object

        Returns:
            Extracted text content
        """
        # Remove unwanted elements
        for element in soup(
            ["script", "style", "nav", "header", "footer", "aside", "iframe", "noscript"]
        ):
            element.decompose()

        # Try to find main content container
        main_content = None

        # Common article containers
        for selector in [
            {"name": "article"},
            {"name": "main"},
            {"class_": re.compile(r"(article|content|post|entry|main)", re.I)},
            {"id": re.compile(r"(article|content|post|entry|main)", re.I)},
        ]:
            main_content = soup.find(**selector)
            if main_content:
                break

        # Fallback to body
        if not main_content:
            main_content = soup.find("body")

        if not main_content:
            return ""

        # Convert to markdown for better structure preservation
        markdown_content = md(str(main_content), heading_style="ATX")

        return self._clean_text(markdown_content)

    async def scrape(self, url: str) -> Dict:
        """
        Scrape content from URL.

        Args:
            url: URL to scrape

        Returns:
            Dictionary with title, content, author, and metadata

        Raises:
            ValueError: If URL is invalid
            Exception: If scraping fails
        """
        if not self._is_valid_url(url):
            raise ValueError(f"Invalid or unsafe URL: {url}")

        try:
            logger.info(f"Scraping URL: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "lxml")

            # Extract metadata
            metadata = self._extract_metadata(soup, url)

            # Extract main content
            content = self._extract_main_content(soup)

            if not content or len(content) < 100:
                raise Exception("Insufficient content extracted from URL")

            result = {
                "title": metadata.get("title", "Untitled Article"),
                "content": content,
                "author": metadata.get("author"),
                "metadata": metadata,
            }

            logger.info(
                f"Successfully scraped {len(content)} characters from {url}"
            )
            return result

        except requests.RequestException as e:
            logger.error(f"Request error scraping {url}: {e}")
            raise Exception(f"Failed to fetch URL: {str(e)}")
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            raise
