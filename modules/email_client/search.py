"""
Email Search and Filtering

Advanced search and filtering capabilities for emails.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class SearchFilter:
    """Search filter criteria."""
    filter_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""

    # Text searches
    query: Optional[str] = None  # Full-text search
    subject_contains: Optional[str] = None
    body_contains: Optional[str] = None

    # Sender/Recipient filters
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    cc_address: Optional[str] = None

    # Date filters
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

    # Status filters
    is_read: Optional[bool] = None
    is_starred: Optional[bool] = None
    is_draft: Optional[bool] = None
    has_attachments: Optional[bool] = None

    # Folder/Label filters
    folder: Optional[str] = None
    labels: Set[str] = field(default_factory=set)

    # Size filters
    min_size_bytes: Optional[int] = None
    max_size_bytes: Optional[int] = None

    # AI filters
    min_priority_score: Optional[float] = None
    category: Optional[str] = None

    # Save filter
    is_saved: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SmartFolder:
    """Smart folder (saved search)."""
    folder_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    filter: SearchFilter = field(default_factory=SearchFilter)
    color: str = "#0066cc"
    icon: str = "folder"
    auto_refresh: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


class EmailSearch:
    """
    Email search and filtering engine.

    Provides full-text search, advanced filtering, and smart folders.
    """

    def __init__(self, db_connection: Optional[Any] = None):
        """
        Initialize search engine.

        Args:
            db_connection: Database connection for indexing
        """
        self.db_connection = db_connection
        self.saved_filters: Dict[str, SearchFilter] = {}
        self.smart_folders: Dict[str, SmartFolder] = {}
        self._initialize_default_smart_folders()

    def _initialize_default_smart_folders(self) -> None:
        """Create default smart folders."""
        # Unread
        self.smart_folders['unread'] = SmartFolder(
            folder_id='unread',
            name='Unread',
            filter=SearchFilter(is_read=False),
            color='#ff6b6b',
            icon='envelope'
        )

        # Starred
        self.smart_folders['starred'] = SmartFolder(
            folder_id='starred',
            name='Starred',
            filter=SearchFilter(is_starred=True),
            color='#ffd700',
            icon='star'
        )

        # With Attachments
        self.smart_folders['attachments'] = SmartFolder(
            folder_id='attachments',
            name='With Attachments',
            filter=SearchFilter(has_attachments=True),
            color='#4ecdc4',
            icon='paperclip'
        )

        # Today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        self.smart_folders['today'] = SmartFolder(
            folder_id='today',
            name='Today',
            filter=SearchFilter(date_from=today_start),
            color='#95e1d3',
            icon='calendar'
        )

        # This Week
        week_start = today_start - timedelta(days=today_start.weekday())
        self.smart_folders['week'] = SmartFolder(
            folder_id='week',
            name='This Week',
            filter=SearchFilter(date_from=week_start),
            color='#a8e6cf',
            icon='calendar-week'
        )

    async def search(
        self,
        query: Optional[str] = None,
        filter: Optional[SearchFilter] = None,
        account_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search for emails.

        Args:
            query: Full-text search query
            filter: Search filter
            account_id: Specific account to search
            limit: Maximum results

        Returns:
            List[Dict]: Matching messages
        """
        # In production, this would query the database
        # For now, return placeholder

        messages = []

        # TODO: Implement database query
        # This would use full-text search indices for performance

        logger.info(f"Search query: {query}, filter: {filter}")

        return messages

    def apply_filter(
        self,
        messages: List[Dict[str, Any]],
        filter: SearchFilter
    ) -> List[Dict[str, Any]]:
        """
        Apply filter to a list of messages.

        Args:
            messages: List of messages
            filter: Filter to apply

        Returns:
            List[Dict]: Filtered messages
        """
        filtered = []

        for msg in messages:
            if self._matches_filter(msg, filter):
                filtered.append(msg)

        return filtered

    def _matches_filter(self, message: Dict[str, Any], filter: SearchFilter) -> bool:
        """Check if a message matches filter criteria."""
        # Text searches
        if filter.query:
            if not self._full_text_match(message, filter.query):
                return False

        if filter.subject_contains:
            subject = message.get('subject', '').lower()
            if filter.subject_contains.lower() not in subject:
                return False

        if filter.body_contains:
            body = (message.get('body_text', '') + message.get('body_html', '')).lower()
            if filter.body_contains.lower() not in body:
                return False

        # Sender/Recipient filters
        if filter.from_address:
            if filter.from_address.lower() not in message.get('from_address', '').lower():
                return False

        if filter.to_address:
            to_addrs = [addr.lower() for addr in message.get('to_addresses', [])]
            if not any(filter.to_address.lower() in addr for addr in to_addrs):
                return False

        # Date filters
        msg_date = message.get('date')
        if filter.date_from and msg_date:
            if msg_date < filter.date_from:
                return False

        if filter.date_to and msg_date:
            if msg_date > filter.date_to:
                return False

        # Status filters
        if filter.is_read is not None:
            if message.get('is_read') != filter.is_read:
                return False

        if filter.is_starred is not None:
            if message.get('is_starred') != filter.is_starred:
                return False

        if filter.is_draft is not None:
            if message.get('is_draft') != filter.is_draft:
                return False

        if filter.has_attachments is not None:
            if message.get('has_attachments') != filter.has_attachments:
                return False

        # Folder/Label filters
        if filter.folder:
            if message.get('folder') != filter.folder:
                return False

        if filter.labels:
            msg_labels = set(message.get('labels', []))
            if not filter.labels.intersection(msg_labels):
                return False

        # Size filters
        msg_size = message.get('size_bytes', 0)
        if filter.min_size_bytes and msg_size < filter.min_size_bytes:
            return False

        if filter.max_size_bytes and msg_size > filter.max_size_bytes:
            return False

        # AI filters
        if filter.min_priority_score is not None:
            priority = message.get('ai_priority_score')
            if priority is None or priority < filter.min_priority_score:
                return False

        if filter.category:
            if message.get('ai_category') != filter.category:
                return False

        return True

    def _full_text_match(self, message: Dict[str, Any], query: str) -> bool:
        """Perform full-text search on message."""
        query = query.lower()

        # Search in subject
        if query in message.get('subject', '').lower():
            return True

        # Search in body
        body_text = (
            message.get('body_text', '') +
            message.get('body_html', '')
        ).lower()

        if query in body_text:
            return True

        # Search in from/to
        if query in message.get('from_address', '').lower():
            return True

        for addr in message.get('to_addresses', []):
            if query in addr.lower():
                return True

        return False

    def save_filter(self, filter: SearchFilter) -> str:
        """
        Save a search filter.

        Args:
            filter: Filter to save

        Returns:
            str: Filter ID
        """
        filter.is_saved = True
        self.saved_filters[filter.filter_id] = filter
        logger.info(f"Saved filter: {filter.name}")
        return filter.filter_id

    def delete_filter(self, filter_id: str) -> bool:
        """Delete a saved filter."""
        if filter_id in self.saved_filters:
            del self.saved_filters[filter_id]
            return True
        return False

    def list_saved_filters(self) -> List[SearchFilter]:
        """List all saved filters."""
        return list(self.saved_filters.values())

    def create_smart_folder(self, smart_folder: SmartFolder) -> str:
        """
        Create a smart folder.

        Args:
            smart_folder: Smart folder configuration

        Returns:
            str: Folder ID
        """
        self.smart_folders[smart_folder.folder_id] = smart_folder
        logger.info(f"Created smart folder: {smart_folder.name}")
        return smart_folder.folder_id

    def delete_smart_folder(self, folder_id: str) -> bool:
        """Delete a smart folder."""
        # Don't delete default folders
        if folder_id in ['unread', 'starred', 'attachments', 'today', 'week']:
            return False

        if folder_id in self.smart_folders:
            del self.smart_folders[folder_id]
            return True
        return False

    def list_smart_folders(self) -> List[SmartFolder]:
        """List all smart folders."""
        return list(self.smart_folders.values())

    def get_smart_folder_messages(
        self,
        folder_id: str,
        messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Get messages for a smart folder.

        Args:
            folder_id: Smart folder ID
            messages: All messages to filter

        Returns:
            List[Dict]: Matching messages
        """
        smart_folder = self.smart_folders.get(folder_id)
        if not smart_folder:
            return []

        return self.apply_filter(messages, smart_folder.filter)

    def search_by_sender(
        self,
        messages: List[Dict[str, Any]],
        sender: str
    ) -> List[Dict[str, Any]]:
        """Search messages by sender."""
        filter = SearchFilter(from_address=sender)
        return self.apply_filter(messages, filter)

    def search_by_date_range(
        self,
        messages: List[Dict[str, Any]],
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Search messages by date range."""
        filter = SearchFilter(date_from=start_date, date_to=end_date)
        return self.apply_filter(messages, filter)

    def search_unread(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get unread messages."""
        filter = SearchFilter(is_read=False)
        return self.apply_filter(messages, filter)

    def search_starred(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get starred messages."""
        filter = SearchFilter(is_starred=True)
        return self.apply_filter(messages, filter)

    def search_with_attachments(
        self,
        messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Get messages with attachments."""
        filter = SearchFilter(has_attachments=True)
        return self.apply_filter(messages, filter)

    def advanced_search(
        self,
        messages: List[Dict[str, Any]],
        **criteria
    ) -> List[Dict[str, Any]]:
        """
        Advanced search with multiple criteria.

        Args:
            messages: Messages to search
            **criteria: Search criteria as keyword arguments

        Returns:
            List[Dict]: Matching messages
        """
        filter = SearchFilter(**criteria)
        return self.apply_filter(messages, filter)

    def highlight_matches(self, text: str, query: str) -> str:
        """
        Highlight search matches in text.

        Args:
            text: Text to highlight
            query: Search query

        Returns:
            str: Text with HTML highlighting
        """
        if not query:
            return text

        # Escape HTML in query
        query = re.escape(query)

        # Case-insensitive highlighting
        pattern = re.compile(f'({query})', re.IGNORECASE)
        highlighted = pattern.sub(r'<mark>\1</mark>', text)

        return highlighted

    def get_search_suggestions(self, partial_query: str) -> List[str]:
        """
        Get search suggestions based on partial query.

        Args:
            partial_query: Partial search query

        Returns:
            List[str]: Suggestions
        """
        suggestions = []

        # Common search operators
        operators = [
            "from:",
            "to:",
            "subject:",
            "has:attachment",
            "is:unread",
            "is:starred",
            "is:important",
            "before:",
            "after:",
            "larger:",
            "smaller:"
        ]

        for op in operators:
            if op.startswith(partial_query.lower()):
                suggestions.append(op)

        return suggestions

    def parse_search_query(self, query: str) -> SearchFilter:
        """
        Parse search query into filter.

        Supports operators like:
        - from:sender@example.com
        - to:recipient@example.com
        - subject:meeting
        - has:attachment
        - is:unread

        Args:
            query: Search query string

        Returns:
            SearchFilter: Parsed filter
        """
        filter = SearchFilter()

        # Extract operators
        parts = query.split()
        text_parts = []

        for part in parts:
            if ':' in part:
                operator, value = part.split(':', 1)
                operator = operator.lower()

                if operator == 'from':
                    filter.from_address = value
                elif operator == 'to':
                    filter.to_address = value
                elif operator == 'subject':
                    filter.subject_contains = value
                elif operator == 'has' and value == 'attachment':
                    filter.has_attachments = True
                elif operator == 'is':
                    if value == 'unread':
                        filter.is_read = False
                    elif value == 'starred':
                        filter.is_starred = True
                    elif value == 'draft':
                        filter.is_draft = True
            else:
                text_parts.append(part)

        # Remaining parts are full-text query
        if text_parts:
            filter.query = ' '.join(text_parts)

        return filter
