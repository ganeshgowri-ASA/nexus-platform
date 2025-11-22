"""
Content management module for content creation, templates, and AI suggestions.

This module provides:
- Content creation and editing
- Template management
- AI-powered content suggestions
- Media management
- Content library
"""
from datetime import datetime
from typing import Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
from loguru import logger
import anthropic
from anthropic import Anthropic

from database import ContentItem, Template, User, ContentType
from config import settings
from .calendar_types import (
    CalendarEvent,
    ContentFormat,
    MediaAsset,
    ContentMetadata,
)


class ContentManager:
    """Content manager for creation, templates, and AI assistance."""

    def __init__(self, db: Session):
        """
        Initialize content manager.

        Args:
            db: Database session
        """
        self.db = db
        self.ai_client: Optional[Anthropic] = None

        # Initialize AI client if API key is available
        if settings.anthropic_api_key:
            self.ai_client = Anthropic(api_key=settings.anthropic_api_key)

        logger.info("ContentManager initialized")

    # Content Creation
    def create_content(
        self,
        title: str,
        content: str,
        content_type: ContentFormat,
        creator_id: int,
        metadata: Optional[ContentMetadata] = None,
    ) -> CalendarEvent:
        """
        Create new content.

        Args:
            title: Content title
            content: Content text
            content_type: Type of content
            creator_id: Creator user ID
            metadata: Optional content metadata

        Returns:
            Created calendar event
        """
        try:
            metadata = metadata or ContentMetadata()

            content_item = ContentItem(
                title=title,
                content=content,
                content_type=self._map_content_format(content_type),
                creator_id=creator_id,
                tags=metadata.tags,
                metadata={
                    "categories": metadata.categories,
                    "keywords": metadata.keywords,
                    "target_audience": metadata.target_audience,
                    "language": metadata.language,
                    "location": metadata.location,
                    "custom_fields": metadata.custom_fields,
                },
            )

            self.db.add(content_item)
            self.db.commit()
            self.db.refresh(content_item)

            logger.info(f"Created content: {content_item.id} - {title}")
            return self._content_item_to_event(content_item)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating content: {e}")
            raise

    def update_content(
        self,
        content_id: int,
        updates: dict[str, Any],
    ) -> CalendarEvent:
        """
        Update existing content.

        Args:
            content_id: Content ID to update
            updates: Dictionary of fields to update

        Returns:
            Updated calendar event
        """
        try:
            content_item = (
                self.db.query(ContentItem)
                .filter(ContentItem.id == content_id)
                .first()
            )

            if not content_item:
                raise ValueError(f"Content {content_id} not found")

            # Track version if content changes
            if "content" in updates and updates["content"] != content_item.content:
                content_item.version += 1

            # Update fields
            for key, value in updates.items():
                if hasattr(content_item, key):
                    setattr(content_item, key, value)

            content_item.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(content_item)

            logger.info(f"Updated content: {content_id}")
            return self._content_item_to_event(content_item)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating content {content_id}: {e}")
            raise

    def get_content(self, content_id: int) -> Optional[CalendarEvent]:
        """
        Get content by ID.

        Args:
            content_id: Content ID

        Returns:
            Calendar event or None if not found
        """
        try:
            content_item = (
                self.db.query(ContentItem)
                .filter(ContentItem.id == content_id)
                .first()
            )

            if not content_item:
                return None

            return self._content_item_to_event(content_item)

        except Exception as e:
            logger.error(f"Error getting content {content_id}: {e}")
            raise

    def search_content(
        self,
        query: str,
        content_type: Optional[ContentFormat] = None,
        tags: Optional[list[str]] = None,
        limit: int = 50,
    ) -> list[CalendarEvent]:
        """
        Search content library.

        Args:
            query: Search query
            content_type: Filter by content type
            tags: Filter by tags
            limit: Maximum results

        Returns:
            List of matching calendar events
        """
        try:
            db_query = self.db.query(ContentItem)

            # Text search
            if query:
                db_query = db_query.filter(
                    or_(
                        ContentItem.title.ilike(f"%{query}%"),
                        ContentItem.content.ilike(f"%{query}%"),
                    )
                )

            # Filter by content type
            if content_type:
                db_type = self._map_content_format(content_type)
                db_query = db_query.filter(ContentItem.content_type == db_type)

            # Filter by tags
            if tags:
                for tag in tags:
                    db_query = db_query.filter(ContentItem.tags.contains([tag]))

            items = db_query.order_by(ContentItem.created_at.desc()).limit(limit).all()

            events = [self._content_item_to_event(item) for item in items]

            logger.info(f"Search returned {len(events)} results for query: {query}")
            return events

        except Exception as e:
            logger.error(f"Error searching content: {e}")
            raise

    # Template Management
    def create_template(
        self,
        name: str,
        description: str,
        content_type: ContentFormat,
        template_content: str,
        variables: Optional[list[str]] = None,
        category: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Create content template.

        Args:
            name: Template name
            description: Template description
            content_type: Content type
            template_content: Template content with variables
            variables: List of variable names
            category: Template category

        Returns:
            Created template data
        """
        try:
            template = Template(
                name=name,
                description=description,
                content_type=self._map_content_format(content_type),
                template_content=template_content,
                variables=variables or [],
                category=category,
                is_active=True,
            )

            self.db.add(template)
            self.db.commit()
            self.db.refresh(template)

            logger.info(f"Created template: {template.id} - {name}")
            return self._template_to_dict(template)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating template: {e}")
            raise

    def get_templates(
        self,
        content_type: Optional[ContentFormat] = None,
        category: Optional[str] = None,
        active_only: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Get templates.

        Args:
            content_type: Filter by content type
            category: Filter by category
            active_only: Only return active templates

        Returns:
            List of templates
        """
        try:
            query = self.db.query(Template)

            if active_only:
                query = query.filter(Template.is_active == True)

            if content_type:
                db_type = self._map_content_format(content_type)
                query = query.filter(Template.content_type == db_type)

            if category:
                query = query.filter(Template.category == category)

            templates = query.order_by(Template.created_at.desc()).all()

            return [self._template_to_dict(t) for t in templates]

        except Exception as e:
            logger.error(f"Error getting templates: {e}")
            raise

    def apply_template(
        self,
        template_id: int,
        variables: dict[str, str],
    ) -> str:
        """
        Apply template with variable substitution.

        Args:
            template_id: Template ID
            variables: Variable values

        Returns:
            Rendered content
        """
        try:
            template = (
                self.db.query(Template).filter(Template.id == template_id).first()
            )

            if not template:
                raise ValueError(f"Template {template_id} not found")

            content = template.template_content

            # Substitute variables
            for var_name, var_value in variables.items():
                placeholder = f"{{{{{var_name}}}}}"
                content = content.replace(placeholder, var_value)

            logger.info(f"Applied template: {template_id}")
            return content

        except Exception as e:
            logger.error(f"Error applying template {template_id}: {e}")
            raise

    # AI Content Suggestions
    def generate_content_ideas(
        self,
        topic: str,
        content_type: ContentFormat,
        target_audience: Optional[str] = None,
        tone: Optional[str] = None,
        count: int = 5,
    ) -> list[dict[str, str]]:
        """
        Generate AI-powered content ideas.

        Args:
            topic: Content topic
            content_type: Type of content
            target_audience: Target audience description
            tone: Content tone (e.g., professional, casual, humorous)
            count: Number of ideas to generate

        Returns:
            List of content ideas with titles and descriptions
        """
        if not self.ai_client:
            logger.warning("AI client not initialized")
            return []

        try:
            prompt = f"""Generate {count} creative content ideas for {content_type} about {topic}.

Target Audience: {target_audience or 'General'}
Tone: {tone or 'Professional'}

For each idea, provide:
1. A compelling title
2. A brief description (2-3 sentences)
3. Key points to cover

Format as a numbered list."""

            message = self.ai_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text

            # Parse response into structured ideas
            ideas = self._parse_content_ideas(response_text, count)

            logger.info(f"Generated {len(ideas)} content ideas for topic: {topic}")
            return ideas

        except Exception as e:
            logger.error(f"Error generating content ideas: {e}")
            return []

    def generate_content_draft(
        self,
        title: str,
        description: str,
        content_type: ContentFormat,
        target_audience: Optional[str] = None,
        tone: Optional[str] = None,
        length: str = "medium",
    ) -> str:
        """
        Generate AI-powered content draft.

        Args:
            title: Content title
            description: Content description/brief
            content_type: Type of content
            target_audience: Target audience
            tone: Content tone
            length: Content length (short, medium, long)

        Returns:
            Generated content draft
        """
        if not self.ai_client:
            logger.warning("AI client not initialized")
            return ""

        try:
            length_map = {"short": "150-200 words", "medium": "300-400 words", "long": "600-800 words"}
            word_count = length_map.get(length, "300-400 words")

            prompt = f"""Write a {content_type} content draft.

Title: {title}
Description: {description}
Target Audience: {target_audience or 'General'}
Tone: {tone or 'Professional'}
Length: {word_count}

Write engaging, high-quality content that matches the requirements."""

            message = self.ai_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )

            content_draft = message.content[0].text

            logger.info(f"Generated content draft for: {title}")
            return content_draft

        except Exception as e:
            logger.error(f"Error generating content draft: {e}")
            return ""

    def improve_content(
        self,
        content: str,
        improvement_type: str = "general",
    ) -> str:
        """
        AI-powered content improvement.

        Args:
            content: Original content
            improvement_type: Type of improvement (general, grammar, engagement, seo)

        Returns:
            Improved content
        """
        if not self.ai_client:
            logger.warning("AI client not initialized")
            return content

        try:
            prompts = {
                "general": "Improve this content to make it more engaging and professional:",
                "grammar": "Fix grammar, spelling, and punctuation in this content:",
                "engagement": "Rewrite this content to be more engaging and compelling:",
                "seo": "Optimize this content for SEO while maintaining readability:",
            }

            prompt = f"""{prompts.get(improvement_type, prompts['general'])}

{content}

Provide the improved version."""

            message = self.ai_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )

            improved_content = message.content[0].text

            logger.info(f"Improved content with type: {improvement_type}")
            return improved_content

        except Exception as e:
            logger.error(f"Error improving content: {e}")
            return content

    def generate_hashtags(
        self,
        content: str,
        count: int = 10,
    ) -> list[str]:
        """
        Generate relevant hashtags for content.

        Args:
            content: Content text
            count: Number of hashtags to generate

        Returns:
            List of hashtags
        """
        if not self.ai_client:
            logger.warning("AI client not initialized")
            return []

        try:
            prompt = f"""Generate {count} relevant hashtags for this content:

{content}

Return only the hashtags, one per line, without the # symbol."""

            message = self.ai_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}],
            )

            hashtags_text = message.content[0].text
            hashtags = [
                f"#{tag.strip()}"
                for tag in hashtags_text.split("\n")
                if tag.strip()
            ][:count]

            logger.info(f"Generated {len(hashtags)} hashtags")
            return hashtags

        except Exception as e:
            logger.error(f"Error generating hashtags: {e}")
            return []

    # Media Management
    def add_media(
        self,
        content_id: int,
        media_asset: MediaAsset,
    ) -> CalendarEvent:
        """
        Add media to content.

        Args:
            content_id: Content ID
            media_asset: Media asset to add

        Returns:
            Updated calendar event
        """
        try:
            content_item = (
                self.db.query(ContentItem)
                .filter(ContentItem.id == content_id)
                .first()
            )

            if not content_item:
                raise ValueError(f"Content {content_id} not found")

            media_urls = content_item.media_urls or []
            media_urls.append(media_asset.url)
            content_item.media_urls = media_urls

            if not content_item.thumbnail_url and media_asset.thumbnail_url:
                content_item.thumbnail_url = media_asset.thumbnail_url

            content_item.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(content_item)

            logger.info(f"Added media to content: {content_id}")
            return self._content_item_to_event(content_item)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding media to content {content_id}: {e}")
            raise

    def remove_media(
        self,
        content_id: int,
        media_url: str,
    ) -> CalendarEvent:
        """
        Remove media from content.

        Args:
            content_id: Content ID
            media_url: Media URL to remove

        Returns:
            Updated calendar event
        """
        try:
            content_item = (
                self.db.query(ContentItem)
                .filter(ContentItem.id == content_id)
                .first()
            )

            if not content_item:
                raise ValueError(f"Content {content_id} not found")

            media_urls = content_item.media_urls or []
            if media_url in media_urls:
                media_urls.remove(media_url)
                content_item.media_urls = media_urls

            content_item.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(content_item)

            logger.info(f"Removed media from content: {content_id}")
            return self._content_item_to_event(content_item)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error removing media from content {content_id}: {e}")
            raise

    # Helper Methods
    def _parse_content_ideas(self, response: str, count: int) -> list[dict[str, str]]:
        """Parse AI response into structured content ideas."""
        ideas = []
        lines = response.split("\n")
        current_idea: dict[str, str] = {}

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # New idea detected
            if line[0].isdigit() and "." in line[:3]:
                if current_idea:
                    ideas.append(current_idea)
                current_idea = {"title": line.split(".", 1)[1].strip(), "description": ""}
            elif current_idea:
                current_idea["description"] += line + " "

        if current_idea:
            ideas.append(current_idea)

        return ideas[:count]

    def _content_item_to_event(self, item: ContentItem) -> CalendarEvent:
        """Convert ContentItem to CalendarEvent."""
        from .calendar_types import (
            ScheduleConfig,
            PublishingChannel,
            Priority,
            ApprovalStatus,
        )

        # Build schedule config
        schedule = ScheduleConfig(
            scheduled_time=item.scheduled_at or datetime.utcnow(),
            timezone=item.timezone or "UTC",
        )

        # Build channels
        channels = [
            PublishingChannel(name=ch, platform=ch, is_active=True)
            for ch in (item.channels or [])
        ]

        # Build media
        media = [
            MediaAsset(url=url, type="image", filename=url.split("/")[-1], size=0)
            for url in (item.media_urls or [])
        ]

        # Build metadata
        metadata_dict = item.metadata or {}
        metadata = ContentMetadata(
            tags=item.tags or [],
            categories=metadata_dict.get("categories", []),
            keywords=metadata_dict.get("keywords", []),
            target_audience=metadata_dict.get("target_audience"),
            language=metadata_dict.get("language", "en"),
        )

        return CalendarEvent(
            id=item.id,
            title=item.title,
            content=item.content,
            content_type=ContentFormat.TEXT,
            status=ApprovalStatus.DRAFT,
            priority=Priority.MEDIUM,
            schedule=schedule,
            channels=channels,
            media=media,
            metadata=metadata,
            creator_id=item.creator_id,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    def _template_to_dict(self, template: Template) -> dict[str, Any]:
        """Convert Template to dictionary."""
        return {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "content_type": template.content_type,
            "template_content": template.template_content,
            "variables": template.variables,
            "category": template.category,
            "is_active": template.is_active,
            "created_at": template.created_at,
            "updated_at": template.updated_at,
        }

    def _map_content_format(self, format: ContentFormat) -> ContentType:
        """Map ContentFormat to ContentType."""
        mapping = {
            ContentFormat.TEXT: ContentType.SOCIAL_POST,
            ContentFormat.IMAGE: ContentType.IMAGE,
            ContentFormat.VIDEO: ContentType.VIDEO,
            ContentFormat.ARTICLE: ContentType.ARTICLE,
            ContentFormat.STORY: ContentType.STORY,
            ContentFormat.REEL: ContentType.REEL,
        }
        return mapping.get(format, ContentType.SOCIAL_POST)
