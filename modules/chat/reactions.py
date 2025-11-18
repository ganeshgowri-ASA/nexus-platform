"""
Reactions - Handles emoji reactions to messages.

Manages adding, removing, and querying emoji reactions on messages.
Supports reaction aggregation and real-time updates.
"""

import logging
from typing import List, Dict, Set
from datetime import datetime
from uuid import UUID, uuid4
from collections import defaultdict

from .models import Reaction, MessageReaction

logger = logging.getLogger(__name__)


class Reactions:
    """
    Manages message reactions.

    Handles:
    - Adding/removing reactions
    - Reaction aggregation
    - Popular emoji tracking
    - Reaction notifications

    Example:
        >>> reactions = Reactions(engine)
        >>> await reactions.add_reaction(message_id, user_id, "👍")
        >>> summary = await reactions.get_message_reactions(message_id)
    """

    # Popular emojis for quick access
    POPULAR_EMOJIS = [
        "👍", "❤️", "😂", "🎉", "😮", "😢", "🙏", "👏",
        "🔥", "✅", "👀", "💯", "🚀", "⭐", "💪", "🎊"
    ]

    def __init__(self, engine):
        """
        Initialize reactions manager.

        Args:
            engine: Reference to the ChatEngine
        """
        self.engine = engine
        self._reactions: Dict[UUID, List[Reaction]] = defaultdict(list)
        logger.info("Reactions initialized")

    async def add_reaction(
        self,
        message_id: UUID,
        user_id: UUID,
        emoji: str
    ) -> Reaction:
        """
        Add a reaction to a message.

        Args:
            message_id: ID of the message
            user_id: ID of the user reacting
            emoji: Emoji character

        Returns:
            Created Reaction object

        Raises:
            ValueError: If reaction already exists
        """
        # Check if user already reacted with this emoji
        existing = await self.get_user_reaction(message_id, user_id, emoji)

        if existing:
            raise ValueError("User already reacted with this emoji")

        # Create reaction
        reaction = Reaction(
            id=uuid4(),
            message_id=message_id,
            user_id=user_id,
            emoji=emoji,
            created_at=datetime.utcnow()
        )

        # Save to storage
        self._reactions[message_id].append(reaction)

        # In production: save to database
        # INSERT INTO reactions ...

        # Broadcast via WebSocket
        await self.engine.websocket_handler.broadcast_reaction(
            message_id=message_id,
            user_id=user_id,
            emoji=emoji,
            action="add"
        )

        # Send notification to message author
        message = await self.engine.message_manager.get_message(message_id)
        if message and message.user_id != user_id:
            await self.engine.notifications.send_notification(
                user_id=message.user_id,
                title="New Reaction",
                body=f"Someone reacted {emoji} to your message"
            )

        logger.info(f"Reaction {emoji} added by user {user_id} to message {message_id}")
        return reaction

    async def remove_reaction(
        self,
        message_id: UUID,
        user_id: UUID,
        emoji: str
    ) -> bool:
        """
        Remove a reaction from a message.

        Args:
            message_id: ID of the message
            user_id: ID of the user
            emoji: Emoji character

        Returns:
            True if removed successfully
        """
        # Find and remove reaction
        if message_id in self._reactions:
            self._reactions[message_id] = [
                r for r in self._reactions[message_id]
                if not (r.user_id == user_id and r.emoji == emoji)
            ]

        # In production: delete from database
        # DELETE FROM reactions WHERE message_id = ... AND user_id = ... AND emoji = ...

        # Broadcast via WebSocket
        await self.engine.websocket_handler.broadcast_reaction(
            message_id=message_id,
            user_id=user_id,
            emoji=emoji,
            action="remove"
        )

        logger.info(f"Reaction {emoji} removed by user {user_id} from message {message_id}")
        return True

    async def toggle_reaction(
        self,
        message_id: UUID,
        user_id: UUID,
        emoji: str
    ) -> bool:
        """
        Toggle a reaction (add if not exists, remove if exists).

        Args:
            message_id: ID of the message
            user_id: ID of the user
            emoji: Emoji character

        Returns:
            True if added, False if removed
        """
        existing = await self.get_user_reaction(message_id, user_id, emoji)

        if existing:
            await self.remove_reaction(message_id, user_id, emoji)
            return False
        else:
            await self.add_reaction(message_id, user_id, emoji)
            return True

    async def get_message_reactions(
        self,
        message_id: UUID,
        current_user_id: Optional[UUID] = None
    ) -> List[MessageReaction]:
        """
        Get aggregated reactions for a message.

        Args:
            message_id: ID of the message
            current_user_id: Optional current user ID to mark their reactions

        Returns:
            List of MessageReaction objects with counts and users
        """
        reactions = self._reactions.get(message_id, [])

        # Aggregate by emoji
        emoji_map: Dict[str, MessageReaction] = {}

        for reaction in reactions:
            if reaction.emoji not in emoji_map:
                emoji_map[reaction.emoji] = MessageReaction(
                    emoji=reaction.emoji,
                    count=0,
                    users=[],
                    has_reacted=False
                )

            emoji_map[reaction.emoji].count += 1
            emoji_map[reaction.emoji].users.append(reaction.user_id)

            if current_user_id and reaction.user_id == current_user_id:
                emoji_map[reaction.emoji].has_reacted = True

        # Sort by count descending
        result = list(emoji_map.values())
        result.sort(key=lambda x: x.count, reverse=True)

        return result

    async def get_user_reaction(
        self,
        message_id: UUID,
        user_id: UUID,
        emoji: str
    ) -> Optional[Reaction]:
        """
        Get a specific user's reaction.

        Args:
            message_id: ID of the message
            user_id: ID of the user
            emoji: Emoji character

        Returns:
            Reaction object or None
        """
        reactions = self._reactions.get(message_id, [])

        for reaction in reactions:
            if reaction.user_id == user_id and reaction.emoji == emoji:
                return reaction

        return None

    async def get_user_reactions_for_message(
        self,
        message_id: UUID,
        user_id: UUID
    ) -> List[Reaction]:
        """
        Get all reactions a user made on a message.

        Args:
            message_id: ID of the message
            user_id: ID of the user

        Returns:
            List of Reaction objects
        """
        reactions = self._reactions.get(message_id, [])

        return [r for r in reactions if r.user_id == user_id]

    async def get_reaction_count(self, message_id: UUID) -> int:
        """
        Get total reaction count for a message.

        Args:
            message_id: ID of the message

        Returns:
            Total count of reactions
        """
        return len(self._reactions.get(message_id, []))

    async def get_top_reactions(
        self,
        channel_id: UUID,
        limit: int = 10
    ) -> List[Dict[str, any]]:
        """
        Get most used reactions in a channel.

        Args:
            channel_id: ID of the channel
            limit: Number of top reactions to return

        Returns:
            List of dictionaries with emoji and count
        """
        # In production: query from database
        # SELECT emoji, COUNT(*) as count FROM reactions r
        # JOIN messages m ON r.message_id = m.id
        # WHERE m.channel_id = channel_id
        # GROUP BY emoji
        # ORDER BY count DESC
        # LIMIT limit

        emoji_counts: Dict[str, int] = defaultdict(int)

        for message_reactions in self._reactions.values():
            for reaction in message_reactions:
                emoji_counts[reaction.emoji] += 1

        # Sort by count
        top = [
            {"emoji": emoji, "count": count}
            for emoji, count in emoji_counts.items()
        ]
        top.sort(key=lambda x: x["count"], reverse=True)

        return top[:limit]

    async def get_users_who_reacted(
        self,
        message_id: UUID,
        emoji: str
    ) -> List[UUID]:
        """
        Get all users who reacted with a specific emoji.

        Args:
            message_id: ID of the message
            emoji: Emoji character

        Returns:
            List of user IDs
        """
        reactions = self._reactions.get(message_id, [])

        return [
            r.user_id for r in reactions
            if r.emoji == emoji
        ]

    async def remove_all_reactions(
        self,
        message_id: UUID,
        admin_id: UUID
    ) -> bool:
        """
        Remove all reactions from a message (admin only).

        Args:
            message_id: ID of the message
            admin_id: ID of the admin

        Returns:
            True if successful
        """
        # In production: check admin permissions

        # Remove all reactions
        self._reactions.pop(message_id, None)

        # In production: delete from database
        # DELETE FROM reactions WHERE message_id = message_id

        logger.info(f"All reactions removed from message {message_id} by admin {admin_id}")
        return True

    def get_popular_emojis(self) -> List[str]:
        """
        Get list of popular emojis for quick selection.

        Returns:
            List of emoji characters
        """
        return self.POPULAR_EMOJIS.copy()


from typing import Optional
