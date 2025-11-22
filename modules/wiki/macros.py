"""
Wiki Macros Service

Dynamic content generation for the NEXUS Wiki System including:
- Built-in macros (TOC, page lists, queries, charts)
- Custom macro execution
- Embedded widgets and plugins
- Macro parameter parsing and validation
- Safe macro execution environment

Author: NEXUS Platform Team
"""

import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict
from sqlalchemy import and_, or_, func, desc, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.utils import get_logger
from modules.wiki.models import WikiPage, WikiMacro, WikiCategory, WikiTag
from modules.wiki.wiki_types import MacroType, PageStatus

logger = get_logger(__name__)


class MacroService:
    """Manages dynamic content macros and embedded widgets."""

    # Macro pattern: {{macro_name:param1=value1,param2=value2}}
    MACRO_PATTERN = re.compile(r'\{\{(\w+)(?::([^}]+))?\}\}')

    def __init__(self, db: Session):
        """
        Initialize MacroService.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self._builtin_macros: Dict[str, Callable] = {
            'toc': self._macro_toc,
            'page_list': self._macro_page_list,
            'recent_pages': self._macro_recent_pages,
            'page_count': self._macro_page_count,
            'category_pages': self._macro_category_pages,
            'tag_list': self._macro_tag_list,
            'breadcrumbs': self._macro_breadcrumbs,
            'children': self._macro_children,
            'include': self._macro_include,
            'search': self._macro_search,
            'date': self._macro_date,
            'user': self._macro_user,
            'stats': self._macro_stats,
        }

    def process_content(
        self,
        content: str,
        page_id: Optional[int] = None,
        context: Optional[Dict] = None
    ) -> str:
        """
        Process content and expand all macros.

        Args:
            content: Content with macro placeholders
            page_id: Current page ID for context
            context: Additional context data

        Returns:
            Content with macros expanded

        Example:
            >>> service = MacroService(db)
            >>> processed = service.process_content(
            ...     "{{toc}} \\n\\n {{recent_pages:limit=5}}",
            ...     page_id=123
            ... )
        """
        try:
            context = context or {}
            context['page_id'] = page_id

            # Find and replace all macros
            def replace_macro(match):
                macro_name = match.group(1)
                params_str = match.group(2) or ''
                params = self._parse_params(params_str)

                try:
                    result = self.execute_macro(macro_name, params, context)
                    return result or ''
                except Exception as e:
                    logger.error(f"Error executing macro '{macro_name}': {str(e)}")
                    return f"[Error in macro: {macro_name}]"

            processed = self.MACRO_PATTERN.sub(replace_macro, content)
            return processed

        except Exception as e:
            logger.error(f"Error processing macros: {str(e)}")
            return content

    def execute_macro(
        self,
        macro_name: str,
        params: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> str:
        """
        Execute a specific macro.

        Args:
            macro_name: Name of the macro
            params: Macro parameters
            context: Execution context

        Returns:
            Macro output

        Example:
            >>> output = service.execute_macro(
            ...     'page_list',
            ...     {'category': 'docs', 'limit': 10}
            ... )
        """
        try:
            context = context or {}

            # Check built-in macros first
            if macro_name in self._builtin_macros:
                return self._builtin_macros[macro_name](params, context)

            # Check custom macros
            custom_macro = self.db.query(WikiMacro).filter(
                WikiMacro.name == macro_name,
                WikiMacro.is_active == True
            ).first()

            if custom_macro:
                return self._execute_custom_macro(custom_macro, params, context)

            logger.warning(f"Macro '{macro_name}' not found")
            return f"[Unknown macro: {macro_name}]"

        except Exception as e:
            logger.error(f"Error executing macro '{macro_name}': {str(e)}")
            return f"[Error: {str(e)}]"

    # ========================================================================
    # CUSTOM MACRO MANAGEMENT
    # ========================================================================

    def create_macro(
        self,
        name: str,
        code: str,
        description: Optional[str] = None,
        parameters: Optional[Dict] = None,
        is_active: bool = True,
        created_by: int = 1
    ) -> Optional[WikiMacro]:
        """
        Create a custom macro.

        Args:
            name: Macro name
            code: Macro code/template
            description: Macro description
            parameters: Parameter definitions
            is_active: Whether macro is active
            created_by: Creator user ID

        Returns:
            Created WikiMacro instance

        Example:
            >>> macro = service.create_macro(
            ...     name='greeting',
            ...     code='Hello, {{name}}!',
            ...     parameters={'name': {'type': 'string', 'required': True}}
            ... )
        """
        try:
            macro = WikiMacro(
                name=name,
                code=code,
                description=description,
                parameters=parameters or {},
                is_active=is_active,
                created_by=created_by
            )

            self.db.add(macro)
            self.db.commit()
            self.db.refresh(macro)

            logger.info(f"Created macro: '{macro.name}'")
            return macro

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating macro: {str(e)}")
            return None

    def get_macro(self, macro_id: int) -> Optional[WikiMacro]:
        """Get a macro by ID."""
        try:
            return self.db.query(WikiMacro).filter(
                WikiMacro.id == macro_id
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting macro: {str(e)}")
            return None

    def list_macros(
        self,
        active_only: bool = True,
        include_system: bool = True
    ) -> List[WikiMacro]:
        """
        List available macros.

        Args:
            active_only: Only show active macros
            include_system: Include system macros

        Returns:
            List of WikiMacro instances

        Example:
            >>> macros = service.list_macros()
        """
        try:
            query = self.db.query(WikiMacro)

            if active_only:
                query = query.filter(WikiMacro.is_active == True)

            if not include_system:
                query = query.filter(WikiMacro.is_system == False)

            return query.order_by(WikiMacro.name).all()

        except SQLAlchemyError as e:
            logger.error(f"Error listing macros: {str(e)}")
            return []

    def update_macro(
        self,
        macro_id: int,
        code: Optional[str] = None,
        description: Optional[str] = None,
        parameters: Optional[Dict] = None,
        is_active: Optional[bool] = None
    ) -> Optional[WikiMacro]:
        """Update a macro."""
        try:
            macro = self.get_macro(macro_id)
            if not macro:
                return None

            if code is not None:
                macro.code = code
            if description is not None:
                macro.description = description
            if parameters is not None:
                macro.parameters = parameters
            if is_active is not None:
                macro.is_active = is_active

            macro.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(macro)

            return macro

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating macro: {str(e)}")
            return None

    def delete_macro(self, macro_id: int) -> bool:
        """Delete a macro."""
        try:
            macro = self.get_macro(macro_id)
            if not macro or macro.is_system:
                return False

            self.db.delete(macro)
            self.db.commit()
            return True

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting macro: {str(e)}")
            return False

    # ========================================================================
    # BUILT-IN MACROS
    # ========================================================================

    def _macro_toc(self, params: Dict, context: Dict) -> str:
        """Generate table of contents for current page."""
        page_id = context.get('page_id')
        if not page_id:
            return ""

        max_depth = int(params.get('depth', 6))
        min_level = int(params.get('min_level', 1))

        # Get page content and extract headings
        page = self.db.query(WikiPage).filter(WikiPage.id == page_id).first()
        if not page:
            return ""

        # Extract headings from markdown
        headings = []
        for line in page.content.split('\n'):
            match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if match:
                level = len(match.group(1))
                if min_level <= level <= max_depth:
                    title = match.group(2)
                    anchor = re.sub(r'[^\w\s-]', '', title.lower()).replace(' ', '-')
                    headings.append((level, title, anchor))

        if not headings:
            return ""

        # Build TOC HTML
        toc_lines = ['<div class="toc">', '<ul>']
        current_level = min_level

        for level, title, anchor in headings:
            while current_level < level:
                toc_lines.append('<ul>')
                current_level += 1
            while current_level > level:
                toc_lines.append('</ul>')
                current_level -= 1

            toc_lines.append(f'<li><a href="#{anchor}">{title}</a></li>')

        while current_level > min_level:
            toc_lines.append('</ul>')
            current_level -= 1

        toc_lines.extend(['</ul>', '</div>'])
        return '\n'.join(toc_lines)

    def _macro_page_list(self, params: Dict, context: Dict) -> str:
        """List pages with optional filtering."""
        category = params.get('category')
        tag = params.get('tag')
        limit = int(params.get('limit', 10))
        format_type = params.get('format', 'ul')  # 'ul', 'ol', 'table'

        query = self.db.query(WikiPage).filter(
            WikiPage.is_deleted == False,
            WikiPage.status == PageStatus.PUBLISHED
        )

        if category:
            cat = self.db.query(WikiCategory).filter(
                WikiCategory.slug == category
            ).first()
            if cat:
                query = query.filter(WikiPage.category_id == cat.id)

        if tag:
            tag_obj = self.db.query(WikiTag).filter(WikiTag.name == tag).first()
            if tag_obj:
                from modules.wiki.models import page_tags
                query = query.join(page_tags).filter(
                    page_tags.c.tag_id == tag_obj.id
                )

        pages = query.order_by(desc(WikiPage.updated_at)).limit(limit).all()

        if not pages:
            return ""

        # Format output
        if format_type == 'table':
            lines = ['| Page | Updated |', '|------|---------|']
            for page in pages:
                date = page.updated_at.strftime('%Y-%m-%d')
                lines.append(f'| [{page.title}]({page.full_path}) | {date} |')
            return '\n'.join(lines)
        else:
            tag_name = 'ol' if format_type == 'ol' else 'ul'
            lines = [f'<{tag_name}>']
            for page in pages:
                lines.append(f'<li><a href="{page.full_path}">{page.title}</a></li>')
            lines.append(f'</{tag_name}>')
            return '\n'.join(lines)

    def _macro_recent_pages(self, params: Dict, context: Dict) -> str:
        """Show recently updated pages."""
        limit = int(params.get('limit', 5))
        days = int(params.get('days', 30))

        cutoff = datetime.utcnow() - __import__('datetime').timedelta(days=days)

        pages = self.db.query(WikiPage).filter(
            WikiPage.is_deleted == False,
            WikiPage.status == PageStatus.PUBLISHED,
            WikiPage.updated_at >= cutoff
        ).order_by(desc(WikiPage.updated_at)).limit(limit).all()

        if not pages:
            return "No recent pages."

        lines = ['<ul class="recent-pages">']
        for page in pages:
            date = page.updated_at.strftime('%Y-%m-%d')
            lines.append(
                f'<li><a href="{page.full_path}">{page.title}</a> '
                f'<span class="date">({date})</span></li>'
            )
        lines.append('</ul>')
        return '\n'.join(lines)

    def _macro_page_count(self, params: Dict, context: Dict) -> str:
        """Display total page count."""
        category = params.get('category')
        status = params.get('status', 'published')

        query = self.db.query(func.count(WikiPage.id)).filter(
            WikiPage.is_deleted == False
        )

        if status == 'published':
            query = query.filter(WikiPage.status == PageStatus.PUBLISHED)

        if category:
            cat = self.db.query(WikiCategory).filter(
                WikiCategory.slug == category
            ).first()
            if cat:
                query = query.filter(WikiPage.category_id == cat.id)

        count = query.scalar()
        return str(count)

    def _macro_category_pages(self, params: Dict, context: Dict) -> str:
        """List pages in a category."""
        category = params.get('category')
        if not category:
            return "[Error: category parameter required]"

        cat = self.db.query(WikiCategory).filter(
            WikiCategory.slug == category
        ).first()

        if not cat:
            return f"[Category '{category}' not found]"

        return self._macro_page_list({'category': category, **params}, context)

    def _macro_tag_list(self, params: Dict, context: Dict) -> str:
        """Display tag cloud or list."""
        min_usage = int(params.get('min_usage', 1))
        limit = int(params.get('limit', 50))
        format_type = params.get('format', 'cloud')  # 'cloud' or 'list'

        tags = self.db.query(WikiTag).filter(
            WikiTag.usage_count >= min_usage
        ).order_by(desc(WikiTag.usage_count)).limit(limit).all()

        if not tags:
            return ""

        if format_type == 'cloud':
            # Simple tag cloud
            max_usage = max(t.usage_count for t in tags)
            min_usage_val = min(t.usage_count for t in tags)
            range_val = max_usage - min_usage_val or 1

            lines = ['<div class="tag-cloud">']
            for tag in tags:
                # Size from 1-5
                size = 1 + int(4 * (tag.usage_count - min_usage_val) / range_val)
                lines.append(
                    f'<span class="tag tag-size-{size}" '
                    f'style="color:{tag.color}">{tag.name}</span>'
                )
            lines.append('</div>')
            return '\n'.join(lines)
        else:
            lines = ['<ul class="tag-list">']
            for tag in tags:
                lines.append(
                    f'<li><span style="color:{tag.color}">{tag.name}</span> '
                    f'({tag.usage_count})</li>'
                )
            lines.append('</ul>')
            return '\n'.join(lines)

    def _macro_breadcrumbs(self, params: Dict, context: Dict) -> str:
        """Generate breadcrumb navigation."""
        page_id = context.get('page_id')
        if not page_id:
            return ""

        from modules.wiki.navigation import NavigationService
        nav_service = NavigationService(self.db)

        breadcrumbs = nav_service.get_breadcrumbs(page_id)

        if not breadcrumbs:
            return ""

        parts = []
        for item in breadcrumbs:
            if item.page_id == 0:
                parts.append(f'<a href="{item.url}">{item.title}</a>')
            else:
                parts.append(f'<a href="{item.url}">{item.title}</a>')

        return ' &gt; '.join(parts)

    def _macro_children(self, params: Dict, context: Dict) -> str:
        """List child pages of current or specified page."""
        page_id = params.get('page_id') or context.get('page_id')
        if not page_id:
            return ""

        children = self.db.query(WikiPage).filter(
            WikiPage.parent_page_id == page_id,
            WikiPage.is_deleted == False
        ).order_by(WikiPage.title).all()

        if not children:
            return ""

        lines = ['<ul class="child-pages">']
        for child in children:
            lines.append(f'<li><a href="{child.full_path}">{child.title}</a></li>')
        lines.append('</ul>')
        return '\n'.join(lines)

    def _macro_include(self, params: Dict, context: Dict) -> str:
        """Include content from another page."""
        page_slug = params.get('page')
        if not page_slug:
            return "[Error: page parameter required]"

        page = self.db.query(WikiPage).filter(
            WikiPage.slug == page_slug,
            WikiPage.is_deleted == False
        ).first()

        if not page:
            return f"[Page '{page_slug}' not found]"

        # Return first N characters to avoid infinite recursion
        max_chars = int(params.get('max_chars', 500))
        content = page.content[:max_chars]
        if len(page.content) > max_chars:
            content += "..."

        return content

    def _macro_search(self, params: Dict, context: Dict) -> str:
        """Embedded search results."""
        query_str = params.get('query', '')
        limit = int(params.get('limit', 5))

        if not query_str:
            return ""

        from modules.wiki.search import SearchService
        search_service = SearchService(self.db)

        results, _ = search_service.search(query_str, limit=limit)

        if not results:
            return f"No results for '{query_str}'"

        lines = ['<ul class="search-results">']
        for result in results:
            page = result['page']
            lines.append(f'<li><a href="{page.full_path}">{page.title}</a></li>')
        lines.append('</ul>')
        return '\n'.join(lines)

    def _macro_date(self, params: Dict, context: Dict) -> str:
        """Display current date/time."""
        format_str = params.get('format', '%Y-%m-%d')
        return datetime.utcnow().strftime(format_str)

    def _macro_user(self, params: Dict, context: Dict) -> str:
        """Display user information."""
        user_id = context.get('user_id')
        if not user_id:
            return "[User not logged in]"

        # In real implementation, fetch user data
        return f"User #{user_id}"

    def _macro_stats(self, params: Dict, context: Dict) -> str:
        """Display wiki statistics."""
        stat_type = params.get('type', 'overview')

        if stat_type == 'overview':
            total_pages = self.db.query(func.count(WikiPage.id)).filter(
                WikiPage.is_deleted == False
            ).scalar()

            total_categories = self.db.query(func.count(WikiCategory.id)).scalar()
            total_tags = self.db.query(func.count(WikiTag.id)).scalar()

            return (
                f'<div class="wiki-stats">'
                f'<p>Pages: {total_pages} | '
                f'Categories: {total_categories} | '
                f'Tags: {total_tags}</p>'
                f'</div>'
            )

        return ""

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _parse_params(self, params_str: str) -> Dict[str, Any]:
        """Parse macro parameter string."""
        params = {}

        if not params_str:
            return params

        # Split by commas, handle quoted values
        parts = re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', params_str)

        for part in parts:
            part = part.strip()
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"\'')

                # Try to convert to appropriate type
                if value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False
                elif value.isdigit():
                    value = int(value)

                params[key] = value

        return params

    def _execute_custom_macro(
        self,
        macro: WikiMacro,
        params: Dict,
        context: Dict
    ) -> str:
        """Execute a custom user-defined macro."""
        try:
            # Simple template substitution
            output = macro.code

            # Replace parameters
            for key, value in params.items():
                placeholder = f'{{{{{key}}}}}'
                output = output.replace(placeholder, str(value))

            # Replace context variables
            for key, value in context.items():
                placeholder = f'{{{{{key}}}}}'
                output = output.replace(placeholder, str(value))

            return output

        except Exception as e:
            logger.error(f"Error executing custom macro '{macro.name}': {str(e)}")
            return f"[Error in macro: {macro.name}]"
