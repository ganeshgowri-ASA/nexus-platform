"""
Channel Manager - Handles channels, rooms, and workspaces.

Manages channel creation, membership, settings, and organization.
Supports public/private channels, categories, and permissions.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

from .models import (
    Channel, ChannelMember, CreateChannelRequest, UpdateChannelRequest,
    ChannelType, MemberRole, ChannelWithMembers
)

logger = logging.getLogger(__name__)


class ChannelManager:
    """
    Manages all channel operations.

    Handles:
    - Channel creation and deletion
    - Channel membership
    - Channel settings and permissions
    - Channel organization (categories, favorites)
    - Channel archiving

    Example:
        >>> manager = ChannelManager(engine)
        >>> channel = await manager.create_channel(user_id, request)
        >>> await manager.add_member(channel_id, user_id)
    """

    def __init__(self, engine):
        """
        Initialize channel manager.

        Args:
            engine: Reference to the ChatEngine
        """
        self.engine = engine
        self._channel_cache: Dict[UUID, Channel] = {}
        self._member_cache: Dict[UUID, List[ChannelMember]] = {}
        logger.info("ChannelManager initialized")

    async def create_channel(
        self,
        creator_id: UUID,
        request: CreateChannelRequest
    ) -> Channel:
        """
        Create a new channel.

        Args:
            creator_id: ID of the user creating the channel
            request: Channel creation request

        Returns:
            Created Channel object

        Raises:
            ValueError: If request is invalid
        """
        # Create channel
        channel = Channel(
            id=uuid4(),
            name=request.name,
            description=request.description,
            channel_type=request.channel_type,
            creator_id=creator_id,
            category=request.category,
            created_at=datetime.utcnow(),
            member_count=1  # Creator is first member
        )

        # Save to database (in production)
        # await self._save_channel(channel)

        # Cache
        self._channel_cache[channel.id] = channel

        # Add creator as owner
        await self.add_member(
            channel_id=channel.id,
            user_id=creator_id,
            role=MemberRole.OWNER
        )

        # Add initial members
        for member_id in request.member_ids:
            if member_id != creator_id:
                await self.add_member(channel.id, member_id)

        logger.info(f"Channel {channel.id} created by user {creator_id}")
        return channel

    async def get_channel(self, channel_id: UUID) -> Optional[Channel]:
        """
        Get a channel by ID.

        Args:
            channel_id: ID of the channel

        Returns:
            Channel object or None
        """
        # Check cache
        if channel_id in self._channel_cache:
            return self._channel_cache[channel_id]

        # In production, fetch from database
        return None

    async def update_channel(
        self,
        channel_id: UUID,
        user_id: UUID,
        request: UpdateChannelRequest
    ) -> Channel:
        """
        Update channel settings.

        Args:
            channel_id: ID of the channel
            user_id: ID of the user updating (must be admin)
            request: Update request

        Returns:
            Updated Channel object

        Raises:
            ValueError: If channel not found
            PermissionError: If user doesn't have permission
        """
        channel = await self.get_channel(channel_id)

        if not channel:
            raise ValueError(f"Channel {channel_id} not found")

        # Check permissions
        if not await self.has_permission(channel_id, user_id, MemberRole.ADMIN):
            raise PermissionError("Only admins can update channel settings")

        # Update fields
        if request.name is not None:
            channel.name = request.name
        if request.description is not None:
            channel.description = request.description
        if request.avatar_url is not None:
            channel.avatar_url = request.avatar_url
        if request.settings is not None:
            channel.settings.update(request.settings)

        channel.updated_at = datetime.utcnow()

        # Update in database (production)
        # await self._update_channel(channel)

        self._channel_cache[channel_id] = channel

        logger.info(f"Channel {channel_id} updated by user {user_id}")
        return channel

    async def delete_channel(
        self,
        channel_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Delete a channel.

        Args:
            channel_id: ID of the channel
            user_id: ID of the user deleting (must be owner)

        Returns:
            True if successful

        Raises:
            PermissionError: If user doesn't have permission
        """
        channel = await self.get_channel(channel_id)

        if not channel:
            return False

        # Check ownership
        if not await self.has_permission(channel_id, user_id, MemberRole.OWNER):
            raise PermissionError("Only owners can delete channels")

        # Delete from database (production)
        # await self._delete_channel(channel_id)

        # Remove from cache
        self._channel_cache.pop(channel_id, None)
        self._member_cache.pop(channel_id, None)

        logger.info(f"Channel {channel_id} deleted by user {user_id}")
        return True

    async def archive_channel(
        self,
        channel_id: UUID,
        user_id: UUID,
        archived: bool = True
    ) -> Channel:
        """
        Archive or unarchive a channel.

        Args:
            channel_id: ID of the channel
            user_id: ID of the user
            archived: True to archive, False to unarchive

        Returns:
            Updated Channel object
        """
        channel = await self.get_channel(channel_id)

        if not channel:
            raise ValueError(f"Channel {channel_id} not found")

        if not await self.has_permission(channel_id, user_id, MemberRole.ADMIN):
            raise PermissionError("Only admins can archive channels")

        channel.is_archived = archived
        channel.updated_at = datetime.utcnow()

        # Update in database
        self._channel_cache[channel_id] = channel

        logger.info(f"Channel {channel_id} {'archived' if archived else 'unarchived'}")
        return channel

    async def add_member(
        self,
        channel_id: UUID,
        user_id: UUID,
        role: MemberRole = MemberRole.MEMBER
    ) -> ChannelMember:
        """
        Add a member to a channel.

        Args:
            channel_id: ID of the channel
            user_id: ID of the user to add
            role: Role for the member

        Returns:
            Created ChannelMember object
        """
        # Check if already a member
        if await self.is_member(channel_id, user_id):
            logger.warning(f"User {user_id} already member of channel {channel_id}")
            # Return existing membership
            members = self._member_cache.get(channel_id, [])
            for member in members:
                if member.user_id == user_id:
                    return member

        # Create membership
        member = ChannelMember(
            id=uuid4(),
            channel_id=channel_id,
            user_id=user_id,
            role=role,
            joined_at=datetime.utcnow()
        )

        # Save to database (production)
        # await self._save_member(member)

        # Update cache
        if channel_id not in self._member_cache:
            self._member_cache[channel_id] = []
        self._member_cache[channel_id].append(member)

        # Update channel member count
        channel = await self.get_channel(channel_id)
        if channel:
            channel.member_count += 1
            self._channel_cache[channel_id] = channel

        logger.info(f"User {user_id} added to channel {channel_id} as {role}")
        return member

    async def remove_member(
        self,
        channel_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Remove a member from a channel.

        Args:
            channel_id: ID of the channel
            user_id: ID of the user to remove

        Returns:
            True if successful
        """
        # Delete from database (production)
        # await self._delete_member(channel_id, user_id)

        # Update cache
        if channel_id in self._member_cache:
            self._member_cache[channel_id] = [
                m for m in self._member_cache[channel_id]
                if m.user_id != user_id
            ]

        # Update channel member count
        channel = await self.get_channel(channel_id)
        if channel:
            channel.member_count = max(0, channel.member_count - 1)
            self._channel_cache[channel_id] = channel

        logger.info(f"User {user_id} removed from channel {channel_id}")
        return True

    async def update_member_role(
        self,
        channel_id: UUID,
        user_id: UUID,
        new_role: MemberRole,
        admin_id: UUID
    ) -> ChannelMember:
        """
        Update a member's role.

        Args:
            channel_id: ID of the channel
            user_id: ID of the member
            new_role: New role
            admin_id: ID of user making the change (must be admin)

        Returns:
            Updated ChannelMember object

        Raises:
            PermissionError: If admin doesn't have permission
        """
        # Check admin permissions
        if not await self.has_permission(channel_id, admin_id, MemberRole.ADMIN):
            raise PermissionError("Only admins can change member roles")

        # Find and update member
        if channel_id in self._member_cache:
            for member in self._member_cache[channel_id]:
                if member.user_id == user_id:
                    member.role = new_role
                    # Update in database
                    return member

        raise ValueError(f"User {user_id} not a member of channel {channel_id}")

    async def get_members(self, channel_id: UUID) -> List[ChannelMember]:
        """
        Get all members of a channel.

        Args:
            channel_id: ID of the channel

        Returns:
            List of ChannelMember objects
        """
        # Check cache
        if channel_id in self._member_cache:
            return self._member_cache[channel_id].copy()

        # In production, fetch from database
        return []

    async def is_member(self, channel_id: UUID, user_id: UUID) -> bool:
        """
        Check if a user is a member of a channel.

        Args:
            channel_id: ID of the channel
            user_id: ID of the user

        Returns:
            True if user is a member
        """
        members = await self.get_members(channel_id)
        return any(m.user_id == user_id for m in members)

    async def has_permission(
        self,
        channel_id: UUID,
        user_id: UUID,
        required_role: MemberRole
    ) -> bool:
        """
        Check if a user has a specific role or higher.

        Args:
            channel_id: ID of the channel
            user_id: ID of the user
            required_role: Required role level

        Returns:
            True if user has permission
        """
        members = await self.get_members(channel_id)
        role_hierarchy = {
            MemberRole.GUEST: 0,
            MemberRole.MEMBER: 1,
            MemberRole.MODERATOR: 2,
            MemberRole.ADMIN: 3,
            MemberRole.OWNER: 4
        }

        for member in members:
            if member.user_id == user_id:
                user_level = role_hierarchy.get(member.role, 0)
                required_level = role_hierarchy.get(required_role, 0)
                return user_level >= required_level

        return False

    async def get_user_channels(
        self,
        user_id: UUID,
        include_archived: bool = False
    ) -> List[Channel]:
        """
        Get all channels a user is a member of.

        Args:
            user_id: ID of the user
            include_archived: Include archived channels

        Returns:
            List of Channel objects
        """
        channels = []

        for channel_id, members in self._member_cache.items():
            if any(m.user_id == user_id for m in members):
                channel = await self.get_channel(channel_id)
                if channel:
                    if include_archived or not channel.is_archived:
                        channels.append(channel)

        # Sort by created date
        channels.sort(key=lambda x: x.created_at, reverse=True)

        logger.debug(f"Retrieved {len(channels)} channels for user {user_id}")
        return channels

    async def get_public_channels(self) -> List[Channel]:
        """
        Get all public channels.

        Returns:
            List of public Channel objects
        """
        channels = [
            ch for ch in self._channel_cache.values()
            if ch.channel_type == ChannelType.PUBLIC and not ch.is_archived
        ]

        channels.sort(key=lambda x: x.member_count, reverse=True)
        return channels

    async def get_channel_with_members(
        self,
        channel_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Optional[ChannelWithMembers]:
        """
        Get channel with member information and unread count.

        Args:
            channel_id: ID of the channel
            user_id: Optional user ID for unread count

        Returns:
            ChannelWithMembers object or None
        """
        channel = await self.get_channel(channel_id)

        if not channel:
            return None

        members = await self.get_members(channel_id)

        # Get unread count if user_id provided
        unread_count = 0
        if user_id:
            # In production: query from message_manager
            # unread_count = await self.engine.message_manager.get_unread_count(channel_id, user_id)
            pass

        channel_with_members = ChannelWithMembers(
            **channel.dict(),
            members=members,
            unread_count=unread_count
        )

        return channel_with_members

    async def search_channels(
        self,
        query: str,
        user_id: Optional[UUID] = None
    ) -> List[Channel]:
        """
        Search for channels by name or description.

        Args:
            query: Search query
            user_id: Optional user ID to filter accessible channels

        Returns:
            List of matching Channel objects
        """
        query_lower = query.lower()

        channels = [
            ch for ch in self._channel_cache.values()
            if (query_lower in ch.name.lower() or
                (ch.description and query_lower in ch.description.lower()))
            and not ch.is_archived
        ]

        # Filter by accessibility
        if user_id:
            accessible = []
            for ch in channels:
                if ch.channel_type == ChannelType.PUBLIC or await self.is_member(ch.id, user_id):
                    accessible.append(ch)
            channels = accessible

        return channels
