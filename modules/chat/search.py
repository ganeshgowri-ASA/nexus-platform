"""
Search - Full-text search for messages and content.

Provides powerful search capabilities including full-text search,
filtering, saved searches, and search suggestions.
"""

import logging
import re
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

from .models import Message, SearchRequest, MessageType, User

logger = logging.getLogger(__name__)


class Search:
    """
    Manages search functionality.

    Handles:
    - Full-text message search
    - Advanced filtering (user, type, date)
    - Search in specific channels
    - Saved searches
    - Search history
    - Search suggestions

    Example:
        >>> search = Search(engine)
        >>> results = await search.search_messages("hello world", channel_id)
        >>> await search.save_search(user_id, "My Search", query)
    """

    def __init__(self, engine):
        """
        Initialize search manager.

        Args:
            engine: Reference to the ChatEngine
        """
        self.engine = engine
        self._saved_searches: Dict[UUID, List[Dict]] = {}  # user_id -> saved searches
        self._search_history: Dict[UUID, List[str]] = {}  # user_id -> recent queries
        logger.info("Search initialized")

    async def search_messages(
        self,
        query: str,
        user_id: Optional[UUID] = None,
        channel_id: Optional[UUID] = None,
        from_user_id: Optional[UUID] = None,
        message_type: Optional[MessageType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Message]:
        """
        Search for messages.

        Args:
            query: Search query string
            user_id: User performing the search (for permissions)
            channel_id: Limit search to specific channel
            from_user_id: Filter by message author
            message_type: Filter by message type
            start_date: Filter messages after this date
            end_date: Filter messages before this date
            limit: Maximum results
            offset: Number of results to skip

        Returns:
            List of matching Message objects
        """
        # Record search in history
        if user_id and query:
            await self._add_to_history(user_id, query)

        # Get all messages (in production, this would be a database query)
        all_messages = list(self.engine.message_manager._message_cache.values())

        # Apply filters
        filtered = []

        for msg in all_messages:
            # Skip deleted messages
            if msg.deleted_at:
                continue

            # Channel filter
            if channel_id and msg.channel_id != channel_id:
                continue

            # User filter
            if from_user_id and msg.user_id != from_user_id:
                continue

            # Message type filter
            if message_type and msg.message_type != message_type:
                continue

            # Date filters
            if start_date and msg.created_at < start_date:
                continue

            if end_date and msg.created_at > end_date:
                continue

            # Text search
            if query:
                if not self._matches_query(msg.content, query):
                    continue

            # Check permissions
            if user_id:
                # In production: check if user can access this channel
                pass

            filtered.append(msg)

        # Sort by relevance (in production, use full-text search ranking)
        # For now, sort by date descending
        filtered.sort(key=lambda x: x.created_at, reverse=True)

        # Apply pagination
        results = filtered[offset:offset + limit]

        logger.info(f"Search for '{query}' returned {len(results)} results")
        return results

    async def search_in_channel(
        self,
        channel_id: UUID,
        query: str,
        limit: int = 50
    ) -> List[Message]:
        """
        Search messages in a specific channel.

        Args:
            channel_id: ID of the channel
            query: Search query
            limit: Maximum results

        Returns:
            List of matching Message objects
        """
        return await self.search_messages(
            query=query,
            channel_id=channel_id,
            limit=limit
        )

    async def search_by_user(
        self,
        user_id: UUID,
        query: Optional[str] = None,
        limit: int = 50
    ) -> List[Message]:
        """
        Search messages from a specific user.

        Args:
            user_id: ID of the user
            query: Optional search query
            limit: Maximum results

        Returns:
            List of matching Message objects
        """
        return await self.search_messages(
            query=query or "",
            from_user_id=user_id,
            limit=limit
        )

    async def search_with_attachments(
        self,
        query: Optional[str] = None,
        channel_id: Optional[UUID] = None,
        limit: int = 50
    ) -> List[Message]:
        """
        Search messages with file attachments.

        Args:
            query: Optional search query
            channel_id: Optional channel filter
            limit: Maximum results

        Returns:
            List of Message objects with attachments
        """
        results = await self.search_messages(
            query=query or "",
            channel_id=channel_id,
            limit=limit * 2  # Get more to filter
        )

        # Filter messages with attachments
        with_attachments = [
            msg for msg in results
            if msg.attachments and len(msg.attachments) > 0
        ]

        return with_attachments[:limit]

    async def advanced_search(
        self,
        request: SearchRequest
    ) -> List[Message]:
        """
        Perform advanced search with full filtering.

        Args:
            request: SearchRequest object with all filters

        Returns:
            List of matching Message objects
        """
        return await self.search_messages(
            query=request.query,
            channel_id=request.channel_id,
            from_user_id=request.user_id,
            message_type=request.message_type,
            start_date=request.start_date,
            end_date=request.end_date,
            limit=request.limit,
            offset=request.offset
        )

    async def save_search(
        self,
        user_id: UUID,
        name: str,
        search_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Save a search for quick access.

        Args:
            user_id: ID of the user
            name: Name for the saved search
            search_params: Search parameters to save

        Returns:
            Saved search dictionary
        """
        saved_search = {
            "id": str(uuid4()),
            "name": name,
            "params": search_params,
            "created_at": datetime.utcnow().isoformat()
        }

        if user_id not in self._saved_searches:
            self._saved_searches[user_id] = []

        self._saved_searches[user_id].append(saved_search)

        # In production: save to database
        # INSERT INTO saved_searches ...

        logger.info(f"Search saved for user {user_id}: {name}")
        return saved_search

    async def get_saved_searches(self, user_id: UUID) -> List[Dict[str, Any]]:
        """
        Get user's saved searches.

        Args:
            user_id: ID of the user

        Returns:
            List of saved search dictionaries
        """
        return self._saved_searches.get(user_id, []).copy()

    async def delete_saved_search(
        self,
        user_id: UUID,
        search_id: str
    ) -> bool:
        """
        Delete a saved search.

        Args:
            user_id: ID of the user
            search_id: ID of the saved search

        Returns:
            True if deleted
        """
        if user_id in self._saved_searches:
            self._saved_searches[user_id] = [
                s for s in self._saved_searches[user_id]
                if s["id"] != search_id
            ]
            return True

        return False

    async def get_search_history(
        self,
        user_id: UUID,
        limit: int = 20
    ) -> List[str]:
        """
        Get user's recent search queries.

        Args:
            user_id: ID of the user
            limit: Maximum queries to return

        Returns:
            List of recent query strings
        """
        history = self._search_history.get(user_id, [])
        return history[:limit]

    async def clear_search_history(self, user_id: UUID) -> bool:
        """
        Clear user's search history.

        Args:
            user_id: ID of the user

        Returns:
            True if cleared
        """
        self._search_history[user_id] = []
        return True

    async def get_search_suggestions(
        self,
        query: str,
        user_id: UUID,
        limit: int = 5
    ) -> List[str]:
        """
        Get search suggestions based on partial query.

        Args:
            query: Partial search query
            user_id: ID of the user
            limit: Maximum suggestions

        Returns:
            List of suggested queries
        """
        suggestions = []

        # Add from search history
        history = self._search_history.get(user_id, [])
        query_lower = query.lower()

        for hist_query in history:
            if query_lower in hist_query.lower() and hist_query not in suggestions:
                suggestions.append(hist_query)

            if len(suggestions) >= limit:
                break

        # In production: also suggest popular searches, channels, users

        return suggestions

    async def search_users(
        self,
        query: str,
        limit: int = 20
    ) -> List[User]:
        """
        Search for users by username, display name, or email.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching User objects
        """
        # In production: query users table
        # SELECT * FROM users
        # WHERE username ILIKE %query%
        # OR display_name ILIKE %query%
        # OR email ILIKE %query%
        # LIMIT limit

        users = []  # Mock

        logger.debug(f"User search for '{query}' returned {len(users)} results")
        return users[:limit]

    async def search_channels(
        self,
        query: str,
        user_id: Optional[UUID] = None,
        limit: int = 20
    ) -> List:
        """
        Search for channels.

        Args:
            query: Search query
            user_id: Optional user ID for permission filtering
            limit: Maximum results

        Returns:
            List of matching Channel objects
        """
        from .models import Channel

        results = await self.engine.channel_manager.search_channels(
            query=query,
            user_id=user_id
        )

        return results[:limit]

    async def get_popular_searches(
        self,
        channel_id: Optional[UUID] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get most popular search queries.

        Args:
            channel_id: Optional channel filter
            limit: Maximum results

        Returns:
            List of dictionaries with query and count
        """
        # In production: aggregate from search logs
        # SELECT query, COUNT(*) as count
        # FROM search_logs
        # WHERE channel_id = channel_id (if provided)
        # GROUP BY query
        # ORDER BY count DESC
        # LIMIT limit

        popular = []  # Mock

        return popular

    # Private helper methods
    def _matches_query(self, text: str, query: str) -> bool:
        """
        Check if text matches search query.

        Args:
            text: Text to search in
            query: Search query

        Returns:
            True if matches
        """
        if not text or not query:
            return False

        # Simple case-insensitive contains match
        # In production: use full-text search with ranking
        text_lower = text.lower()
        query_lower = query.lower()

        # Support phrase search with quotes
        if query.startswith('"') and query.endswith('"'):
            phrase = query[1:-1].lower()
            return phrase in text_lower

        # Support multiple terms (AND logic)
        terms = query_lower.split()
        return all(term in text_lower for term in terms)

    async def _add_to_history(self, user_id: UUID, query: str) -> None:
        """Add query to user's search history."""
        if user_id not in self._search_history:
            self._search_history[user_id] = []

        history = self._search_history[user_id]

        # Remove if already exists
        if query in history:
            history.remove(query)

        # Add to front
        history.insert(0, query)

        # Keep only last 100
        self._search_history[user_id] = history[:100]

        # In production: save to database
