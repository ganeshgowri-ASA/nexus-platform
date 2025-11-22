"""
Wiki Templates Service

Page and section templates for the NEXUS Wiki System including:
- Predefined page templates
- Section templates
- Quick start wizards
- Template variables and substitution
- Custom template management

Author: NEXUS Platform Team
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.utils import get_logger
from modules.wiki.models import WikiTemplate, WikiPage
from modules.wiki.wiki_types import (
    TemplateCategory, WikiTemplate as WikiTemplateSchema,
    ContentFormat
)

logger = get_logger(__name__)


class TemplateService:
    """Manages page templates and content wizards."""

    # Built-in template definitions
    BUILTIN_TEMPLATES = {
        'meeting_notes': {
            'name': 'Meeting Notes',
            'category': TemplateCategory.MEETING_NOTES,
            'content': '''# Meeting Notes: {{title}}

**Date:** {{date}}
**Attendees:** {{attendees}}
**Location:** {{location}}

## Agenda
1. {{agenda_item_1}}
2. {{agenda_item_2}}
3. {{agenda_item_3}}

## Discussion
{{discussion}}

## Action Items
- [ ] {{action_1}} - Assigned to: {{assignee_1}}
- [ ] {{action_2}} - Assigned to: {{assignee_2}}

## Next Meeting
**Date:** {{next_meeting_date}}
**Topics:** {{next_topics}}
''',
            'variables': ['title', 'date', 'attendees', 'location', 'agenda_item_1',
                         'agenda_item_2', 'agenda_item_3', 'discussion', 'action_1',
                         'assignee_1', 'action_2', 'assignee_2', 'next_meeting_date', 'next_topics']
        },
        'project_doc': {
            'name': 'Project Documentation',
            'category': TemplateCategory.PROJECT_DOC,
            'content': '''# {{project_name}}

## Overview
{{overview}}

## Objectives
- {{objective_1}}
- {{objective_2}}
- {{objective_3}}

## Scope
**In Scope:**
{{in_scope}}

**Out of Scope:**
{{out_of_scope}}

## Timeline
| Phase | Duration | Status |
|-------|----------|--------|
| {{phase_1}} | {{duration_1}} | {{status_1}} |
| {{phase_2}} | {{duration_2}} | {{status_2}} |

## Team
| Role | Name | Responsibilities |
|------|------|-----------------|
| {{role_1}} | {{name_1}} | {{resp_1}} |
| {{role_2}} | {{name_2}} | {{resp_2}} |

## Resources
{{resources}}

## Risks and Mitigation
{{risks}}
''',
            'variables': ['project_name', 'overview', 'objective_1', 'objective_2', 'objective_3',
                         'in_scope', 'out_of_scope', 'phase_1', 'duration_1', 'status_1',
                         'phase_2', 'duration_2', 'status_2', 'role_1', 'name_1', 'resp_1',
                         'role_2', 'name_2', 'resp_2', 'resources', 'risks']
        },
        'how_to': {
            'name': 'How-To Guide',
            'category': TemplateCategory.HOW_TO,
            'content': '''# How to {{task_name}}

## Overview
{{overview}}

## Prerequisites
- {{prereq_1}}
- {{prereq_2}}
- {{prereq_3}}

## Steps

### Step 1: {{step_1_title}}
{{step_1_description}}

### Step 2: {{step_2_title}}
{{step_2_description}}

### Step 3: {{step_3_title}}
{{step_3_description}}

## Troubleshooting

### Problem: {{problem_1}}
**Solution:** {{solution_1}}

### Problem: {{problem_2}}
**Solution:** {{solution_2}}

## Additional Resources
- {{resource_1}}
- {{resource_2}}

## Related Articles
- [[{{related_1}}]]
- [[{{related_2}}]]
''',
            'variables': ['task_name', 'overview', 'prereq_1', 'prereq_2', 'prereq_3',
                         'step_1_title', 'step_1_description', 'step_2_title', 'step_2_description',
                         'step_3_title', 'step_3_description', 'problem_1', 'solution_1',
                         'problem_2', 'solution_2', 'resource_1', 'resource_2',
                         'related_1', 'related_2']
        },
        'api_doc': {
            'name': 'API Documentation',
            'category': TemplateCategory.API_DOC,
            'content': '''# {{api_name}} API

## Endpoint: {{endpoint}}

**Method:** {{method}}
**Authentication:** {{auth_type}}

## Description
{{description}}

## Request

### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| {{param_1}} | {{type_1}} | {{required_1}} | {{desc_1}} |
| {{param_2}} | {{type_2}} | {{required_2}} | {{desc_2}} |

### Example Request
```{{language}}
{{request_example}}
```

## Response

### Success Response (200 OK)
```json
{{success_response}}
```

### Error Responses

**400 Bad Request**
```json
{{error_400}}
```

**401 Unauthorized**
```json
{{error_401}}
```

## Rate Limiting
{{rate_limit_info}}

## Examples
{{examples}}
''',
            'variables': ['api_name', 'endpoint', 'method', 'auth_type', 'description',
                         'param_1', 'type_1', 'required_1', 'desc_1',
                         'param_2', 'type_2', 'required_2', 'desc_2',
                         'language', 'request_example', 'success_response',
                         'error_400', 'error_401', 'rate_limit_info', 'examples']
        },
        'troubleshooting': {
            'name': 'Troubleshooting Guide',
            'category': TemplateCategory.TROUBLESHOOTING,
            'content': '''# Troubleshooting: {{issue_name}}

## Symptoms
{{symptoms}}

## Possible Causes
1. {{cause_1}}
2. {{cause_2}}
3. {{cause_3}}

## Diagnostics

### Check 1: {{check_1_name}}
{{check_1_steps}}

### Check 2: {{check_2_name}}
{{check_2_steps}}

## Solutions

### Solution 1: {{solution_1_name}}
**When to use:** {{solution_1_when}}

**Steps:**
1. {{solution_1_step_1}}
2. {{solution_1_step_2}}
3. {{solution_1_step_3}}

### Solution 2: {{solution_2_name}}
**When to use:** {{solution_2_when}}

**Steps:**
1. {{solution_2_step_1}}
2. {{solution_2_step_2}}

## Prevention
{{prevention}}

## Additional Help
If the issue persists, contact: {{contact}}
''',
            'variables': ['issue_name', 'symptoms', 'cause_1', 'cause_2', 'cause_3',
                         'check_1_name', 'check_1_steps', 'check_2_name', 'check_2_steps',
                         'solution_1_name', 'solution_1_when', 'solution_1_step_1',
                         'solution_1_step_2', 'solution_1_step_3', 'solution_2_name',
                         'solution_2_when', 'solution_2_step_1', 'solution_2_step_2',
                         'prevention', 'contact']
        },
        'decision_log': {
            'name': 'Decision Log',
            'category': TemplateCategory.DECISION_LOG,
            'content': '''# Decision: {{decision_title}}

**Date:** {{date}}
**Status:** {{status}}
**Decision Makers:** {{decision_makers}}

## Context
{{context}}

## Problem Statement
{{problem}}

## Options Considered

### Option 1: {{option_1_name}}
**Pros:**
- {{option_1_pro_1}}
- {{option_1_pro_2}}

**Cons:**
- {{option_1_con_1}}
- {{option_1_con_2}}

### Option 2: {{option_2_name}}
**Pros:**
- {{option_2_pro_1}}
- {{option_2_pro_2}}

**Cons:**
- {{option_2_con_1}}
- {{option_2_con_2}}

## Decision
{{decision}}

## Rationale
{{rationale}}

## Consequences
{{consequences}}

## Implementation
{{implementation}}

## Review Date
{{review_date}}
''',
            'variables': ['decision_title', 'date', 'status', 'decision_makers', 'context',
                         'problem', 'option_1_name', 'option_1_pro_1', 'option_1_pro_2',
                         'option_1_con_1', 'option_1_con_2', 'option_2_name',
                         'option_2_pro_1', 'option_2_pro_2', 'option_2_con_1',
                         'option_2_con_2', 'decision', 'rationale', 'consequences',
                         'implementation', 'review_date']
        }
    }

    def __init__(self, db: Session):
        """
        Initialize TemplateService.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create_template(
        self,
        name: str,
        content: str,
        category: TemplateCategory,
        description: Optional[str] = None,
        variables: Optional[List[str]] = None,
        is_public: bool = True,
        created_by: int = 1
    ) -> Optional[WikiTemplate]:
        """
        Create a new template.

        Args:
            name: Template name
            content: Template content with variable placeholders
            category: Template category
            description: Template description
            variables: List of variable names used in template
            is_public: Whether template is publicly available
            created_by: User ID who created the template

        Returns:
            Created WikiTemplate instance

        Example:
            >>> service = TemplateService(db)
            >>> template = service.create_template(
            ...     name="Custom Template",
            ...     content="# {{title}}\\n\\n{{content}}",
            ...     category=TemplateCategory.CUSTOM,
            ...     variables=["title", "content"]
            ... )
        """
        try:
            # Extract variables if not provided
            if variables is None:
                variables = self._extract_variables(content)

            template = WikiTemplate(
                name=name,
                content=content,
                category=category,
                description=description,
                variables=variables,
                is_public=is_public,
                created_by=created_by
            )

            self.db.add(template)
            self.db.commit()
            self.db.refresh(template)

            logger.info(f"Created template: '{template.name}'")
            return template

        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Template with name '{name}' already exists")
            raise ValueError(f"Template '{name}' already exists")
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating template: {str(e)}")
            raise

    def get_template(self, template_id: int) -> Optional[WikiTemplate]:
        """
        Get a template by ID.

        Args:
            template_id: Template ID

        Returns:
            WikiTemplate instance or None

        Example:
            >>> template = service.get_template(5)
        """
        try:
            return self.db.query(WikiTemplate).filter(
                WikiTemplate.id == template_id
            ).first()

        except SQLAlchemyError as e:
            logger.error(f"Error getting template: {str(e)}")
            return None

    def get_template_by_name(self, name: str) -> Optional[WikiTemplate]:
        """
        Get a template by name.

        Args:
            name: Template name

        Returns:
            WikiTemplate instance or None

        Example:
            >>> template = service.get_template_by_name("Meeting Notes")
        """
        try:
            return self.db.query(WikiTemplate).filter(
                WikiTemplate.name == name
            ).first()

        except SQLAlchemyError as e:
            logger.error(f"Error getting template by name: {str(e)}")
            return None

    def list_templates(
        self,
        category: Optional[TemplateCategory] = None,
        public_only: bool = True,
        limit: int = 50
    ) -> List[WikiTemplate]:
        """
        List available templates.

        Args:
            category: Filter by category
            public_only: Only show public templates
            limit: Maximum results

        Returns:
            List of WikiTemplate instances

        Example:
            >>> templates = service.list_templates(category=TemplateCategory.HOW_TO)
        """
        try:
            query = self.db.query(WikiTemplate)

            if category:
                query = query.filter(WikiTemplate.category == category)

            if public_only:
                query = query.filter(WikiTemplate.is_public == True)

            templates = query.order_by(
                desc(WikiTemplate.usage_count),
                WikiTemplate.name
            ).limit(limit).all()

            return templates

        except SQLAlchemyError as e:
            logger.error(f"Error listing templates: {str(e)}")
            return []

    def apply_template(
        self,
        template_id: int,
        variables: Dict[str, Any],
        fill_defaults: bool = True
    ) -> str:
        """
        Apply variable substitution to a template.

        Args:
            template_id: Template ID
            variables: Dictionary of variable values
            fill_defaults: Fill missing variables with placeholders

        Returns:
            Rendered template content

        Example:
            >>> content = service.apply_template(
            ...     template_id=1,
            ...     variables={'title': 'My Page', 'date': '2024-01-01'}
            ... )
        """
        try:
            template = self.get_template(template_id)
            if not template:
                raise ValueError(f"Template {template_id} not found")

            content = template.content

            # Replace variables
            for var in template.variables:
                placeholder = f"{{{{{var}}}}}"
                value = variables.get(var, f"[{var}]" if fill_defaults else "")
                content = content.replace(placeholder, str(value))

            # Increment usage count
            template.usage_count += 1
            self.db.commit()

            return content

        except Exception as e:
            logger.error(f"Error applying template: {str(e)}")
            raise

    def create_page_from_template(
        self,
        template_id: int,
        title: str,
        variables: Dict[str, Any],
        author_id: int,
        **page_kwargs
    ) -> Optional[WikiPage]:
        """
        Create a new page from a template.

        Args:
            template_id: Template ID
            title: Page title
            variables: Template variable values
            author_id: Page author ID
            **page_kwargs: Additional page creation arguments

        Returns:
            Created WikiPage instance

        Example:
            >>> page = service.create_page_from_template(
            ...     template_id=1,
            ...     title="Weekly Meeting - 2024-01-01",
            ...     variables={'date': '2024-01-01', 'attendees': 'Team A'},
            ...     author_id=5
            ... )
        """
        try:
            # Apply template
            content = self.apply_template(template_id, variables)

            # Create page using page manager
            from modules.wiki.pages import PageManager
            from modules.wiki.wiki_types import PageCreateRequest

            page_manager = PageManager(self.db)

            request = PageCreateRequest(
                title=title,
                content=content,
                **page_kwargs
            )

            page = page_manager.create_page(request, author_id)

            logger.info(f"Created page from template: {page.id}")
            return page

        except Exception as e:
            logger.error(f"Error creating page from template: {str(e)}")
            return None

    def get_template_preview(
        self,
        template_id: int,
        sample_values: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Get a preview of template with sample values.

        Args:
            template_id: Template ID
            sample_values: Optional sample variable values

        Returns:
            Preview content

        Example:
            >>> preview = service.get_template_preview(1)
        """
        try:
            template = self.get_template(template_id)
            if not template:
                return ""

            # Use provided samples or generate defaults
            if sample_values is None:
                sample_values = {}
                for var in template.variables:
                    sample_values[var] = f"[Sample {var}]"

            return self.apply_template(template_id, sample_values, fill_defaults=True)

        except Exception as e:
            logger.error(f"Error generating template preview: {str(e)}")
            return ""

    def update_template(
        self,
        template_id: int,
        name: Optional[str] = None,
        content: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[TemplateCategory] = None,
        is_public: Optional[bool] = None
    ) -> Optional[WikiTemplate]:
        """
        Update an existing template.

        Args:
            template_id: Template ID
            name: New name
            content: New content
            description: New description
            category: New category
            is_public: New public status

        Returns:
            Updated WikiTemplate instance

        Example:
            >>> template = service.update_template(1, name="New Name")
        """
        try:
            template = self.get_template(template_id)
            if not template:
                return None

            if name is not None:
                template.name = name
            if content is not None:
                template.content = content
                # Re-extract variables
                template.variables = self._extract_variables(content)
            if description is not None:
                template.description = description
            if category is not None:
                template.category = category
            if is_public is not None:
                template.is_public = is_public

            template.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(template)

            logger.info(f"Updated template: {template_id}")
            return template

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating template: {str(e)}")
            return None

    def delete_template(self, template_id: int) -> bool:
        """
        Delete a template.

        Args:
            template_id: Template ID

        Returns:
            True if successful

        Example:
            >>> success = service.delete_template(5)
        """
        try:
            template = self.get_template(template_id)
            if not template:
                return False

            # Don't delete system templates
            if template.is_system:
                logger.warning(f"Cannot delete system template: {template_id}")
                return False

            self.db.delete(template)
            self.db.commit()

            logger.info(f"Deleted template: {template_id}")
            return True

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting template: {str(e)}")
            return False

    def install_builtin_templates(self, overwrite: bool = False) -> int:
        """
        Install built-in templates to database.

        Args:
            overwrite: Overwrite existing templates

        Returns:
            Number of templates installed

        Example:
            >>> count = service.install_builtin_templates()
            >>> print(f"Installed {count} templates")
        """
        try:
            installed = 0

            for key, template_def in self.BUILTIN_TEMPLATES.items():
                existing = self.get_template_by_name(template_def['name'])

                if existing and not overwrite:
                    logger.debug(f"Template '{template_def['name']}' already exists")
                    continue

                if existing and overwrite:
                    # Update existing
                    self.update_template(
                        existing.id,
                        content=template_def['content'],
                        category=template_def['category']
                    )
                    installed += 1
                else:
                    # Create new
                    self.create_template(
                        name=template_def['name'],
                        content=template_def['content'],
                        category=template_def['category'],
                        variables=template_def['variables'],
                        is_public=True,
                        created_by=1
                    )
                    # Mark as system template
                    template = self.get_template_by_name(template_def['name'])
                    if template:
                        template.is_system = True
                        self.db.commit()
                    installed += 1

            logger.info(f"Installed {installed} built-in templates")
            return installed

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error installing built-in templates: {str(e)}")
            return 0

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _extract_variables(self, content: str) -> List[str]:
        """Extract variable names from template content."""
        # Find all {{variable}} patterns
        pattern = r'\{\{(\w+)\}\}'
        matches = re.findall(pattern, content)

        # Return unique variables
        return list(set(matches))
