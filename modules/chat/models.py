"""
Database models and schemas for the Chat module.

This module defines all data structures, Pydantic models, and database schemas
used throughout the chat system.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from uuid import UUID, uuid4


# Enums
class MessageType(str, Enum):
    """Types of messages."""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"
    VOICE = "voice"
    STICKER = "sticker"
    GIF = "gif"
    SYSTEM = "system"
    POLL = "poll"


class MessageStatus(str, Enum):
    """Message delivery status."""
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class ChannelType(str, Enum):
    """Types of channels."""
    PUBLIC = "public"
    PRIVATE = "private"
    DIRECT = "direct"
    GROUP = "group"
    ANNOUNCEMENT = "announcement"


class UserStatus(str, Enum):
    """User online status."""
    ONLINE = "online"
    OFFLINE = "offline"
    AWAY = "away"
    DO_NOT_DISTURB = "do_not_disturb"
    INVISIBLE = "invisible"


class MemberRole(str, Enum):
    """Member roles in channels/groups."""
    OWNER = "owner"
    ADMIN = "admin"
    MODERATOR = "moderator"
    MEMBER = "member"
    GUEST = "guest"


class NotificationType(str, Enum):
    """Types of notifications."""
    MESSAGE = "message"
    MENTION = "mention"
    REPLY = "reply"
    REACTION = "reaction"
    INVITE = "invite"
    SYSTEM = "system"


# Base Models
class User(BaseModel):
    """User model."""
    id: UUID = Field(default_factory=uuid4)
    username: str
    email: str
    display_name: str
    avatar_url: Optional[str] = None
    status: UserStatus = UserStatus.OFFLINE
    last_seen: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    preferences: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class Message(BaseModel):
    """Message model."""
    id: UUID = Field(default_factory=uuid4)
    channel_id: UUID
    user_id: UUID
    content: str
    message_type: MessageType = MessageType.TEXT
    status: MessageStatus = MessageStatus.SENT
    parent_id: Optional[UUID] = None  # For threading
    thread_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    is_edited: bool = False
    is_pinned: bool = False
    mentions: List[UUID] = Field(default_factory=list)
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class Channel(BaseModel):
    """Channel/Room model."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    channel_type: ChannelType
    creator_id: UUID
    avatar_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    is_archived: bool = False
    is_favorite: bool = False
    member_count: int = 0
    settings: Dict[str, Any] = Field(default_factory=dict)
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True


class ChannelMember(BaseModel):
    """Channel membership model."""
    id: UUID = Field(default_factory=uuid4)
    channel_id: UUID
    user_id: UUID
    role: MemberRole = MemberRole.MEMBER
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    last_read_at: Optional[datetime] = None
    is_muted: bool = False
    is_blocked: bool = False
    notification_settings: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class Reaction(BaseModel):
    """Reaction model."""
    id: UUID = Field(default_factory=uuid4)
    message_id: UUID
    user_id: UUID
    emoji: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Attachment(BaseModel):
    """File attachment model."""
    id: UUID = Field(default_factory=uuid4)
    message_id: UUID
    file_name: str
    file_type: str
    file_size: int
    file_url: str
    thumbnail_url: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Thread(BaseModel):
    """Message thread model."""
    id: UUID = Field(default_factory=uuid4)
    parent_message_id: UUID
    channel_id: UUID
    message_count: int = 0
    participant_ids: List[UUID] = Field(default_factory=list)
    last_reply_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Notification(BaseModel):
    """Notification model."""
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    notification_type: NotificationType
    title: str
    body: str
    data: Dict[str, Any] = Field(default_factory=dict)
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = None

    class Config:
        use_enum_values = True


class TypingIndicator(BaseModel):
    """Typing indicator model."""
    channel_id: UUID
    user_id: UUID
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Poll(BaseModel):
    """Poll model."""
    id: UUID = Field(default_factory=uuid4)
    message_id: UUID
    question: str
    options: List[Dict[str, Any]]
    votes: Dict[UUID, str] = Field(default_factory=dict)  # user_id -> option_id
    allow_multiple: bool = False
    is_anonymous: bool = False
    ends_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Request/Response Models
class SendMessageRequest(BaseModel):
    """Request to send a message."""
    channel_id: UUID
    content: str
    message_type: MessageType = MessageType.TEXT
    parent_id: Optional[UUID] = None
    mentions: List[UUID] = Field(default_factory=list)
    attachments: List[Dict[str, Any]] = Field(default_factory=list)


class CreateChannelRequest(BaseModel):
    """Request to create a channel."""
    name: str
    description: Optional[str] = None
    channel_type: ChannelType
    member_ids: List[UUID] = Field(default_factory=list)
    category: Optional[str] = None

    @validator('name')
    def validate_name(cls, v):
        """Validate channel name."""
        if len(v) < 1 or len(v) > 100:
            raise ValueError('Name must be 1-100 characters')
        return v


