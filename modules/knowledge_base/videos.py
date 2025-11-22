"""
Video Management Module

Video hosting with transcription, chapters, and interactive features.
"""

import logging
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from .kb_types import ContentStatus, Language
from .models import Video

logger = logging.getLogger(__name__)


class VideoManager:
    """Manager for video content with enhanced features."""

    def __init__(self, db_session: Session):
        self.db = db_session

    async def create_video(
        self,
        title: str,
        description: str,
        video_url: str,
        author_id: UUID,
        duration: int,
        thumbnail_url: Optional[str] = None,
        chapters: Optional[List[Dict]] = None,
        transcripts: Optional[List[Dict]] = None,
        **kwargs,
    ) -> Video:
        """Create a new video."""
        try:
            slug = self._generate_slug(title)

            video = Video(
                title=title,
                slug=slug,
                description=description,
                video_url=video_url,
                author_id=author_id,
                duration=duration,
                thumbnail_url=thumbnail_url,
                chapters=chapters or [],
                transcripts=transcripts or [],
                **kwargs,
            )

            self.db.add(video)
            self.db.commit()
            self.db.refresh(video)

            logger.info(f"Created video: {video.id} - {video.title}")
            return video

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating video: {str(e)}")
            raise

    async def add_transcript(
        self,
        video_id: UUID,
        transcript_segments: List[Dict],
        language: Language = Language.EN,
    ) -> Video:
        """Add or update video transcript."""
        try:
            video = self.db.query(Video).filter(Video.id == video_id).first()
            if not video:
                raise ValueError(f"Video {video_id} not found")

            video.transcripts = transcript_segments
            self.db.commit()
            self.db.refresh(video)

            return video

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding transcript: {str(e)}")
            raise

    async def track_watch_time(
        self,
        video_id: UUID,
        watch_duration: int,
        user_id: Optional[UUID] = None,
    ) -> None:
        """Track video watch time analytics."""
        try:
            video = self.db.query(Video).filter(Video.id == video_id).first()
            if not video:
                return

            video.view_count += 1
            video.watch_time += watch_duration

            # Calculate completion rate
            if video.duration > 0:
                completion_rate = (watch_duration / video.duration) * 100
                # Update average completion rate
                total_views = video.view_count
                video.average_completion_rate = (
                    (video.average_completion_rate * (total_views - 1) + completion_rate)
                    / total_views
                )

            self.db.commit()

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error tracking watch time: {str(e)}")

    async def search_transcript(
        self,
        video_id: UUID,
        query: str,
    ) -> List[Dict]:
        """Search within video transcript."""
        try:
            video = self.db.query(Video).filter(Video.id == video_id).first()
            if not video or not video.transcripts:
                return []

            results = []
            for segment in video.transcripts:
                if query.lower() in segment.get("text", "").lower():
                    results.append({
                        "start_time": segment.get("start_time"),
                        "end_time": segment.get("end_time"),
                        "text": segment.get("text"),
                    })

            return results

        except Exception as e:
            logger.error(f"Error searching transcript: {str(e)}")
            return []

    def _generate_slug(self, title: str) -> str:
        """Generate URL slug from title."""
        import re

        slug = title.lower().strip()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[-\s]+", "-", slug)

        base_slug = slug
        counter = 1
        while self.db.query(Video).filter(Video.slug == slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug
