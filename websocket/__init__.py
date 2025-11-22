"""
NEXUS Platform WebSocket Module

Real-time communication infrastructure for the NEXUS platform.
Provides WebSocket server, connection management, and event handlers.
"""

from .server import WebSocketServer
from .connection_manager import ConnectionManager
from .events import (
    EventType,
    WebSocketEvent,
    ChatEvent,
    DocumentEvent,
    NotificationEvent,
    PresenceEvent,
)

__all__ = [
    "WebSocketServer",
    "ConnectionManager",
    "EventType",
    "WebSocketEvent",
    "ChatEvent",
    "DocumentEvent",
    "NotificationEvent",
    "PresenceEvent",
]
