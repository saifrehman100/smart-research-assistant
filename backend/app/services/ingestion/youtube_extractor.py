"""YouTube transcript extractor."""

import logging
import re
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlparse

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

logger = logging.getLogger(__name__)


class YouTubeExtractor:
    """Extractor for YouTube video transcripts."""

    def __init__(self):
        """Initialize YouTube extractor."""
        pass

    def _extract_video_id(self, url: str) -> Optional[str]:
        """
        Extract video ID from YouTube URL.

        Args:
            url: YouTube URL

        Returns:
            Video ID or None

        Examples:
            https://www.youtube.com/watch?v=VIDEO_ID
            https://youtu.be/VIDEO_ID
            https://www.youtube.com/embed/VIDEO_ID
        """
        patterns = [
            r"(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})",
            r"youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        # Try parsing query parameters
        try:
            parsed = urlparse(url)
            if parsed.hostname in ["www.youtube.com", "youtube.com"]:
                query = parse_qs(parsed.query)
                if "v" in query:
                    return query["v"][0]
        except Exception:
            pass

        return None

    def _format_timestamp(self, seconds: float) -> str:
        """
        Format seconds to timestamp string (HH:MM:SS).

        Args:
            seconds: Time in seconds

        Returns:
            Formatted timestamp
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    def _combine_transcript(
        self, transcript: List[Dict], include_timestamps: bool = True
    ) -> str:
        """
        Combine transcript segments into full text.

        Args:
            transcript: List of transcript segments
            include_timestamps: Whether to include timestamps

        Returns:
            Combined transcript text
        """
        if include_timestamps:
            parts = []
            for segment in transcript:
                timestamp = self._format_timestamp(segment["start"])
                text = segment["text"].strip()
                parts.append(f"[{timestamp}] {text}")
            return "\n".join(parts)
        else:
            return " ".join(segment["text"].strip() for segment in transcript)

    async def extract(self, url: str) -> Dict:
        """
        Extract transcript from YouTube video.

        Args:
            url: YouTube video URL

        Returns:
            Dictionary with title, content, metadata, and transcript

        Raises:
            ValueError: If URL is invalid
            Exception: If extraction fails
        """
        video_id = self._extract_video_id(url)
        if not video_id:
            raise ValueError(f"Invalid YouTube URL: {url}")

        try:
            logger.info(f"Extracting transcript for video: {video_id}")

            # Fetch transcript
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)

            if not transcript_list:
                raise Exception("Empty transcript received")

            # Combine transcript with timestamps
            full_transcript = self._combine_transcript(
                transcript_list, include_timestamps=True
            )

            # Also create version without timestamps for better embedding
            clean_transcript = self._combine_transcript(
                transcript_list, include_timestamps=False
            )

            # Calculate video duration
            duration_seconds = (
                transcript_list[-1]["start"] + transcript_list[-1]["duration"]
                if transcript_list
                else 0
            )
            duration_formatted = self._format_timestamp(duration_seconds)

            # Build metadata
            metadata = {
                "video_id": video_id,
                "url": url,
                "thumbnail": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
                "duration": duration_formatted,
                "duration_seconds": duration_seconds,
                "transcript_segments": len(transcript_list),
                "extracted_at": datetime.utcnow().isoformat(),
            }

            # Try to extract title from URL or use generic
            # In a real implementation, you might use YouTube Data API for metadata
            title = f"YouTube Video {video_id}"

            result = {
                "title": title,
                "content": full_transcript,  # With timestamps for citations
                "clean_content": clean_transcript,  # Without timestamps for embedding
                "author": None,
                "transcript": transcript_list,
                "metadata": metadata,
            }

            logger.info(
                f"Successfully extracted transcript with {len(transcript_list)} segments, "
                f"{len(full_transcript)} characters"
            )
            return result

        except NoTranscriptFound:
            logger.error(f"No transcript available for video: {video_id}")
            raise Exception(
                "No transcript available for this video. "
                "The video may not have captions enabled."
            )
        except TranscriptsDisabled:
            logger.error(f"Transcripts disabled for video: {video_id}")
            raise Exception("Transcripts are disabled for this video")
        except VideoUnavailable:
            logger.error(f"Video unavailable: {video_id}")
            raise Exception("Video is unavailable or private")
        except Exception as e:
            logger.error(f"Error extracting transcript for {video_id}: {e}")
            raise
