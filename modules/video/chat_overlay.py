"""
NEXUS Chat Overlay Module - In-Meeting Chat with Private Messaging and File Sharing
Supports public chat, private messages, and file transfers
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Callable, Set
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of chat messages"""
    TEXT = "text"
    FILE = "file"
    IMAGE = "image"
    EMOJI = "emoji"
    LINK = "link"
    SYSTEM = "system"


class ChatScope(Enum):
    """Chat message scope"""
    PUBLIC = "public"  # Everyone in conference
    PRIVATE = "private"  # Direct message
    BREAKOUT_ROOM = "breakout_room"  # Everyone in breakout room
    HOST_ONLY = "host_only"  # Only hosts/co-hosts


@dataclass
class FileAttachment:
    """Represents a file attachment"""
    id: str = field(default_factory=lambda: str(uuid4()))
    filename: str = ""
    file_size: int = 0
    file_type: str = ""
    file_path: Optional[Path] = None
    download_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    uploaded_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "filename": self.filename,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "download_url": self.download_url,
            "thumbnail_url": self.thumbnail_url,
            "uploaded_at": self.uploaded_at.isoformat(),
        }


@dataclass
class ChatMessage:
    """Represents a chat message"""
    id: str = field(default_factory=lambda: str(uuid4()))
    sender_id: str = ""
    sender_name: str = ""
    message_type: MessageType = MessageType.TEXT
    scope: ChatScope = ChatScope.PUBLIC
    recipient_id: Optional[str] = None  # For private messages
    recipient_name: Optional[str] = None
    content: str = ""
    attachments: List[FileAttachment] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    edited_at: Optional[datetime] = None
    is_deleted: bool = False
    reactions: Dict[str, List[str]] = field(default_factory=dict)  # emoji -> [user_ids]
    reply_to: Optional[str] = None  # Message ID being replied to
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "sender_name": self.sender_name,
            "message_type": self.message_type.value,
            "scope": self.scope.value,
            "recipient_id": self.recipient_id,
            "recipient_name": self.recipient_name,
            "content": self.content if not self.is_deleted else "[Message deleted]",
            "attachments": [a.to_dict() for a in self.attachments],
            "timestamp": self.timestamp.isoformat(),
            "edited_at": self.edited_at.isoformat() if self.edited_at else None,
            "is_deleted": self.is_deleted,
            "reactions": self.reactions,
            "reply_to": self.reply_to,
        }


class ChatHistory:
    """
    Manages chat history for a conference
    """

    def __init__(self, conference_id: str):
        self.conference_id = conference_id
        self.messages: Dict[str, ChatMessage] = {}
        self.message_order: List[str] = []  # For chronological ordering

        # Filters
        self.public_messages: List[str] = []
        self.private_messages: Dict[str, List[str]] = {}  # participant_id -> message_ids

        logger.info(f"ChatHistory initialized for conference: {conference_id}")

    def add_message(self, message: ChatMessage) -> None:
        """Add a message to history"""
        self.messages[message.id] = message
        self.message_order.append(message.id)

        # Update filters
        if message.scope == ChatScope.PUBLIC:
            self.public_messages.append(message.id)
        elif message.scope == ChatScope.PRIVATE:
            # Add to both sender and recipient's private messages
            if message.sender_id not in self.private_messages:
                self.private_messages[message.sender_id] = []
            self.private_messages[message.sender_id].append(message.id)

            if message.recipient_id:
                if message.recipient_id not in self.private_messages:
                    self.private_messages[message.recipient_id] = []
                self.private_messages[message.recipient_id].append(message.id)

    def get_message(self, message_id: str) -> Optional[ChatMessage]:
        """Get a message by ID"""
        return self.messages.get(message_id)

    def get_all_messages(self) -> List[ChatMessage]:
        """Get all messages in chronological order"""
        return [self.messages[msg_id] for msg_id in self.message_order if msg_id in self.messages]

    def get_public_messages(self) -> List[ChatMessage]:
        """Get all public messages"""
        return [self.messages[msg_id] for msg_id in self.public_messages if msg_id in self.messages]

    def get_private_messages(self, participant_id: str) -> List[ChatMessage]:
        """Get all private messages for a participant"""
        message_ids = self.private_messages.get(participant_id, [])
        return [self.messages[msg_id] for msg_id in message_ids if msg_id in self.messages]

    def get_conversation(self, user1_id: str, user2_id: str) -> List[ChatMessage]:
        """Get conversation between two users"""
        messages = []
        for msg_id in self.message_order:
            if msg_id not in self.messages:
                continue

            msg = self.messages[msg_id]
            if msg.scope == ChatScope.PRIVATE:
                if (msg.sender_id == user1_id and msg.recipient_id == user2_id) or \
                   (msg.sender_id == user2_id and msg.recipient_id == user1_id):
                    messages.append(msg)

        return messages

    def search_messages(self, query: str) -> List[ChatMessage]:
        """Search messages by content"""
        query_lower = query.lower()
        results = []

        for message in self.get_all_messages():
            if not message.is_deleted and query_lower in message.content.lower():
                results.append(message)

        return results

    def get_stats(self) -> Dict:
        """Get chat statistics"""
        total_attachments = sum(len(msg.attachments) for msg in self.messages.values())

        return {
            "total_messages": len(self.messages),
            "public_messages": len(self.public_messages),
            "private_messages": sum(len(msgs) for msgs in self.private_messages.values()) // 2,  # Divide by 2 as each DM is counted twice
            "total_attachments": total_attachments,
        }