class UpdateChannelRequest(BaseModel):
    """Request to update a channel."""
    name: Optional[str] = None
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class SearchRequest(BaseModel):
    """Request to search messages."""
    query: str
    channel_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    message_type: Optional[MessageType] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 50
    offset: int = 0


class MessageReaction(BaseModel):
    """Message reaction summary."""
    emoji: str
    count: int
    users: List[UUID]
    has_reacted: bool = False


class MessageWithReactions(Message):
    """Message with reactions."""
    reactions: List[MessageReaction] = Field(default_factory=list)
    user: Optional[User] = None


class ChannelWithMembers(Channel):
    """Channel with member information."""
    members: List[ChannelMember] = Field(default_factory=list)
    unread_count: int = 0


class DirectMessageInfo(BaseModel):
    """Direct message conversation info."""
    id: UUID = Field(default_factory=uuid4)
    user1_id: UUID
    user2_id: UUID
    channel_id: UUID
    last_message: Optional[Message] = None
    unread_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


# WebSocket Models
class WSMessage(BaseModel):
    """WebSocket message wrapper."""
    type: str  # message, typing, status, reaction, etc.
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WSTypingEvent(BaseModel):
    """WebSocket typing event."""
    channel_id: UUID
    user_id: UUID
    username: str
    is_typing: bool


class WSStatusEvent(BaseModel):
    """WebSocket status event."""
    user_id: UUID
    status: UserStatus
    last_seen: Optional[datetime] = None


class WSReactionEvent(BaseModel):
    """WebSocket reaction event."""
    message_id: UUID
    user_id: UUID
    emoji: str
    action: str  # add or remove


# Database Schema (for PostgreSQL)
DATABASE_SCHEMA = """
-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    avatar_url TEXT,
    status VARCHAR(20) DEFAULT 'offline',
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    preferences JSONB DEFAULT '{}'::jsonb
);

-- Channels table
CREATE TABLE IF NOT EXISTS channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    channel_type VARCHAR(20) NOT NULL,
    creator_id UUID REFERENCES users(id),
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    is_archived BOOLEAN DEFAULT FALSE,
    is_favorite BOOLEAN DEFAULT FALSE,
    member_count INTEGER DEFAULT 0,
    settings JSONB DEFAULT '{}'::jsonb,
    category VARCHAR(50),
    tags TEXT[]
);

-- Channel members table
CREATE TABLE IF NOT EXISTS channel_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id UUID REFERENCES channels(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'member',
    joined_at TIMESTAMP DEFAULT NOW(),
    last_read_at TIMESTAMP,
    is_muted BOOLEAN DEFAULT FALSE,
    is_blocked BOOLEAN DEFAULT FALSE,
    notification_settings JSONB DEFAULT '{}'::jsonb,
    UNIQUE(channel_id, user_id)
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id UUID REFERENCES channels(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    content TEXT NOT NULL,
    message_type VARCHAR(20) DEFAULT 'text',
    status VARCHAR(20) DEFAULT 'sent',
    parent_id UUID REFERENCES messages(id),
    thread_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP,
    is_edited BOOLEAN DEFAULT FALSE,
    is_pinned BOOLEAN DEFAULT FALSE,
    mentions UUID[],
    attachments JSONB DEFAULT '[]'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Reactions table
CREATE TABLE IF NOT EXISTS reactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    emoji VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(message_id, user_id, emoji)
);

-- Attachments table
CREATE TABLE IF NOT EXISTS attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(100),
    file_size BIGINT,
    file_url TEXT NOT NULL,
    thumbnail_url TEXT,
    uploaded_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Threads table
CREATE TABLE IF NOT EXISTS threads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    channel_id UUID REFERENCES channels(id) ON DELETE CASCADE,
    message_count INTEGER DEFAULT 0,
    participant_ids UUID[],
    last_reply_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    notification_type VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    data JSONB DEFAULT '{}'::jsonb,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    read_at TIMESTAMP
);

-- Polls table
CREATE TABLE IF NOT EXISTS polls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    options JSONB NOT NULL,
    votes JSONB DEFAULT '{}'::jsonb,
    allow_multiple BOOLEAN DEFAULT FALSE,
    is_anonymous BOOLEAN DEFAULT FALSE,
    ends_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_messages_channel ON messages(channel_id);
CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_parent ON messages(parent_id);
CREATE INDEX IF NOT EXISTS idx_messages_content ON messages USING gin(to_tsvector('english', content));
CREATE INDEX IF NOT EXISTS idx_channel_members_channel ON channel_members(channel_id);
CREATE INDEX IF NOT EXISTS idx_channel_members_user ON channel_members(user_id);
CREATE INDEX IF NOT EXISTS idx_reactions_message ON reactions(message_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(user_id) WHERE is_read = FALSE;
"""
