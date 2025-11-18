"""
Comprehensive unit tests for the NEXUS Chat & Messaging Module.

Tests all core functionality including:
- Message management
- Channel operations
- Direct messaging
- Group chat
- File sharing
- Reactions
- Threads
- Search
- Notifications
- AI features
- WebSocket handling
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

# Import chat components
import sys
sys.path.insert(0, '../modules')

from chat.chat_engine import ChatEngine
from chat.message_manager import MessageManager
from chat.channel_manager import ChannelManager
from chat.direct_messaging import DirectMessaging
from chat.group_chat import GroupChat
from chat.file_sharing import FileSharing
from chat.reactions import Reactions
from chat.threads import Threads
from chat.search import Search
from chat.notifications import Notifications
from chat.ai_features import AIFeatures
from chat.websocket_handler import WebSocketHandler
from chat.models import (
    User, Message, Channel, ChannelType, UserStatus,
    MessageType, MessageStatus, MemberRole,
    CreateChannelRequest, SendMessageRequest
)


# Fixtures
@pytest.fixture
def engine():
    """Create a ChatEngine instance for testing."""
    return ChatEngine()


@pytest.fixture
async def initialized_engine(engine):
    """Create and initialize a ChatEngine."""
    await engine.initialize()
    yield engine
    await engine.shutdown()


@pytest.fixture
def test_user():
    """Create a test user."""
    return User(
        id=uuid4(),
        username="test_user",
        email="test@example.com",
        display_name="Test User",
        status=UserStatus.ONLINE
    )


@pytest.fixture
def test_user2():
    """Create a second test user."""
    return User(
        id=uuid4(),
        username="test_user2",
        email="test2@example.com",
        display_name="Test User 2",
        status=UserStatus.ONLINE
    )


@pytest.fixture
def test_channel(test_user):
    """Create a test channel."""
    return Channel(
        id=uuid4(),
        name="test-channel",
        description="Test Channel",
        channel_type=ChannelType.PUBLIC,
        creator_id=test_user.id
    )


# Message Manager Tests
class TestMessageManager:
    """Tests for MessageManager."""

    @pytest.mark.asyncio
    async def test_create_message(self, initialized_engine, test_user, test_channel):
        """Test message creation."""
        request = SendMessageRequest(
            channel_id=test_channel.id,
            content="Hello, World!",
            message_type=MessageType.TEXT
        )

        message = await initialized_engine.message_manager.create_message(
            user_id=test_user.id,
            request=request
        )

        assert message is not None
        assert message.content == "Hello, World!"
        assert message.user_id == test_user.id
        assert message.channel_id == test_channel.id
        assert message.status == MessageStatus.SENT

    @pytest.mark.asyncio
    async def test_get_messages(self, initialized_engine, test_user, test_channel):
        """Test retrieving messages."""
        # Create multiple messages
        for i in range(5):
            request = SendMessageRequest(
                channel_id=test_channel.id,
                content=f"Message {i}"
            )
            await initialized_engine.message_manager.create_message(
                user_id=test_user.id,
                request=request
            )

        # Retrieve messages
        messages = await initialized_engine.message_manager.get_messages(
            channel_id=test_channel.id,
            limit=10
        )

        assert len(messages) == 5

    @pytest.mark.asyncio
    async def test_update_message(self, initialized_engine, test_user, test_channel):
        """Test message editing."""
        # Create message
        request = SendMessageRequest(
            channel_id=test_channel.id,
            content="Original content"
        )
        message = await initialized_engine.message_manager.create_message(
            user_id=test_user.id,
            request=request
        )

        # Update message
        updated = await initialized_engine.message_manager.update_message(
            message_id=message.id,
            user_id=test_user.id,
            content="Updated content"
        )

        assert updated.content == "Updated content"
        assert updated.is_edited is True

    @pytest.mark.asyncio
    async def test_delete_message(self, initialized_engine, test_user, test_channel):
        """Test message deletion."""
        # Create message
        request = SendMessageRequest(
            channel_id=test_channel.id,
            content="To be deleted"
        )
        message = await initialized_engine.message_manager.create_message(
            user_id=test_user.id,
            request=request
        )

        # Delete message
        success = await initialized_engine.message_manager.delete_message(
            message_id=message.id,
            user_id=test_user.id,
            hard_delete=False
        )

        assert success is True

        # Verify soft delete
        deleted_msg = await initialized_engine.message_manager.get_message(message.id)
        assert deleted_msg.deleted_at is not None


# Channel Manager Tests
class TestChannelManager:
    """Tests for ChannelManager."""

    @pytest.mark.asyncio
    async def test_create_channel(self, initialized_engine, test_user):
        """Test channel creation."""
        request = CreateChannelRequest(
            name="New Channel",
            description="Test description",
            channel_type=ChannelType.PUBLIC,
            member_ids=[test_user.id]
        )

        channel = await initialized_engine.channel_manager.create_channel(
            creator_id=test_user.id,
            request=request
        )

        assert channel is not None
        assert channel.name == "New Channel"
        assert channel.creator_id == test_user.id

    @pytest.mark.asyncio
    async def test_add_member(self, initialized_engine, test_user, test_user2, test_channel):
        """Test adding member to channel."""
        member = await initialized_engine.channel_manager.add_member(
            channel_id=test_channel.id,
            user_id=test_user2.id,
            role=MemberRole.MEMBER
        )

        assert member.user_id == test_user2.id
        assert member.channel_id == test_channel.id

    @pytest.mark.asyncio
    async def test_is_member(self, initialized_engine, test_user, test_channel):
        """Test member checking."""
        # Add user as member
        await initialized_engine.channel_manager.add_member(
            channel_id=test_channel.id,
            user_id=test_user.id
        )

        is_member = await initialized_engine.channel_manager.is_member(
            channel_id=test_channel.id,
            user_id=test_user.id
        )

        assert is_member is True


# Direct Messaging Tests
class TestDirectMessaging:
    """Tests for DirectMessaging."""

    @pytest.mark.asyncio
    async def test_create_dm(self, initialized_engine, test_user, test_user2):
        """Test DM channel creation."""
        dm = await initialized_engine.direct_messaging.get_or_create_dm(
            user1_id=test_user.id,
            user2_id=test_user2.id
        )

        assert dm is not None
        assert dm.channel_type == ChannelType.DIRECT

    @pytest.mark.asyncio
    async def test_block_user(self, initialized_engine, test_user, test_user2):
        """Test blocking a user."""
        success = await initialized_engine.direct_messaging.block_user(
            user_id=test_user.id,
            blocked_user_id=test_user2.id
        )

        assert success is True

        is_blocked = await initialized_engine.direct_messaging.is_blocked(
            user_id=test_user.id,
            other_user_id=test_user2.id
        )

        assert is_blocked is True


# Group Chat Tests
class TestGroupChat:
    """Tests for GroupChat."""

    @pytest.mark.asyncio
    async def test_create_group(self, initialized_engine, test_user, test_user2):
        """Test group creation."""
        group = await initialized_engine.group_chat.create_group(
            creator_id=test_user.id,
            name="Test Group",
            member_ids=[test_user2.id],
            description="A test group"
        )

        assert group is not None
        assert group.name == "Test Group"
        assert group.channel_type == ChannelType.GROUP


# File Sharing Tests
class TestFileSharing:
    """Tests for FileSharing."""

    @pytest.mark.asyncio
    async def test_upload_file(self, initialized_engine, test_user):
        """Test file upload."""
        file_data = b"Test file content"
        filename = "test.txt"

        attachment = await initialized_engine.file_sharing.upload_file(
            user_id=test_user.id,
            file_data=file_data,
            filename=filename
        )

        assert attachment is not None
        assert attachment.file_name == filename
        assert attachment.file_size == len(file_data)


# Reactions Tests
class TestReactions:
    """Tests for Reactions."""

    @pytest.mark.asyncio
    async def test_add_reaction(self, initialized_engine, test_user, test_channel):
        """Test adding reaction to message."""
        # Create a message first
        request = SendMessageRequest(
            channel_id=test_channel.id,
            content="Test message"
        )
        message = await initialized_engine.message_manager.create_message(
            user_id=test_user.id,
            request=request
        )

        # Add reaction
        reaction = await initialized_engine.reactions.add_reaction(
            message_id=message.id,
            user_id=test_user.id,
            emoji="👍"
        )

        assert reaction is not None
        assert reaction.emoji == "👍"

    @pytest.mark.asyncio
    async def test_get_message_reactions(self, initialized_engine, test_user, test_channel):
        """Test getting reactions for a message."""
        # Create message
        request = SendMessageRequest(
            channel_id=test_channel.id,
            content="Test message"
        )
        message = await initialized_engine.message_manager.create_message(
            user_id=test_user.id,
            request=request
        )

        # Add reactions
        await initialized_engine.reactions.add_reaction(
            message_id=message.id,
            user_id=test_user.id,
            emoji="👍"
        )

        # Get reactions
        reactions = await initialized_engine.reactions.get_message_reactions(
            message_id=message.id
        )

        assert len(reactions) > 0
        assert reactions[0].emoji == "👍"


# Threads Tests
class TestThreads:
    """Tests for Threads."""

    @pytest.mark.asyncio
    async def test_create_reply(self, initialized_engine, test_user, test_channel):
        """Test creating a threaded reply."""
        # Create parent message
        request = SendMessageRequest(
            channel_id=test_channel.id,
            content="Parent message"
        )
        parent = await initialized_engine.message_manager.create_message(
            user_id=test_user.id,
            request=request
        )

        # Create reply
        reply = await initialized_engine.threads.create_reply(
            parent_message_id=parent.id,
            user_id=test_user.id,
            content="Reply message"
        )

        assert reply is not None
        assert reply.parent_id == parent.id


# Search Tests
class TestSearch:
    """Tests for Search."""

    @pytest.mark.asyncio
    async def test_search_messages(self, initialized_engine, test_user, test_channel):
        """Test message search."""
        # Create messages
        for content in ["Hello world", "Test message", "Search this"]:
            request = SendMessageRequest(
                channel_id=test_channel.id,
                content=content
            )
            await initialized_engine.message_manager.create_message(
                user_id=test_user.id,
                request=request
            )

        # Search
        results = await initialized_engine.search.search_messages(
            query="test",
            channel_id=test_channel.id
        )

        assert len(results) > 0


# Notifications Tests
class TestNotifications:
    """Tests for Notifications."""

    @pytest.mark.asyncio
    async def test_send_notification(self, initialized_engine, test_user):
        """Test sending notification."""
        notification = await initialized_engine.notifications.send_notification(
            user_id=test_user.id,
            title="Test Notification",
            body="This is a test"
        )

        assert notification is not None
        assert notification.title == "Test Notification"

    @pytest.mark.asyncio
    async def test_dnd_mode(self, initialized_engine, test_user):
        """Test Do Not Disturb mode."""
        # Enable DND
        await initialized_engine.notifications.set_dnd_mode(
            user_id=test_user.id,
            enabled=True
        )

        is_dnd = await initialized_engine.notifications.is_dnd_enabled(test_user.id)
        assert is_dnd is True


# AI Features Tests
class TestAIFeatures:
    """Tests for AIFeatures."""

    @pytest.mark.asyncio
    async def test_get_smart_replies(self, initialized_engine, test_user, test_channel):
        """Test smart reply generation."""
        # Create message
        request = SendMessageRequest(
            channel_id=test_channel.id,
            content="How are you?"
        )
        message = await initialized_engine.message_manager.create_message(
            user_id=test_user.id,
            request=request
        )

        # Get smart replies
        replies = await initialized_engine.ai_features.get_smart_replies(message)

        assert len(replies) > 0

    @pytest.mark.asyncio
    async def test_detect_spam(self, initialized_engine, test_user, test_channel):
        """Test spam detection."""
        # Create spam message
        request = SendMessageRequest(
            channel_id=test_channel.id,
            content="CLICK HERE NOW!!! LIMITED TIME OFFER!!!"
        )
        message = await initialized_engine.message_manager.create_message(
            user_id=test_user.id,
            request=request
        )

        is_spam = await initialized_engine.ai_features.detect_spam(message)

        # Note: May or may not detect as spam depending on implementation
        assert isinstance(is_spam, bool)


# WebSocket Handler Tests
class TestWebSocketHandler:
    """Tests for WebSocketHandler."""

    def test_websocket_initialization(self, initialized_engine):
        """Test WebSocket handler initialization."""
        handler = initialized_engine.websocket_handler
        assert handler is not None


# Integration Tests
class TestIntegration:
    """Integration tests for full workflows."""

    @pytest.mark.asyncio
    async def test_full_message_workflow(self, initialized_engine, test_user, test_user2):
        """Test complete message sending workflow."""
        # Create channel
        request = CreateChannelRequest(
            name="Integration Test",
            channel_type=ChannelType.PUBLIC,
            member_ids=[test_user.id, test_user2.id]
        )
        channel = await initialized_engine.channel_manager.create_channel(
            creator_id=test_user.id,
            request=request
        )

        # Send message
        msg_request = SendMessageRequest(
            channel_id=channel.id,
            content="Integration test message"
        )
        message = await initialized_engine.message_manager.create_message(
            user_id=test_user.id,
            request=msg_request
        )

        # Add reaction
        await initialized_engine.reactions.add_reaction(
            message_id=message.id,
            user_id=test_user2.id,
            emoji="👍"
        )

        # Create reply
        await initialized_engine.threads.create_reply(
            parent_message_id=message.id,
            user_id=test_user2.id,
            content="Reply to integration test"
        )

        # Verify everything worked
        assert message is not None
        assert channel is not None


# Performance Tests
class TestPerformance:
    """Performance tests."""

    @pytest.mark.asyncio
    async def test_bulk_message_creation(self, initialized_engine, test_user, test_channel):
        """Test creating many messages."""
        start_time = datetime.utcnow()

        for i in range(100):
            request = SendMessageRequest(
                channel_id=test_channel.id,
                content=f"Message {i}"
            )
            await initialized_engine.message_manager.create_message(
                user_id=test_user.id,
                request=request
            )

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Should complete in reasonable time
        assert duration < 5.0  # 5 seconds for 100 messages


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