class Chat:
    """
    Main chat interface for a conference
    Handles sending, receiving, and managing chat messages
    """

    def __init__(self, conference_id: str):
        self.conference_id = conference_id
        self.history = ChatHistory(conference_id)

        # Settings
        self.enabled = True
        self.allow_private_messages = True
        self.allow_file_sharing = True
        self.max_file_size_mb = 100
        self.save_chat_on_end = True

        # Active participants
        self.participants: Set[str] = set()

        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {
            "message_sent": [],
            "message_edited": [],
            "message_deleted": [],
            "message_reaction_added": [],
            "file_shared": [],
        }

        logger.info(f"Chat initialized for conference: {conference_id}")

    def send_message(
        self,
        sender_id: str,
        sender_name: str,
        content: str,
        scope: ChatScope = ChatScope.PUBLIC,
        recipient_id: Optional[str] = None,
        recipient_name: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> ChatMessage:
        """Send a chat message"""

        if not self.enabled:
            raise ValueError("Chat is disabled")

        if scope == ChatScope.PRIVATE and not self.allow_private_messages:
            raise ValueError("Private messages are not allowed")

        message = ChatMessage(
            sender_id=sender_id,
            sender_name=sender_name,
            content=content,
            scope=scope,
            recipient_id=recipient_id,
            recipient_name=recipient_name,
            reply_to=reply_to,
        )

        self.history.add_message(message)

        self._trigger_event("message_sent", message.to_dict())

        logger.debug(f"Message sent by {sender_name}: {content[:50]}...")
        return message

    def send_system_message(self, content: str) -> ChatMessage:
        """Send a system message"""
        message = ChatMessage(
            sender_id="system",
            sender_name="System",
            message_type=MessageType.SYSTEM,
            scope=ChatScope.PUBLIC,
            content=content,
        )

        self.history.add_message(message)
        self._trigger_event("message_sent", message.to_dict())

        logger.info(f"System message sent: {content}")
        return message

    def send_file(
        self,
        sender_id: str,
        sender_name: str,
        file_path: Path,
        scope: ChatScope = ChatScope.PUBLIC,
        recipient_id: Optional[str] = None,
        recipient_name: Optional[str] = None,
    ) -> ChatMessage:
        """Send a file"""

        if not self.allow_file_sharing:
            raise ValueError("File sharing is not allowed")

        # Check file size
        file_size = file_path.stat().st_size if file_path.exists() else 0
        max_size = self.max_file_size_mb * 1024 * 1024

        if file_size > max_size:
            raise ValueError(f"File size exceeds maximum of {self.max_file_size_mb}MB")

        # Create attachment
        attachment = FileAttachment(
            filename=file_path.name,
            file_size=file_size,
            file_type=file_path.suffix,
            file_path=file_path,
        )

        # Determine message type
        message_type = MessageType.FILE
        if file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            message_type = MessageType.IMAGE

        message = ChatMessage(
            sender_id=sender_id,
            sender_name=sender_name,
            message_type=message_type,
            scope=scope,
            recipient_id=recipient_id,
            recipient_name=recipient_name,
            content=f"Shared file: {file_path.name}",
            attachments=[attachment],
        )

        self.history.add_message(message)

        self._trigger_event("file_shared", {
            **message.to_dict(),
            "file_info": attachment.to_dict(),
        })

        logger.info(f"File shared by {sender_name}: {file_path.name}")
        return message

    def edit_message(
        self,
        message_id: str,
        new_content: str,
        editor_id: str,
    ) -> bool:
        """Edit a message"""
        message = self.history.get_message(message_id)
        if not message:
            return False

        # Only sender can edit
        if message.sender_id != editor_id:
            return False

        # Cannot edit deleted messages
        if message.is_deleted:
            return False

        message.content = new_content
        message.edited_at = datetime.now()

        self._trigger_event("message_edited", message.to_dict())

        logger.debug(f"Message edited: {message_id}")
        return True

    def delete_message(
        self,
        message_id: str,
        deleter_id: str,
        is_host: bool = False,
    ) -> bool:
        """Delete a message"""
        message = self.history.get_message(message_id)
        if not message:
            return False

        # Only sender or host can delete
        if message.sender_id != deleter_id and not is_host:
            return False

        message.is_deleted = True
        message.content = "[Message deleted]"

        self._trigger_event("message_deleted", {
            "message_id": message_id,
            "deleted_by": deleter_id,
        })

        logger.debug(f"Message deleted: {message_id}")
        return True

    def add_reaction(
        self,
        message_id: str,
        emoji: str,
        user_id: str,
    ) -> bool:
        """Add a reaction to a message"""
        message = self.history.get_message(message_id)
        if not message or message.is_deleted:
            return False

        if emoji not in message.reactions:
            message.reactions[emoji] = []

        if user_id not in message.reactions[emoji]:
            message.reactions[emoji].append(user_id)

            self._trigger_event("message_reaction_added", {
                "message_id": message_id,
                "emoji": emoji,
                "user_id": user_id,
            })

            logger.debug(f"Reaction added to message {message_id}: {emoji}")
            return True

        return False

    def remove_reaction(
        self,
        message_id: str,
        emoji: str,
        user_id: str,
    ) -> bool:
        """Remove a reaction from a message"""
        message = self.history.get_message(message_id)
        if not message:
            return False

        if emoji in message.reactions and user_id in message.reactions[emoji]:
            message.reactions[emoji].remove(user_id)

            if not message.reactions[emoji]:
                del message.reactions[emoji]

            logger.debug(f"Reaction removed from message {message_id}: {emoji}")
            return True

        return False

    def get_messages(
        self,
        scope: Optional[ChatScope] = None,
        participant_id: Optional[str] = None,
    ) -> List[ChatMessage]:
        """Get messages filtered by scope and participant"""
        if scope == ChatScope.PUBLIC:
            return self.history.get_public_messages()
        elif scope == ChatScope.PRIVATE and participant_id:
            return self.history.get_private_messages(participant_id)
        else:
            return self.history.get_all_messages()

    def export_chat(self, file_path: Optional[Path] = None) -> str:
        """Export chat history to a file"""
        messages = self.history.get_all_messages()

        # Format messages as text
        lines = [f"Chat History - {self.conference_id}", "=" * 80, ""]

        for msg in messages:
            timestamp = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            if msg.scope == ChatScope.PRIVATE:
                header = f"[{timestamp}] {msg.sender_name} -> {msg.recipient_name} (Private)"
            else:
                header = f"[{timestamp}] {msg.sender_name}"

            lines.append(header)
            lines.append(msg.content)

            if msg.attachments:
                for att in msg.attachments:
                    lines.append(f"  📎 {att.filename} ({att.file_size} bytes)")

            lines.append("")

        content = "\n".join(lines)

        # Save to file if path provided
        if file_path:
            file_path.write_text(content)
            logger.info(f"Chat exported to: {file_path}")

        return content

    def clear_chat(self) -> int:
        """Clear all chat messages"""
        count = len(self.history.messages)
        self.history = ChatHistory(self.conference_id)
        logger.info(f"Cleared {count} chat messages")
        return count

    def on_event(self, event_name: str, callback: Callable) -> None:
        """Register an event handler"""
        if event_name in self.event_handlers:
            self.event_handlers[event_name].append(callback)

    def _trigger_event(self, event_name: str, data: Dict) -> None:
        """Trigger an event"""
        if event_name in self.event_handlers:
            for callback in self.event_handlers[event_name]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in event handler {event_name}: {e}")
