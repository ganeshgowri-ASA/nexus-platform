"""Collaboration features for multi-user spreadsheet editing."""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json


class ChangeType(Enum):
    """Types of changes."""
    CELL_VALUE = "cell_value"
    CELL_STYLE = "cell_style"
    CELL_FORMULA = "cell_formula"
    INSERT_ROW = "insert_row"
    INSERT_COLUMN = "insert_column"
    DELETE_ROW = "delete_row"
    DELETE_COLUMN = "delete_column"
    MERGE_CELLS = "merge_cells"
    UNMERGE_CELLS = "unmerge_cells"


@dataclass
class Change:
    """Represents a single change."""

    change_id: str
    user_id: int
    user_name: str
    change_type: ChangeType
    timestamp: datetime
    row: Optional[int] = None
    col: Optional[int] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'change_id': self.change_id,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'change_type': self.change_type.value,
            'timestamp': self.timestamp.isoformat(),
            'row': self.row,
            'col': self.col,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Change':
        """Create from dictionary."""
        return cls(
            change_id=data['change_id'],
            user_id=data['user_id'],
            user_name=data['user_name'],
            change_type=ChangeType(data['change_type']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            row=data.get('row'),
            col=data.get('col'),
            old_value=data.get('old_value'),
            new_value=data.get('new_value'),
            metadata=data.get('metadata')
        )


@dataclass
class Comment:
    """Cell comment."""

    comment_id: str
    row: int
    col: int
    user_id: int
    user_name: str
    text: str
    created_at: datetime
    resolved: bool = False
    replies: List['CommentReply'] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.replies is None:
            self.replies = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'comment_id': self.comment_id,
            'row': self.row,
            'col': self.col,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'text': self.text,
            'created_at': self.created_at.isoformat(),
            'resolved': self.resolved,
            'replies': [r.to_dict() for r in self.replies]
        }


@dataclass
class CommentReply:
    """Reply to a comment."""

    reply_id: str
    user_id: int
    user_name: str
    text: str
    created_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'reply_id': self.reply_id,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'text': self.text,
            'created_at': self.created_at.isoformat()
        }


class CollaborationManager:
    """Manage collaboration features."""

    def __init__(self, spreadsheet_id: int):
        """
        Initialize collaboration manager.

        Args:
            spreadsheet_id: Spreadsheet ID
        """
        self.spreadsheet_id = spreadsheet_id
        self.changes: List[Change] = []
        self.comments: Dict[tuple, Comment] = {}  # (row, col) -> Comment
        self.active_users: Dict[int, Dict[str, Any]] = {}  # user_id -> {name, cursor_pos}
        self.locked_cells: Dict[tuple, int] = {}  # (row, col) -> user_id

    def record_change(self, change: Change) -> None:
        """
        Record a change.

        Args:
            change: Change to record
        """
        self.changes.append(change)

        # Limit history size
        if len(self.changes) > 1000:
            self.changes = self.changes[-1000:]

    def get_change_history(self, limit: Optional[int] = None) -> List[Change]:
        """
        Get change history.

        Args:
            limit: Maximum number of changes to return

        Returns:
            List of changes
        """
        if limit:
            return self.changes[-limit:]
        return self.changes.copy()

    def add_comment(self, comment: Comment) -> None:
        """
        Add a comment to a cell.

        Args:
            comment: Comment to add
        """
        self.comments[(comment.row, comment.col)] = comment

    def get_comment(self, row: int, col: int) -> Optional[Comment]:
        """
        Get comment for a cell.

        Args:
            row: Row index
            col: Column index

        Returns:
            Comment if exists, None otherwise
        """
        return self.comments.get((row, col))

    def resolve_comment(self, row: int, col: int) -> bool:
        """
        Resolve a comment.

        Args:
            row: Row index
            col: Column index

        Returns:
            bool: True if comment was resolved
        """
        comment = self.get_comment(row, col)
        if comment:
            comment.resolved = True
            return True
        return False

    def add_comment_reply(self, row: int, col: int, reply: CommentReply) -> bool:
        """
        Add reply to a comment.

        Args:
            row: Row index
            col: Column index
            reply: Reply to add

        Returns:
            bool: True if reply was added
        """
        comment = self.get_comment(row, col)
        if comment:
            comment.replies.append(reply)
            return True
        return False

    def lock_cell(self, row: int, col: int, user_id: int) -> bool:
        """
        Lock a cell for editing by a user.

        Args:
            row: Row index
            col: Column index
            user_id: User ID

        Returns:
            bool: True if cell was locked
        """
        cell_key = (row, col)

        # Check if already locked by another user
        if cell_key in self.locked_cells and self.locked_cells[cell_key] != user_id:
            return False

        self.locked_cells[cell_key] = user_id
        return True

    def unlock_cell(self, row: int, col: int, user_id: int) -> bool:
        """
        Unlock a cell.

        Args:
            row: Row index
            col: Column index
            user_id: User ID

        Returns:
            bool: True if cell was unlocked
        """
        cell_key = (row, col)

        if cell_key in self.locked_cells and self.locked_cells[cell_key] == user_id:
            del self.locked_cells[cell_key]
            return True

        return False

    def is_cell_locked(self, row: int, col: int, user_id: Optional[int] = None) -> bool:
        """
        Check if cell is locked.

        Args:
            row: Row index
            col: Column index
            user_id: Optional user ID to check if locked by another user

        Returns:
            bool: True if cell is locked
        """
        cell_key = (row, col)

        if cell_key not in self.locked_cells:
            return False

        if user_id is None:
            return True

        return self.locked_cells[cell_key] != user_id

    def add_active_user(self, user_id: int, user_name: str,
                       cursor_pos: Optional[tuple] = None) -> None:
        """
        Add an active user.

        Args:
            user_id: User ID
            user_name: User name
            cursor_pos: Optional cursor position (row, col)
        """
        self.active_users[user_id] = {
            'name': user_name,
            'cursor_pos': cursor_pos,
            'last_seen': datetime.now()
        }

    def remove_active_user(self, user_id: int) -> None:
        """
        Remove an active user.

        Args:
            user_id: User ID
        """
        if user_id in self.active_users:
            del self.active_users[user_id]

            # Unlock all cells locked by this user
            cells_to_unlock = [
                cell_key for cell_key, uid in self.locked_cells.items()
                if uid == user_id
            ]
            for cell_key in cells_to_unlock:
                del self.locked_cells[cell_key]

    def update_user_cursor(self, user_id: int, cursor_pos: tuple) -> None:
        """
        Update user's cursor position.

        Args:
            user_id: User ID
            cursor_pos: Cursor position (row, col)
        """
        if user_id in self.active_users:
            self.active_users[user_id]['cursor_pos'] = cursor_pos
            self.active_users[user_id]['last_seen'] = datetime.now()

    def get_active_users(self) -> List[Dict[str, Any]]:
        """
        Get list of active users.

        Returns:
            List of active user info
        """
        return [
            {
                'user_id': user_id,
                'name': info['name'],
                'cursor_pos': info['cursor_pos'],
                'last_seen': info['last_seen'].isoformat()
            }
            for user_id, info in self.active_users.items()
        ]

    def export_changes(self, filename: str) -> None:
        """
        Export change history to file.

        Args:
            filename: Output filename
        """
        data = [change.to_dict() for change in self.changes]
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

    def import_changes(self, filename: str) -> None:
        """
        Import change history from file.

        Args:
            filename: Input filename
        """
        with open(filename, 'r') as f:
            data = json.load(f)
            self.changes = [Change.from_dict(item) for item in data]
