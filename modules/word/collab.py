"""
Collaborative features for Word Editor module.
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import difflib
from core.utils import get_timestamp, generate_document_id


@dataclass
class User:
    """Collaborative user."""
    id: str
    name: str
    color: str
    cursor_position: int = 0
    last_active: str = ""

    def __post_init__(self):
        if not self.last_active:
            self.last_active = get_timestamp()


@dataclass
class CollaborativeEdit:
    """Represents a collaborative edit."""
    user_id: str
    timestamp: str
    start_pos: int
    end_pos: int
    old_text: str
    new_text: str


class CollaborativeSession:
    """Manages collaborative editing session."""

    def __init__(self, document_id: str):
        """
        Initialize collaborative session.

        Args:
            document_id: Document ID
        """
        self.document_id = document_id
        self.active_users: Dict[str, User] = {}
        self.edit_history: List[CollaborativeEdit] = []
        self.cursor_positions: Dict[str, int] = {}

    def add_user(self, user_id: str, name: str, color: str) -> User:
        """
        Add a user to the session.

        Args:
            user_id: User ID
            name: User name
            color: Cursor color

        Returns:
            User object
        """
        user = User(
            id=user_id,
            name=name,
            color=color,
        )
        self.active_users[user_id] = user
        return user

    def remove_user(self, user_id: str) -> bool:
        """
        Remove a user from the session.

        Args:
            user_id: User ID

        Returns:
            True if successful
        """
        if user_id in self.active_users:
            del self.active_users[user_id]
            if user_id in self.cursor_positions:
                del self.cursor_positions[user_id]
            return True
        return False

    def update_cursor(self, user_id: str, position: int) -> None:
        """
        Update user cursor position.

        Args:
            user_id: User ID
            position: Cursor position
        """
        if user_id in self.active_users:
            self.active_users[user_id].cursor_position = position
            self.active_users[user_id].last_active = get_timestamp()
            self.cursor_positions[user_id] = position

    def record_edit(
        self,
        user_id: str,
        start_pos: int,
        end_pos: int,
        old_text: str,
        new_text: str,
    ) -> CollaborativeEdit:
        """
        Record an edit made by a user.

        Args:
            user_id: User ID
            start_pos: Start position
            end_pos: End position
            old_text: Old text
            new_text: New text

        Returns:
            CollaborativeEdit object
        """
        edit = CollaborativeEdit(
            user_id=user_id,
            timestamp=get_timestamp(),
            start_pos=start_pos,
            end_pos=end_pos,
            old_text=old_text,
            new_text=new_text,
        )
        self.edit_history.append(edit)
        return edit

    def get_active_users(self) -> List[User]:
        """
        Get list of active users.

        Returns:
            List of User objects
        """
        return list(self.active_users.values())

    def get_cursor_positions(self) -> Dict[str, Dict[str, any]]:
        """
        Get cursor positions for all users.

        Returns:
            Dictionary of user cursor info
        """
        cursors = {}
        for user_id, user in self.active_users.items():
            cursors[user_id] = {
                "name": user.name,
                "color": user.color,
                "position": user.cursor_position,
            }
        return cursors


class VersionDiff:
    """Generate diffs between document versions."""

    @staticmethod
    def generate_diff(old_text: str, new_text: str) -> List[Tuple[str, str]]:
        """
        Generate a diff between two text versions.

        Args:
            old_text: Old version
            new_text: New version

        Returns:
            List of tuples (change_type, line) where change_type is '+', '-', or ' '
        """
        old_lines = old_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)

        diff = list(difflib.unified_diff(old_lines, new_lines, lineterm=""))
        return diff

    @staticmethod
    def generate_html_diff(old_text: str, new_text: str) -> str:
        """
        Generate an HTML diff view.

        Args:
            old_text: Old version
            new_text: New version

        Returns:
            HTML string
        """
        differ = difflib.HtmlDiff()
        old_lines = old_text.splitlines()
        new_lines = new_text.splitlines()

        html = differ.make_table(
            old_lines,
            new_lines,
            fromdesc="Previous Version",
            todesc="Current Version",
            context=True,
            numlines=3,
        )
        return html

    @staticmethod
    def get_change_summary(old_text: str, new_text: str) -> Dict[str, int]:
        """
        Get a summary of changes between versions.

        Args:
            old_text: Old version
            new_text: New version

        Returns:
            Dictionary with change statistics
        """
        old_lines = old_text.splitlines()
        new_lines = new_text.splitlines()

        diff = list(difflib.unified_diff(old_lines, new_lines))

        additions = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
        deletions = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))

        return {
            "additions": additions,
            "deletions": deletions,
            "total_changes": additions + deletions,
        }

    @staticmethod
    def get_inline_diff(old_text: str, new_text: str) -> str:
        """
        Generate inline diff with markup.

        Args:
            old_text: Old version
            new_text: New version

        Returns:
            Marked up text
        """
        old_words = old_text.split()
        new_words = new_text.split()

        differ = difflib.SequenceMatcher(None, old_words, new_words)
        result = []

        for tag, i1, i2, j1, j2 in differ.get_opcodes():
            if tag == "equal":
                result.extend(old_words[i1:i2])
            elif tag == "delete":
                for word in old_words[i1:i2]:
                    result.append(f"~~{word}~~")
            elif tag == "insert":
                for word in new_words[j1:j2]:
                    result.append(f"**{word}**")
            elif tag == "replace":
                for word in old_words[i1:i2]:
                    result.append(f"~~{word}~~")
                for word in new_words[j1:j2]:
                    result.append(f"**{word}**")

        return " ".join(result)


class SuggestionMode:
    """Manage document suggestions and tracked changes."""

    def __init__(self):
        """Initialize suggestion mode."""
        self.suggestions: List[Dict[str, any]] = []
        self.enabled = False

    def enable(self) -> None:
        """Enable suggestion mode."""
        self.enabled = True

    def disable(self) -> None:
        """Disable suggestion mode."""
        self.enabled = False

    def add_suggestion(
        self,
        user_id: str,
        user_name: str,
        change_type: str,
        start_pos: int,
        end_pos: int,
        text: str,
    ) -> Dict[str, any]:
        """
        Add a suggestion.

        Args:
            user_id: User ID
            user_name: User name
            change_type: Type of change (insert, delete, replace)
            start_pos: Start position
            end_pos: End position
            text: Suggested text

        Returns:
            Suggestion dictionary
        """
        suggestion = {
            "id": generate_document_id(),
            "user_id": user_id,
            "user_name": user_name,
            "change_type": change_type,
            "start_pos": start_pos,
            "end_pos": end_pos,
            "text": text,
            "timestamp": get_timestamp(),
            "status": "pending",  # pending, accepted, rejected
        }
        self.suggestions.append(suggestion)
        return suggestion

    def accept_suggestion(self, suggestion_id: str) -> Optional[Dict[str, any]]:
        """
        Accept a suggestion.

        Args:
            suggestion_id: Suggestion ID

        Returns:
            Suggestion dictionary or None
        """
        for suggestion in self.suggestions:
            if suggestion["id"] == suggestion_id:
                suggestion["status"] = "accepted"
                return suggestion
        return None

    def reject_suggestion(self, suggestion_id: str) -> Optional[Dict[str, any]]:
        """
        Reject a suggestion.

        Args:
            suggestion_id: Suggestion ID

        Returns:
            Suggestion dictionary or None
        """
        for suggestion in self.suggestions:
            if suggestion["id"] == suggestion_id:
                suggestion["status"] = "rejected"
                return suggestion
        return None

    def get_pending_suggestions(self) -> List[Dict[str, any]]:
        """
        Get all pending suggestions.

        Returns:
            List of pending suggestions
        """
        return [s for s in self.suggestions if s["status"] == "pending"]

    def apply_accepted_suggestions(self, text: str) -> str:
        """
        Apply all accepted suggestions to text.

        Args:
            text: Original text

        Returns:
            Modified text
        """
        accepted = [s for s in self.suggestions if s["status"] == "accepted"]
        # Sort by position (reverse order to maintain positions)
        accepted.sort(key=lambda s: s["start_pos"], reverse=True)

        for suggestion in accepted:
            if suggestion["change_type"] == "insert":
                text = text[:suggestion["start_pos"]] + suggestion["text"] + text[suggestion["start_pos"]:]
            elif suggestion["change_type"] == "delete":
                text = text[:suggestion["start_pos"]] + text[suggestion["end_pos"]:]
            elif suggestion["change_type"] == "replace":
                text = text[:suggestion["start_pos"]] + suggestion["text"] + text[suggestion["end_pos"]:]

        return text

    def clear_processed_suggestions(self) -> None:
        """Remove all accepted and rejected suggestions."""
        self.suggestions = [s for s in self.suggestions if s["status"] == "pending"]
