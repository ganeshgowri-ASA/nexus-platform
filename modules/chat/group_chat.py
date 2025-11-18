"""
Group Chat - Handles group conversations and management.

Manages group creation, member management, group settings,
permissions, and group-specific features.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

from .models import (
    Channel, ChannelType, ChannelMember, MemberRole,
    CreateChannelRequest, User
)

logger = logging.getLogger(__name__)


class GroupChat:
    """
    Manages group chat functionality.

    Handles:
    - Group creation and settings
    - Member invitations and removal
    - Admin and moderator permissions
    - Group descriptions and avatars
    - Member limits and rules

    Example:
        >>> group = GroupChat(engine)
        >>> channel = await group.create_group(creator_id, "My Group", [user1, user2])
        >>> await group.invite_members(channel_id, admin_id, [user3, user4])
    """

    def __init__(self, engine):
        """
        Initialize group chat manager.

        Args:
            engine: Reference to the ChatEngine
        """
        self.engine = engine
        self._group_settings: Dict[UUID, Dict[str, Any]] = {}
        logger.info("GroupChat initialized")

    async def create_group(
        self,
        creator_id: UUID,
        name: str,
        member_ids: List[UUID],
        description: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> Channel:
        """
        Create a new group chat.

        Args:
            creator_id: ID of the user creating the group
            name: Group name
            member_ids: List of initial member IDs
            description: Optional group description
            avatar_url: Optional group avatar URL

        Returns:
            Created Channel object
        """
        # Create channel request
        request = CreateChannelRequest(
            name=name,
            description=description,
            channel_type=ChannelType.GROUP,
            member_ids=member_ids
        )

        # Create channel
        channel = await self.engine.channel_manager.create_channel(
            creator_id=creator_id,
            request=request
        )

        if avatar_url:
            channel.avatar_url = avatar_url
            self.engine.channel_manager._channel_cache[channel.id] = channel

        # Initialize group settings
        self._group_settings[channel.id] = {
            "max_members": 256,
            "allow_member_invites": True,
            "require_approval": False,
            "allow_message_deletion": True,
            "message_retention_days": None,  # None = forever
            "slow_mode_seconds": 0,
        }

        logger.info(f"Group {channel.id} created: {name}")
        return channel

    async def invite_members(
        self,
        channel_id: UUID,
        inviter_id: UUID,
        user_ids: List[UUID]
    ) -> List[ChannelMember]:
        """
        Invite members to a group.

        Args:
            channel_id: ID of the group channel
            inviter_id: ID of the user inviting (must have permission)
            user_ids: List of user IDs to invite

        Returns:
            List of created ChannelMember objects

        Raises:
            PermissionError: If inviter doesn't have permission
        """
        # Check if inviter has permission
        settings = self._group_settings.get(channel_id, {})

        if not settings.get("allow_member_invites", True):
            # Only admins can invite
            if not await self.engine.channel_manager.has_permission(
                channel_id, inviter_id, MemberRole.ADMIN
            ):
                raise PermissionError("Only admins can invite members")
        else:
            # Must be a member
            if not await self.engine.channel_manager.is_member(channel_id, inviter_id):
                raise PermissionError("Must be a member to invite others")

        # Check member limit
        current_members = await self.engine.channel_manager.get_members(channel_id)
        max_members = settings.get("max_members", 256)

        if len(current_members) + len(user_ids) > max_members:
            raise ValueError(f"Group member limit ({max_members}) would be exceeded")

        # Add members
        added_members = []
        for user_id in user_ids:
            member = await self.engine.channel_manager.add_member(
                channel_id=channel_id,
                user_id=user_id,
                role=MemberRole.MEMBER
            )
            added_members.append(member)

            # Send notification
            await self.engine.notifications.send_notification(
                user_id=user_id,
                title="Added to Group",
                body=f"You've been added to a group chat"
            )

        logger.info(f"{len(added_members)} members invited to group {channel_id}")
        return added_members

    async def remove_member(
        self,
        channel_id: UUID,
        admin_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Remove a member from a group.

        Args:
            channel_id: ID of the group channel
            admin_id: ID of the admin removing the member
            user_id: ID of the member to remove

        Returns:
            True if successful

        Raises:
            PermissionError: If admin doesn't have permission
        """
        # Check permissions
        if not await self.engine.channel_manager.has_permission(
            channel_id, admin_id, MemberRole.ADMIN
        ):
            raise PermissionError("Only admins can remove members")

        # Cannot remove owner
        members = await self.engine.channel_manager.get_members(channel_id)
        target_member = next((m for m in members if m.user_id == user_id), None)

        if target_member and target_member.role == MemberRole.OWNER:
            raise PermissionError("Cannot remove group owner")

        # Remove member
        success = await self.engine.channel_manager.remove_member(channel_id, user_id)

        if success:
            # Broadcast to group
            await self.engine.websocket_handler.broadcast_user_left(channel_id, user_id)

        logger.info(f"User {user_id} removed from group {channel_id}")
        return success

    async def leave_group(
        self,
        channel_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Leave a group.

        Args:
            channel_id: ID of the group channel
            user_id: ID of the user leaving

        Returns:
            True if successful
        """
        # Check if user is owner
        members = await self.engine.channel_manager.get_members(channel_id)
        user_member = next((m for m in members if m.user_id == user_id), None)

        if user_member and user_member.role == MemberRole.OWNER:
            # Transfer ownership or delete group
            if len(members) > 1:
                # Transfer to first admin or member
                new_owner = next(
                    (m for m in members if m.user_id != user_id and m.role == MemberRole.ADMIN),
                    next((m for m in members if m.user_id != user_id), None)
                )
                if new_owner:
                    await self.engine.channel_manager.update_member_role(
                        channel_id, new_owner.user_id, MemberRole.OWNER, user_id
                    )
            else:
                # Last member - delete group
                await self.engine.channel_manager.delete_channel(channel_id, user_id)
                return True

        # Leave group
        success = await self.engine.channel_manager.remove_member(channel_id, user_id)

        if success:
            await self.engine.websocket_handler.broadcast_user_left(channel_id, user_id)

        return success

    async def update_group_info(
        self,
        channel_id: UUID,
        admin_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> Channel:
        """
        Update group information.

        Args:
            channel_id: ID of the group channel
            admin_id: ID of the admin updating
            name: New name
            description: New description
            avatar_url: New avatar URL

        Returns:
            Updated Channel object
        """
        from .models import UpdateChannelRequest

        request = UpdateChannelRequest(
            name=name,
            description=description,
            avatar_url=avatar_url
        )

        channel = await self.engine.channel_manager.update_channel(
            channel_id=channel_id,
            user_id=admin_id,
            request=request
        )

        logger.info(f"Group {channel_id} info updated")
        return channel

    async def promote_to_admin(
        self,
        channel_id: UUID,
        promoter_id: UUID,
        user_id: UUID
    ) -> ChannelMember:
        """
        Promote a member to admin.

        Args:
            channel_id: ID of the group channel
            promoter_id: ID of the user promoting (must be owner/admin)
            user_id: ID of the user to promote

        Returns:
            Updated ChannelMember object
        """
        member = await self.engine.channel_manager.update_member_role(
            channel_id=channel_id,
            user_id=user_id,
            new_role=MemberRole.ADMIN,
            admin_id=promoter_id
        )

        # Notify user
        await self.engine.notifications.send_notification(
            user_id=user_id,
            title="Promoted to Admin",
            body="You've been promoted to admin in a group"
        )

        return member

    async def demote_admin(
        self,
        channel_id: UUID,
        demoter_id: UUID,
        user_id: UUID
    ) -> ChannelMember:
        """
        Demote an admin to member.

        Args:
            channel_id: ID of the group channel
            demoter_id: ID of the user demoting (must be owner)
            user_id: ID of the admin to demote

        Returns:
            Updated ChannelMember object
        """
        # Only owner can demote admins
        if not await self.engine.channel_manager.has_permission(
            channel_id, demoter_id, MemberRole.OWNER
        ):
            raise PermissionError("Only owner can demote admins")

        member = await self.engine.channel_manager.update_member_role(
            channel_id=channel_id,
            user_id=user_id,
            new_role=MemberRole.MEMBER,
            admin_id=demoter_id
        )

        return member

    async def update_group_settings(
        self,
        channel_id: UUID,
        admin_id: UUID,
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update group settings.

        Args:
            channel_id: ID of the group channel
            admin_id: ID of the admin updating
            settings: Settings to update

        Returns:
            Updated settings dictionary
        """
        # Check permissions
        if not await self.engine.channel_manager.has_permission(
            channel_id, admin_id, MemberRole.ADMIN
        ):
            raise PermissionError("Only admins can update group settings")

        if channel_id not in self._group_settings:
            self._group_settings[channel_id] = {}

        self._group_settings[channel_id].update(settings)

        logger.info(f"Group {channel_id} settings updated")
        return self._group_settings[channel_id]

    async def get_group_settings(self, channel_id: UUID) -> Dict[str, Any]:
        """
        Get group settings.

        Args:
            channel_id: ID of the group channel

        Returns:
            Settings dictionary
        """
        return self._group_settings.get(channel_id, {})

    async def get_group_admins(self, channel_id: UUID) -> List[ChannelMember]:
        """
        Get all admins and owner of a group.

        Args:
            channel_id: ID of the group channel

        Returns:
            List of admin ChannelMember objects
        """
        members = await self.engine.channel_manager.get_members(channel_id)

        admins = [
            m for m in members
            if m.role in [MemberRole.OWNER, MemberRole.ADMIN, MemberRole.MODERATOR]
        ]

        return admins
