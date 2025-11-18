"""
NEXUS Chat & Messaging Module

A comprehensive real-time chat and messaging system with WebSocket support,
AI features, and a beautiful Streamlit UI.

Features:
- Real-time messaging with WebSocket
- Direct messages and group chats
- Channels and workspaces
- File sharing and media support
- Emoji reactions and threads
- Full-text search
- AI-powered features
- Push notifications
- Rich Streamlit UI

Author: NEXUS Platform
Version: 1.0.0
"""

from typing import Optional
import logging

# Module metadata
__version__ = "1.0.0"
__author__ = "NEXUS Platform"
__all__ = [
    "ChatEngine",
    "WebSocketHandler",
    "MessageManager",
    "ChannelManager",
    "DirectMessaging",
    "GroupChat",
    "FileSharing",
    "Reactions",
    "Threads",
    "Search",
    "Notifications",
    "AIFeatures",
    "StreamlitUI",
]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# Lazy imports to avoid circular dependencies
def get_chat_engine():
    """Get ChatEngine instance."""
    from .chat_engine import ChatEngine
    return ChatEngine()


def get_websocket_handler():
    """Get WebSocketHandler instance."""
    from .websocket_handler import WebSocketHandler
    return WebSocketHandler()


def get_message_manager():
    """Get MessageManager instance."""
    from .message_manager import MessageManager
    return MessageManager()


def get_channel_manager():
    """Get ChannelManager instance."""
    from .channel_manager import ChannelManager
    return ChannelManager()


def get_direct_messaging():
    """Get DirectMessaging instance."""
    from .direct_messaging import DirectMessaging
    return DirectMessaging()


def get_group_chat():
    """Get GroupChat instance."""
    from .group_chat import GroupChat
    return GroupChat()


def get_file_sharing():
    """Get FileSharing instance."""
    from .file_sharing import FileSharing
    return FileSharing()


def get_reactions():
    """Get Reactions instance."""
    from .reactions import Reactions
    return Reactions()


def get_threads():
    """Get Threads instance."""
    from .threads import Threads
    return Threads()


def get_search():
    """Get Search instance."""
    from .search import Search
    return Search()


def get_notifications():
    """Get Notifications instance."""
    from .notifications import Notifications
    return Notifications()


def get_ai_features():
    """Get AIFeatures instance."""
    from .ai_features import AIFeatures
    return AIFeatures()


def launch_ui(port: int = 8501, host: str = "localhost") -> None:
    """
    Launch the Streamlit UI for the chat module.

    Args:
        port: Port to run the Streamlit app on
        host: Host to bind to
    """
    logger.info(f"Launching Chat UI on {host}:{port}")
    from .streamlit_ui import main
    main()


# Module initialization
logger.info(f"NEXUS Chat Module v{__version__} initialized")
