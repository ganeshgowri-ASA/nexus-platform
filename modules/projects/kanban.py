"""
NEXUS Kanban Board Module
Kanban board management with columns, swimlanes, and WIP limits.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import uuid


class KanbanColumn:
    """
    Represents a column in a Kanban board.

    Attributes:
        id: Unique column identifier
        name: Column name
        position: Column position (order)
        wip_limit: Work-in-progress limit (None = no limit)
        color: Column color
        is_done_column: Whether this column represents completed work
    """

    def __init__(
        self,
        name: str,
        position: int = 0,
        wip_limit: Optional[int] = None,
        color: str = "#0066cc",
        is_done_column: bool = False,
        column_id: Optional[str] = None
    ):
        """Initialize a Kanban column."""
        self.id: str = column_id or str(uuid.uuid4())
        self.name: str = name
        self.position: int = position
        self.wip_limit: Optional[int] = wip_limit
        self.color: str = color
        self.is_done_column: bool = is_done_column

    def to_dict(self) -> Dict[str, Any]:
        """Convert column to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "position": self.position,
            "wip_limit": self.wip_limit,
            "color": self.color,
            "is_done_column": self.is_done_column
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KanbanColumn':
        """Create column from dictionary."""
        return cls(
            column_id=data.get("id"),
            name=data["name"],
            position=data.get("position", 0),
            wip_limit=data.get("wip_limit"),
            color=data.get("color", "#0066cc"),
            is_done_column=data.get("is_done_column", False)
        )


class Swimlane:
    """
    Represents a swimlane in a Kanban board.

    Attributes:
        id: Unique swimlane identifier
        name: Swimlane name
        position: Swimlane position (order)
        color: Swimlane color
        criteria: Filter criteria for tasks
    """

    def __init__(
        self,
        name: str,
        position: int = 0,
        color: str = "#f0f0f0",
        criteria: Optional[Dict[str, Any]] = None,
        swimlane_id: Optional[str] = None
    ):
        """Initialize a swimlane."""
        self.id: str = swimlane_id or str(uuid.uuid4())
        self.name: str = name
        self.position: int = position
        self.color: str = color
        self.criteria: Dict[str, Any] = criteria or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert swimlane to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "position": self.position,
            "color": self.color,
            "criteria": self.criteria
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Swimlane':
        """Create swimlane from dictionary."""
        return cls(
            swimlane_id=data.get("id"),
            name=data["name"],
            position=data.get("position", 0),
            color=data.get("color", "#f0f0f0"),
            criteria=data.get("criteria", {})
        )


