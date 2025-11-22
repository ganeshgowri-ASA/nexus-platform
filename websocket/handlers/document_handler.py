"""
Document Handler

Handles collaborative document editing with CRDT-ready architecture.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from collections import defaultdict

from ..events import (
    EventType,
    WebSocketEvent,
    DocumentEvent,
    DocumentCursor,
)

logger = logging.getLogger(__name__)


class DocumentSession:
    """Represents a collaborative editing session for a document"""

    def __init__(self, document_id: str):
        self.document_id = document_id
        self.created_at = datetime.utcnow()
        self.active_users: Set[str] = set()
        self.user_cursors: Dict[str, DocumentCursor] = {}  # user_id -> cursor
        self.version = 0
        self.pending_operations: List[Dict[str, Any]] = []
        self.user_colors: Dict[str, str] = {}  # user_id -> color

    def add_user(self, user_id: str, username: str, color: str):
        """Add user to editing session"""
        self.active_users.add(user_id)
        self.user_colors[user_id] = color

    def remove_user(self, user_id: str):
        """Remove user from editing session"""
        self.active_users.discard(user_id)
        self.user_cursors.pop(user_id, None)

    def update_cursor(self, cursor: DocumentCursor):
        """Update user's cursor position"""
        self.user_cursors[cursor.user_id] = cursor

    def increment_version(self):
        """Increment document version"""
        self.version += 1
        return self.version


