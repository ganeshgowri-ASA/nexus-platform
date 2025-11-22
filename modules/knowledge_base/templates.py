"""
Templates Module

Article templates, quick start wizards, and style guides.
"""

import logging
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from .kb_types import ContentType
from .models import ContentTemplate

logger = logging.getLogger(__name__)


class TemplateManager:
    """Manager for content templates."""

    def __init__(self, db_session: Session):
        self.db = db_session

    async def create_template(
        self,
        name: str,
        content_type: ContentType,
        template_content: str,
        description: Optional[str] = None,
        placeholders: Optional[List[str]] = None,
        sections: Optional[List[Dict]] = None,
    ) -> ContentTemplate:
        """Create a new content template."""
        try:
            template = ContentTemplate(
                name=name,
                content_type=content_type.value,
                template_content=template_content,
                description=description,
                placeholders=placeholders or [],
                sections=sections or [],
            )

            self.db.add(template)
            self.db.commit()
            self.db.refresh(template)

            return template

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating template: {str(e)}")
            raise

    async def list_templates(
        self,
        content_type: Optional[ContentType] = None,
    ) -> List[ContentTemplate]:
        """List available templates."""
        try:
            query = self.db.query(ContentTemplate).filter(
                ContentTemplate.is_active == True
            )

            if content_type:
                query = query.filter(
                    ContentTemplate.content_type == content_type.value
                )

            return query.all()

        except Exception as e:
            logger.error(f"Error listing templates: {str(e)}")
            return []

    async def apply_template(
        self,
        template_id: UUID,
        replacements: Optional[Dict[str, str]] = None,
    ) -> str:
        """Apply template with replacements."""
        try:
            template = (
                self.db.query(ContentTemplate)
                .filter(ContentTemplate.id == template_id)
                .first()
            )

            if not template:
                raise ValueError(f"Template {template_id} not found")

            content = template.template_content

            # Apply replacements
            if replacements:
                for key, value in replacements.items():
                    content = content.replace(f"{{{key}}}", value)

            # Increment usage count
            template.usage_count += 1
            self.db.commit()

            return content

        except Exception as e:
            logger.error(f"Error applying template: {str(e)}")
            raise