class KanbanCard:
    """
    Represents a card on a Kanban board (wraps a task).

    Attributes:
        task_id: Associated task ID
        column_id: Current column ID
        swimlane_id: Current swimlane ID (optional)
        position: Position within column
        labels: Card labels
        color: Card color
    """

    def __init__(
        self,
        task_id: str,
        column_id: str,
        swimlane_id: Optional[str] = None,
        position: int = 0,
        labels: Optional[List[str]] = None,
        color: Optional[str] = None
    ):
        """Initialize a Kanban card."""
        self.task_id: str = task_id
        self.column_id: str = column_id
        self.swimlane_id: Optional[str] = swimlane_id
        self.position: int = position
        self.labels: List[str] = labels or []
        self.color: Optional[str] = color

    def to_dict(self) -> Dict[str, Any]:
        """Convert card to dictionary."""
        return {
            "task_id": self.task_id,
            "column_id": self.column_id,
            "swimlane_id": self.swimlane_id,
            "position": self.position,
            "labels": self.labels,
            "color": self.color
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KanbanCard':
        """Create card from dictionary."""
        return cls(
            task_id=data["task_id"],
            column_id=data["column_id"],
            swimlane_id=data.get("swimlane_id"),
            position=data.get("position", 0),
            labels=data.get("labels", []),
            color=data.get("color")
        )


class KanbanBoard:
    """
    Represents a Kanban board.

    Attributes:
        id: Unique board identifier
        project_id: Associated project ID
        name: Board name
        description: Board description
        columns: List of columns
        swimlanes: List of swimlanes
        cards: Dictionary of cards (task_id -> KanbanCard)
        filters: Active filters
        settings: Board settings
    """

    def __init__(
        self,
        project_id: str,
        name: str,
        description: str = "",
        board_id: Optional[str] = None
    ):
        """Initialize a Kanban board."""
        self.id: str = board_id or str(uuid.uuid4())
        self.project_id: str = project_id
        self.name: str = name
        self.description: str = description
        self.columns: List[KanbanColumn] = []
        self.swimlanes: List[Swimlane] = []
        self.cards: Dict[str, KanbanCard] = {}
        self.filters: Dict[str, Any] = {}
        self.settings: Dict[str, Any] = {
            "show_wip_limits": True,
            "show_card_count": True,
            "auto_move_on_status": True
        }
        self.created_at: datetime = datetime.now()
        self.updated_at: datetime = datetime.now()

        # Initialize with default columns
        self._create_default_columns()

    def _create_default_columns(self) -> None:
        """Create default Kanban columns."""
        default_columns = [
            ("To Do", 0, "#6b7280", False),
            ("In Progress", 1, "#3b82f6", False),
            ("Review", 2, "#f59e0b", False),
            ("Done", 3, "#10b981", True)
        ]

        for name, pos, color, is_done in default_columns:
            self.add_column(name, position=pos, color=color, is_done_column=is_done)

    def add_column(
        self,
        name: str,
        position: Optional[int] = None,
        wip_limit: Optional[int] = None,
        color: str = "#0066cc",
        is_done_column: bool = False
    ) -> KanbanColumn:
        """
        Add a column to the board.

        Args:
            name: Column name
            position: Column position (None = append to end)
            wip_limit: WIP limit
            color: Column color
            is_done_column: Whether column represents done work

        Returns:
            Created column
        """
        if position is None:
            position = len(self.columns)

        column = KanbanColumn(
            name=name,
            position=position,
            wip_limit=wip_limit,
            color=color,
            is_done_column=is_done_column
        )

        self.columns.append(column)
        self._reorder_columns()
        self.updated_at = datetime.now()

        return column

    def remove_column(self, column_id: str) -> bool:
        """
        Remove a column from the board.

        Args:
            column_id: Column identifier

        Returns:
            True if removed, False if not found
        """
        for i, column in enumerate(self.columns):
            if column.id == column_id:
                # Move cards to first column
                if self.columns:
                    first_column = self.columns[0]
                    for card in self.cards.values():
                        if card.column_id == column_id:
                            card.column_id = first_column.id

                self.columns.pop(i)
                self._reorder_columns()
                self.updated_at = datetime.now()
                return True
        return False

    def _reorder_columns(self) -> None:
        """Reorder columns by position."""
        self.columns.sort(key=lambda c: c.position)
        for i, column in enumerate(self.columns):
            column.position = i

    def add_swimlane(
        self,
        name: str,
        position: Optional[int] = None,
        color: str = "#f0f0f0",
        criteria: Optional[Dict[str, Any]] = None
    ) -> Swimlane:
        """
        Add a swimlane to the board.

        Args:
            name: Swimlane name
            position: Swimlane position (None = append to end)
            color: Swimlane color
            criteria: Filter criteria

        Returns:
            Created swimlane
        """
        if position is None:
            position = len(self.swimlanes)

        swimlane = Swimlane(
            name=name,
            position=position,
            color=color,
            criteria=criteria
        )

        self.swimlanes.append(swimlane)
        self._reorder_swimlanes()
        self.updated_at = datetime.now()

        return swimlane

    def remove_swimlane(self, swimlane_id: str) -> bool:
        """
        Remove a swimlane from the board.

        Args:
            swimlane_id: Swimlane identifier

        Returns:
            True if removed, False if not found
        """
        for i, swimlane in enumerate(self.swimlanes):
            if swimlane.id == swimlane_id:
                # Clear swimlane from cards
                for card in self.cards.values():
                    if card.swimlane_id == swimlane_id:
                        card.swimlane_id = None

                self.swimlanes.pop(i)
                self._reorder_swimlanes()
                self.updated_at = datetime.now()
                return True
        return False

    def _reorder_swimlanes(self) -> None:
        """Reorder swimlanes by position."""
        self.swimlanes.sort(key=lambda s: s.position)
        for i, swimlane in enumerate(self.swimlanes):
            swimlane.position = i

    def add_card(
        self,
        task_id: str,
        column_id: Optional[str] = None,
        swimlane_id: Optional[str] = None,
        labels: Optional[List[str]] = None,
        color: Optional[str] = None
    ) -> Optional[KanbanCard]:
        """
        Add a card to the board.

        Args:
            task_id: Task identifier
            column_id: Column to place card (None = first column)
            swimlane_id: Swimlane to place card
            labels: Card labels
            color: Card color

        Returns:
            Created card or None if invalid
        """
        # Use first column if not specified
        if column_id is None:
            if not self.columns:
                return None
            column_id = self.columns[0].id

        # Get position at end of column
        cards_in_column = [c for c in self.cards.values() if c.column_id == column_id]
        position = len(cards_in_column)

        card = KanbanCard(
            task_id=task_id,
            column_id=column_id,
            swimlane_id=swimlane_id,
            position=position,
            labels=labels,
            color=color
        )

        self.cards[task_id] = card
        self.updated_at = datetime.now()

        return card

    def move_card(
        self,
        task_id: str,
        to_column_id: str,
        to_position: Optional[int] = None,
        to_swimlane_id: Optional[str] = None
    ) -> bool:
        """
        Move a card to a different column/position.

        Args:
            task_id: Task identifier
            to_column_id: Destination column
            to_position: Destination position (None = end of column)
            to_swimlane_id: Destination swimlane

        Returns:
            True if moved, False if invalid
        """
        if task_id not in self.cards:
            return False

        card = self.cards[task_id]

        # Check WIP limit
        if self._check_wip_limit(to_column_id, exclude_task=task_id):
            return False

        # Remove from old position
        old_column_id = card.column_id
        self._remove_card_from_position(task_id)

        # Update card
        card.column_id = to_column_id
        if to_swimlane_id is not None:
            card.swimlane_id = to_swimlane_id

        # Insert at new position
        if to_position is None:
            cards_in_column = [c for c in self.cards.values() if c.column_id == to_column_id]
            to_position = len(cards_in_column)

        card.position = to_position
        self._reorder_cards_in_column(to_column_id)

        if old_column_id != to_column_id:
            self._reorder_cards_in_column(old_column_id)

        self.updated_at = datetime.now()
        return True

    def _remove_card_from_position(self, task_id: str) -> None:
        """Remove card from its current position."""
        if task_id not in self.cards:
            return

        card = self.cards[task_id]
        cards_in_column = [
            c for c in self.cards.values()
            if c.column_id == card.column_id and c.task_id != task_id
        ]

        for i, c in enumerate(sorted(cards_in_column, key=lambda x: x.position)):
            c.position = i

    def _reorder_cards_in_column(self, column_id: str) -> None:
        """Reorder cards in a column."""
        cards_in_column = [c for c in self.cards.values() if c.column_id == column_id]
        for i, card in enumerate(sorted(cards_in_column, key=lambda c: c.position)):
            card.position = i

    def _check_wip_limit(self, column_id: str, exclude_task: Optional[str] = None) -> bool:
        """
        Check if adding a card would exceed WIP limit.

        Args:
            column_id: Column to check
            exclude_task: Task to exclude from count

        Returns:
            True if WIP limit would be exceeded
        """
        column = next((c for c in self.columns if c.id == column_id), None)
        if not column or column.wip_limit is None:
            return False

        cards_in_column = [
            c for c in self.cards.values()
            if c.column_id == column_id and c.task_id != exclude_task
        ]

        return len(cards_in_column) >= column.wip_limit

    def get_column_card_count(self, column_id: str) -> int:
        """Get the number of cards in a column."""
        return sum(1 for c in self.cards.values() if c.column_id == column_id)

    def get_cards_by_column(self, column_id: str) -> List[KanbanCard]:
        """Get all cards in a column."""
        cards = [c for c in self.cards.values() if c.column_id == column_id]
        return sorted(cards, key=lambda c: c.position)

    def get_cards_by_swimlane(self, swimlane_id: str) -> List[KanbanCard]:
        """Get all cards in a swimlane."""
        return [c for c in self.cards.values() if c.swimlane_id == swimlane_id]

    def apply_filter(self, filter_criteria: Dict[str, Any]) -> None:
        """
        Apply filters to the board.

        Args:
            filter_criteria: Filter criteria dictionary
        """
        self.filters = filter_criteria
        self.updated_at = datetime.now()

    def clear_filters(self) -> None:
        """Clear all filters."""
        self.filters = {}
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert board to dictionary."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "columns": [c.to_dict() for c in self.columns],
            "swimlanes": [s.to_dict() for s in self.swimlanes],
            "cards": {tid: c.to_dict() for tid, c in self.cards.items()},
            "filters": self.filters,
            "settings": self.settings,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class KanbanManager:
    """
    Manages Kanban boards.
    Handles board creation, card movements, and board queries.
    """

    def __init__(self, task_manager):
        """
        Initialize the Kanban manager.

        Args:
            task_manager: Task manager instance
        """
        self.task_manager = task_manager
        self.boards: Dict[str, KanbanBoard] = {}

    def create_board(
        self,
        project_id: str,
        name: str,
        description: str = ""
    ) -> KanbanBoard:
        """
        Create a new Kanban board.

        Args:
            project_id: Project identifier
            name: Board name
            description: Board description

        Returns:
            Created board
        """
        board = KanbanBoard(project_id=project_id, name=name, description=description)
        self.boards[board.id] = board

        # Add all project tasks as cards
        tasks = self.task_manager.get_tasks_by_project(project_id)
        for task in tasks:
            # Map task status to column
            column = self._get_column_for_status(board, task.status.value)
            board.add_card(task.id, column_id=column.id if column else None)

        return board

    def get_board(self, board_id: str) -> Optional[KanbanBoard]:
        """Get a board by ID."""
        return self.boards.get(board_id)

    def get_boards_by_project(self, project_id: str) -> List[KanbanBoard]:
        """Get all boards for a project."""
        return [b for b in self.boards.values() if b.project_id == project_id]

    def delete_board(self, board_id: str) -> bool:
        """Delete a board."""
        if board_id in self.boards:
            del self.boards[board_id]
            return True
        return False

    def _get_column_for_status(self, board: KanbanBoard, status: str) -> Optional[KanbanColumn]:
        """Map task status to board column."""
        status_mapping = {
            "todo": 0,
            "in_progress": 1,
            "blocked": 1,
            "done": -1,
            "cancelled": -1
        }

        index = status_mapping.get(status, 0)
        if index == -1:
            # Find done column
            for column in board.columns:
                if column.is_done_column:
                    return column
            return board.columns[-1] if board.columns else None
        else:
            return board.columns[index] if index < len(board.columns) else None

    def sync_task_to_board(self, task_id: str, board_id: str) -> bool:
        """
        Sync a task status to its Kanban board position.

        Args:
            task_id: Task identifier
            board_id: Board identifier

        Returns:
            True if synced
        """
        board = self.get_board(board_id)
        task = self.task_manager.get_task(task_id)

        if not board or not task:
            return False

        # Find or create card
        if task_id not in board.cards:
            column = self._get_column_for_status(board, task.status.value)
            board.add_card(task_id, column_id=column.id if column else None)
        else:
            # Move card to appropriate column
            column = self._get_column_for_status(board, task.status.value)
            if column:
                board.move_card(task_id, column.id)

        return True
