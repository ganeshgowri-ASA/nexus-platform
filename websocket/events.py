"""
WebSocket Event Types and Models

Defines all event types and data structures for WebSocket communication.
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class EventType(str, Enum):
    """WebSocket event types"""

    # Connection events
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"

    # Chat events
    CHAT_MESSAGE = "chat.message"
    CHAT_TYPING = "chat.typing"
    CHAT_READ = "chat.read"
    CHAT_DELIVERED = "chat.delivered"
    CHAT_EDIT = "chat.edit"
    CHAT_DELETE = "chat.delete"

    # Document events
    DOC_OPEN = "doc.open"
    DOC_CLOSE = "doc.close"
    DOC_EDIT = "doc.edit"
    DOC_CURSOR = "doc.cursor"
    DOC_SELECTION = "doc.selection"
    DOC_SAVE = "doc.save"
    DOC_CONFLICT = "doc.conflict"

    # Notification events
    NOTIFICATION = "notification"
    NOTIFICATION_READ = "notification.read"
    NOTIFICATION_CLEAR = "notification.clear"

    # Presence events
    PRESENCE_ONLINE = "presence.online"
    PRESENCE_OFFLINE = "presence.offline"
    PRESENCE_AWAY = "presence.away"
    PRESENCE_BUSY = "presence.busy"
    PRESENCE_UPDATE = "presence.update"

    # Room/Channel events
    ROOM_JOIN = "room.join"
    ROOM_LEAVE = "room.leave"
    ROOM_BROADCAST = "room.broadcast"

    # System events
    SYSTEM_MESSAGE = "system.message"
    SYSTEM_MAINTENANCE = "system.maintenance"
    SYSTEM_ALERT = "system.alert"


class WebSocketEvent(BaseModel):
    """Base WebSocket event model"""

    event_type: EventType
    event_id: str = Field(default_factory=lambda: f"evt_{datetime.utcnow().timestamp()}")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sender_id: Optional[str] = None
    room_id: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChatEvent(BaseModel):
    """Chat message event"""

    message_id: str
    conversation_id: str
    sender_id: str
    content: str
    content_type: str = "text"  # text, image, file, audio, video
    reply_to: Optional[str] = None
    mentions: List[str] = Field(default_factory=list)
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    edited: bool = False
    deleted: bool = False

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TypingEvent(BaseModel):
    """Typing indicator event"""

    conversation_id: str
    user_id: str
    username: str
    is_typing: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ReadReceiptEvent(BaseModel):
    """Read receipt event"""

    conversation_id: str
    message_id: str
    user_id: str
    read_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DocumentEvent(BaseModel):
    """Collaborative document event"""

    document_id: str
    user_id: str
    username: str
    operation: str  # insert, delete, replace, format
    version: int
    changes: List[Dict[str, Any]] = Field(default_factory=list)
    cursor_position: Optional[Dict[str, int]] = None
    selection: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DocumentCursor(BaseModel):
    """Document cursor position"""

    document_id: str
    user_id: str
    username: str
    color: str  # User-specific cursor color
    position: Dict[str, int]  # line, column
    selection: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class NotificationEvent(BaseModel):
    """Notification event"""

    notification_id: str
    user_id: str
    title: str
    message: str
    notification_type: str  # info, success, warning, error
    priority: str = "normal"  # low, normal, high, urgent
    action_url: Optional[str] = None
    action_label: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    read: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PresenceEvent(BaseModel):
    """User presence event"""

    user_id: str
    username: str
    status: str  # online, offline, away, busy
    status_message: Optional[str] = None
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    device_info: Optional[Dict[str, str]] = None
    location: Optional[str] = None  # Current page/module

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RoomEvent(BaseModel):
    """Room/Channel event"""

    room_id: str
    user_id: str
    username: str
    action: str  # join, leave
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SystemEvent(BaseModel):
    """System-level event"""

    message: str
    event_type: str  # message, maintenance, alert
    severity: str = "info"  # info, warning, critical
    affected_services: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    estimated_duration: Optional[int] = None  # minutes

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