class DocumentHandler:
    """
    Handles collaborative document editing events:
    - Real-time document synchronization
    - Cursor tracking and selection sharing
    - Operation transformation (CRDT-ready)
    - Conflict resolution
    - Version management
    """

    def __init__(self, connection_manager):
        self.connection_manager = connection_manager

        # Document sessions
        self.sessions: Dict[str, DocumentSession] = {}  # document_id -> DocumentSession

        # User color palette for cursors
        self.color_palette = [
            "#FF6B6B",
            "#4ECDC4",
            "#45B7D1",
            "#FFA07A",
            "#98D8C8",
            "#F7DC6F",
            "#BB8FCE",
            "#85C1E2",
            "#F8B739",
            "#52B788",
        ]
        self.color_index = 0

        # Operation history for conflict resolution
        self.operation_history: Dict[str, List[Dict[str, Any]]] = defaultdict(
            list
        )  # document_id -> operations
        self.max_history_size = 1000

        logger.info("DocumentHandler initialized")

    async def handle_open(self, connection_id: str, user_id: str, data: Dict[str, Any]):
        """
        Handle document open event

        Args:
            connection_id: Connection ID
            user_id: User ID
            data: Document open data
        """
        try:
            document_id = data.get("document_id")
            username = data.get("username", "Unknown")

            if not document_id:
                return

            # Get or create session
            if document_id not in self.sessions:
                self.sessions[document_id] = DocumentSession(document_id)

            session = self.sessions[document_id]

            # Assign color to user
            color = self._assign_color(user_id)
            session.add_user(user_id, username, color)

            # Join document room
            room_id = f"doc_{document_id}"
            await self.connection_manager.join_room(connection_id, room_id)

            # Send current session state to new user
            await self._send_session_state(connection_id, session)

            # Notify other users
            ws_event = WebSocketEvent(
                event_type=EventType.DOC_OPEN,
                sender_id=user_id,
                room_id=room_id,
                data={
                    "document_id": document_id,
                    "user_id": user_id,
                    "username": username,
                    "color": color,
                    "version": session.version,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            await self.connection_manager.broadcast_to_room(
                room_id, ws_event.dict(), exclude={connection_id}
            )

            logger.info(
                f"User {user_id} opened document {document_id} "
                f"(active users: {len(session.active_users)})"
            )

        except Exception as e:
            logger.error(f"Error handling document open: {e}")

    async def handle_close(
        self, connection_id: str, user_id: str, data: Dict[str, Any]
    ):
        """
        Handle document close event

        Args:
            connection_id: Connection ID
            user_id: User ID
            data: Document close data
        """
        try:
            document_id = data.get("document_id")

            if not document_id or document_id not in self.sessions:
                return

            session = self.sessions[document_id]
            session.remove_user(user_id)

            # Leave document room
            room_id = f"doc_{document_id}"
            await self.connection_manager.leave_room(connection_id, room_id)

            # Notify other users
            ws_event = WebSocketEvent(
                event_type=EventType.DOC_CLOSE,
                sender_id=user_id,
                room_id=room_id,
                data={
                    "document_id": document_id,
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            await self.connection_manager.broadcast_to_room(room_id, ws_event.dict())

            # Cleanup empty session
            if not session.active_users:
                del self.sessions[document_id]
                logger.info(f"Document session {document_id} closed (no active users)")

            logger.info(
                f"User {user_id} closed document {document_id} "
                f"(remaining users: {len(session.active_users)})"
            )

        except Exception as e:
            logger.error(f"Error handling document close: {e}")

    async def handle_edit(self, connection_id: str, user_id: str, data: Dict[str, Any]):
        """
        Handle document edit event

        Args:
            connection_id: Connection ID
            user_id: User ID
            data: Edit data with operations
        """
        try:
            document_id = data.get("document_id")
            username = data.get("username", "Unknown")
            operation = data.get("operation")
            changes = data.get("changes", [])

            if not document_id or document_id not in self.sessions:
                return

            session = self.sessions[document_id]

            # Increment version
            new_version = session.increment_version()

            # Create document event
            doc_event = DocumentEvent(
                document_id=document_id,
                user_id=user_id,
                username=username,
                operation=operation,
                version=new_version,
                changes=changes,
                cursor_position=data.get("cursor_position"),
                selection=data.get("selection"),
            )

            # Store operation in history
            self._store_operation(document_id, doc_event.dict())

            # Create WebSocket event
            ws_event = WebSocketEvent(
                event_type=EventType.DOC_EDIT,
                sender_id=user_id,
                room_id=f"doc_{document_id}",
                data=doc_event.dict(),
            )

            # Broadcast to all users (including sender for confirmation)
            room_id = f"doc_{document_id}"
            await self.connection_manager.broadcast_to_room(room_id, ws_event.dict())

            logger.debug(
                f"Document {document_id} edited by {user_id} "
                f"(operation: {operation}, version: {new_version})"
            )

        except Exception as e:
            logger.error(f"Error handling document edit: {e}")

    async def handle_cursor(
        self, connection_id: str, user_id: str, data: Dict[str, Any]
    ):
        """
        Handle cursor position update

        Args:
            connection_id: Connection ID
            user_id: User ID
            data: Cursor data
        """
        try:
            document_id = data.get("document_id")
            username = data.get("username", "Unknown")
            position = data.get("position")

            if not document_id or not position or document_id not in self.sessions:
                return

            session = self.sessions[document_id]

            # Get user color
            color = session.user_colors.get(user_id, self._assign_color(user_id))

            # Create cursor event
            cursor = DocumentCursor(
                document_id=document_id,
                user_id=user_id,
                username=username,
                color=color,
                position=position,
                selection=data.get("selection"),
            )

            # Update session cursor
            session.update_cursor(cursor)

            # Create WebSocket event
            ws_event = WebSocketEvent(
                event_type=EventType.DOC_CURSOR,
                sender_id=user_id,
                room_id=f"doc_{document_id}",
                data=cursor.dict(),
            )

            # Broadcast to other users
            room_id = f"doc_{document_id}"
            await self.connection_manager.broadcast_to_room(
                room_id, ws_event.dict(), exclude={connection_id}
            )

        except Exception as e:
            logger.error(f"Error handling cursor update: {e}")

    async def handle_save(self, connection_id: str, user_id: str, data: Dict[str, Any]):
        """
        Handle document save event

        Args:
            connection_id: Connection ID
            user_id: User ID
            data: Save data
        """
        try:
            document_id = data.get("document_id")

            if not document_id or document_id not in self.sessions:
                return

            session = self.sessions[document_id]

            # Create WebSocket event
            ws_event = WebSocketEvent(
                event_type=EventType.DOC_SAVE,
                sender_id=user_id,
                room_id=f"doc_{document_id}",
                data={
                    "document_id": document_id,
                    "user_id": user_id,
                    "version": session.version,
                    "saved_at": datetime.utcnow().isoformat(),
                },
            )

            # Notify all users
            room_id = f"doc_{document_id}"
            await self.connection_manager.broadcast_to_room(room_id, ws_event.dict())

            logger.info(
                f"Document {document_id} saved by {user_id} (version: {session.version})"
            )

        except Exception as e:
            logger.error(f"Error handling document save: {e}")

    async def _send_session_state(self, connection_id: str, session: DocumentSession):
        """Send current session state to a user"""
        state_data = {
            "document_id": session.document_id,
            "version": session.version,
            "active_users": [
                {
                    "user_id": uid,
                    "color": session.user_colors.get(uid),
                }
                for uid in session.active_users
            ],
            "cursors": [cursor.dict() for cursor in session.user_cursors.values()],
        }

        ws_event = WebSocketEvent(
            event_type=EventType.SYSTEM_MESSAGE,
            sender_id="system",
            data={"session_state": state_data},
        )

        await self.connection_manager.send_to_connection(
            connection_id, ws_event.dict()
        )

    def _assign_color(self, user_id: str) -> str:
        """Assign a color to a user for cursor display"""
        color = self.color_palette[self.color_index % len(self.color_palette)]
        self.color_index += 1
        return color

    def _store_operation(self, document_id: str, operation: Dict[str, Any]):
        """Store operation in history for conflict resolution"""
        history = self.operation_history[document_id]
        history.append(operation)

        # Limit history size
        if len(history) > self.max_history_size:
            history.pop(0)

    def get_document_session(self, document_id: str) -> Optional[DocumentSession]:
        """Get active document session"""
        return self.sessions.get(document_id)

    def get_active_documents(self) -> List[str]:
        """Get list of documents with active editing sessions"""
        return list(self.sessions.keys())

    def get_operation_history(
        self, document_id: str, since_version: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get operation history for a document

        Args:
            document_id: Document ID
            since_version: Optional version to get operations since

        Returns:
            List of operations
        """
        history = self.operation_history.get(document_id, [])

        if since_version is not None:
            history = [op for op in history if op.get("version", 0) > since_version]

        return history
