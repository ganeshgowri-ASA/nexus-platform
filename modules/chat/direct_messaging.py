"""
Direct Messaging - Handles 1-on-1 conversations.

Manages direct message channels between two users, including
contact lists, favorites, blocking, and muting.
"""

import logging
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID, uuid4

from .models import (
    Channel, ChannelType, DirectMessageInfo, User, Message
)

logger = logging.getLogger(__name__)


class DirectMessaging:
    """
    Manages direct messaging functionality.

    Handles:
    - Creating/finding DM channels
    - Contact management
    - Blocking and muting users
    - Favorites
    - User search

    Example:
        >>> dm = DirectMessaging(engine)
        >>> channel = await dm.get_or_create_dm(user1_id, user2_id)
        >>> await dm.block_user(user_id, blocked_user_id)
    """

    def __init__(self, engine):
        """
        Initialize direct messaging.

        Args:
            engine: Reference to the ChatEngine
        """
        self.engine = engine
        self._dm_cache: Dict[frozenset, UUID] = {}  # {user_id_set: channel_id}
        self._blocked_users: Dict[UUID, set] = {}  # {user_id: set of blocked user_ids}
        self._favorites: Dict[UUID, set] = {}  # {user_id: set of favorite user_ids}
        logger.info("DirectMessaging initialized")

    async def get_or_create_dm(
        self,
        user1_id: UUID,
        user2_id: UUID
    ) -> Channel:
        """
        Get or create a direct message channel between two users.

        Args:
            user1_id: ID of first user
            user2_id: ID of second user

        Returns:
            DM Channel object

        Raises:
            ValueError: If user tries to DM themselves
        """
        if user1_id == user2_id:
            raise ValueError("Cannot create DM with yourself")

        # Check if DM already exists
        user_set = frozenset([user1_id, user2_id])

        if user_set in self._dm_cache:
            channel_id = self._dm_cache[user_set]
            channel = await self.engine.channel_manager.get_channel(channel_id)
            if channel:
                return channel

        # Create new DM channel
        channel = Channel(
            id=uuid4(),
            name=f"DM-{user1_id}-{user2_id}",  # Internal name
            channel_type=ChannelType.DIRECT,
            creator_id=user1_id,
            created_at=datetime.utcnow(),
            member_count=2
        )

        # Save channel
        self.engine.channel_manager._channel_cache[channel.id] = channel

        # Add both users as members
        await self.engine.channel_manager.add_member(channel.id, user1_id)
        await self.engine.channel_manager.add_member(channel.id, user2_id)

        # Cache the DM mapping
        self._dm_cache[user_set] = channel.id

        logger.info(f"DM channel {channel.id} created between {user1_id} and {user2_id}")
        return channel

    async def get_dm_info(
        self,
        user1_id: UUID,
        user2_id: UUID
    ) -> Optional[DirectMessageInfo]:
        """
        Get DM conversation information.

        Args:
            user1_id: ID of first user
            user2_id: ID of second user

        Returns:
            DirectMessageInfo object or None if no DM exists
        """
        user_set = frozenset([user1_id, user2_id])

        if user_set not in self._dm_cache:
            return None

        channel_id = self._dm_cache[user_set]
        channel = await self.engine.channel_manager.get_channel(channel_id)

        if not channel:
            return None

        # Get last message
        messages = await self.engine.message_manager.get_messages(
            channel_id=channel_id,
            limit=1
        )
        last_message = messages[0] if messages else None

        # Get unread count
        unread_count = await self.engine.message_manager.get_unread_count(
            channel_id=channel_id,
            user_id=user1_id
        )

        dm_info = DirectMessageInfo(
            id=channel.id,
            user1_id=user1_id,
            user2_id=user2_id,
            channel_id=channel_id,
            last_message=last_message,
            unread_count=unread_count,
            created_at=channel.created_at
        )

        return dm_info

    async def get_user_dms(self, user_id: UUID) -> List[DirectMessageInfo]:
        """
        Get all DM conversations for a user.

        Args:
            user_id: ID of the user

        Returns:
            List of DirectMessageInfo objects sorted by last message
        """
        dm_infos = []

        # Find all DMs involving this user
        for user_set, channel_id in self._dm_cache.items():
            if user_id in user_set:
                other_user_id = next(uid for uid in user_set if uid != user_id)
                dm_info = await self.get_dm_info(user_id, other_user_id)
                if dm_info:
                    dm_infos.append(dm_info)

        # Sort by last message time
        dm_infos.sort(
            key=lambda x: x.last_message.created_at if x.last_message else x.created_at,
            reverse=True
        )

        return dm_infos

    async def block_user(
        self,
        user_id: UUID,
        blocked_user_id: UUID
    ) -> bool:
        """
        Block a user.

        Args:
            user_id: ID of the user doing the blocking
            blocked_user_id: ID of the user to block

        Returns:
            True if successful
        """
        if user_id == blocked_user_id:
            raise ValueError("Cannot block yourself")

        if user_id not in self._blocked_users:
            self._blocked_users[user_id] = set()

        self._blocked_users[user_id].add(blocked_user_id)

        # In production, save to database
        # UPDATE users SET blocked_users = ... WHERE id = user_id

        logger.info(f"User {user_id} blocked user {blocked_user_id}")
        return True

    async def unblock_user(
        self,
        user_id: UUID,
        blocked_user_id: UUID
    ) -> bool:
        """
        Unblock a user.

        Args:
            user_id: ID of the user doing the unblocking
            blocked_user_id: ID of the user to unblock

        Returns:
            True if successful
        """
        if user_id in self._blocked_users:
            self._blocked_users[user_id].discard(blocked_user_id)

        logger.info(f"User {user_id} unblocked user {blocked_user_id}")
        return True

    async def is_blocked(
        self,
        user_id: UUID,
        other_user_id: UUID
    ) -> bool:
        """
        Check if a user is blocked.

        Args:
            user_id: ID of the user
            other_user_id: ID of the other user

        Returns:
            True if other_user is blocked by user
        """
        blocked = self._blocked_users.get(user_id, set())
        return other_user_id in blocked

    async def add_favorite(
        self,
        user_id: UUID,
        favorite_user_id: UUID
    ) -> bool:
        """
        Add a user to favorites.

        Args:
            user_id: ID of the user
            favorite_user_id: ID of the user to favorite

        Returns:
            True if successful
        """
        if user_id not in self._favorites:
            self._favorites[user_id] = set()

        self._favorites[user_id].add(favorite_user_id)

        logger.info(f"User {user_id} favorited user {favorite_user_id}")
        return True

    async def remove_favorite(
        self,
        user_id: UUID,
        favorite_user_id: UUID
    ) -> bool:
        """
        Remove a user from favorites.

        Args:
            user_id: ID of the user
            favorite_user_id: ID of the user to unfavorite

        Returns:
            True if successful
        """
        if user_id in self._favorites:
            self._favorites[user_id].discard(favorite_user_id)

        return True

    async def get_favorites(self, user_id: UUID) -> List[UUID]:
        """
        Get user's favorite contacts.

        Args:
            user_id: ID of the user

        Returns:
            List of favorite user IDs
        """
        return list(self._favorites.get(user_id, set()))

    async def get_contacts(self, user_id: UUID) -> List[UUID]:
        """
        Get all contacts (users with DM conversations).

        Args:
            user_id: ID of the user

        Returns:
            List of contact user IDs
        """
        contacts = set()

        for user_set in self._dm_cache.keys():
            if user_id in user_set:
                other_user = next(uid for uid in user_set if uid != user_id)
                contacts.add(other_user)

        return list(contacts)

    async def search_users(
        self,
        user_id: UUID,
        query: str,
        limit: int = 20
    ) -> List[User]:
        """
        Search for users to message.

        Args:
            user_id: ID of the searching user
            query: Search query (username, display name, email)
            limit: Maximum results

        Returns:
            List of User objects
        """
        # In production, query from users table
        # SELECT * FROM users
        # WHERE (username ILIKE %query% OR display_name ILIKE %query% OR email ILIKE %query%)
        # AND id != user_id
        # AND is_active = TRUE
        # LIMIT limit

        # Mock implementation
        users = []

        logger.debug(f"User {user_id} searched for: {query}")
        return users[:limit]

    async def mute_dm(
        self,
        user_id: UUID,
        other_user_id: UUID,
        muted: bool = True
    ) -> bool:
        """
        Mute or unmute a DM conversation.

        Args:
            user_id: ID of the user
            other_user_id: ID of the other user
            muted: True to mute, False to unmute

        Returns:
            True if successful
        """
        # Get DM channel
        user_set = frozenset([user_id, other_user_id])

        if user_set not in self._dm_cache:
            raise ValueError("No DM conversation found")

        channel_id = self._dm_cache[user_set]

        # Update channel member settings
        # In production:
        # UPDATE channel_members
        # SET is_muted = muted
        # WHERE channel_id = channel_id AND user_id = user_id

        logger.info(f"User {user_id} {'muted' if muted else 'unmuted'} DM with {other_user_id}")
        return True

    async def mark_dm_as_read(
        self,
        user_id: UUID,
        other_user_id: UUID
    ) -> bool:
        """
        Mark all messages in a DM as read.

        Args:
            user_id: ID of the user
            other_user_id: ID of the other user

        Returns:
            True if successful
        """
        # Get DM channel
        user_set = frozenset([user_id, other_user_id])

        if user_set not in self._dm_cache:
            return False

        channel_id = self._dm_cache[user_set]

        await self.engine.message_manager.mark_as_read(channel_id, user_id)

        return True

    async def get_unread_dm_count(self, user_id: UUID) -> int:
        """
        Get total count of unread DMs for a user.

        Args:
            user_id: ID of the user

        Returns:
            Count of unread DMs
        """
        total = 0

        for user_set, channel_id in self._dm_cache.items():
            if user_id in user_set:
                count = await self.engine.message_manager.get_unread_count(
                    channel_id=channel_id,
                    user_id=user_id
                )
                total += count

        return total

    async def delete_dm_conversation(
        self,
        user_id: UUID,
        other_user_id: UUID,
        for_both: bool = False
    ) -> bool:
        """
        Delete a DM conversation.

        Args:
            user_id: ID of the user
            other_user_id: ID of the other user
            for_both: If True, delete for both users; otherwise just hide for user

        Returns:
            True if successful
        """
        user_set = frozenset([user_id, other_user_id])

        if user_set not in self._dm_cache:
            return False

        channel_id = self._dm_cache[user_set]

        if for_both:
            # Delete channel and all messages
            await self.engine.channel_manager.delete_channel(channel_id, user_id)
            self._dm_cache.pop(user_set, None)
        else:
            # Just remove user from channel (hide conversation)
            await self.engine.channel_manager.remove_member(channel_id, user_id)

        logger.info(f"DM conversation deleted between {user_id} and {other_user_id}")
        return True
