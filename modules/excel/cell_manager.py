"""Cell management for spreadsheet editing and formatting."""
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import copy


class HorizontalAlignment(Enum):
    """Horizontal alignment options."""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"


class VerticalAlignment(Enum):
    """Vertical alignment options."""
    TOP = "top"
    MIDDLE = "middle"
    BOTTOM = "bottom"


class NumberFormat(Enum):
    """Number format types."""
    GENERAL = "general"
    NUMBER = "0.00"
    CURRENCY = "$#,##0.00"
    ACCOUNTING = "_($* #,##0.00_);_($* (#,##0.00);_($* \"-\"??_);_(@_)"
    PERCENTAGE = "0.00%"
    FRACTION = "# ?/?"
    SCIENTIFIC = "0.00E+00"
    DATE = "m/d/yyyy"
    TIME = "h:mm:ss"
    DATETIME = "m/d/yyyy h:mm"
    TEXT = "@"
    CUSTOM = "custom"


@dataclass
class CellStyle:
    """Cell formatting style."""

    # Font
    font_family: str = "Arial"
    font_size: int = 11
    font_color: str = "#000000"
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strikethrough: bool = False

    # Background
    background_color: Optional[str] = None

    # Borders
    border_top: Optional[str] = None
    border_bottom: Optional[str] = None
    border_left: Optional[str] = None
    border_right: Optional[str] = None
    border_color: str = "#000000"

    # Alignment
    horizontal_align: HorizontalAlignment = HorizontalAlignment.LEFT
    vertical_align: VerticalAlignment = VerticalAlignment.MIDDLE
    text_wrap: bool = False

    # Number format
    number_format: NumberFormat = NumberFormat.GENERAL
    custom_format: Optional[str] = None

    # Misc
    locked: bool = True
    hidden: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'font_family': self.font_family,
            'font_size': self.font_size,
            'font_color': self.font_color,
            'bold': self.bold,
            'italic': self.italic,
            'underline': self.underline,
            'strikethrough': self.strikethrough,
            'background_color': self.background_color,
            'border_top': self.border_top,
            'border_bottom': self.border_bottom,
            'border_left': self.border_left,
            'border_right': self.border_right,
            'border_color': self.border_color,
            'horizontal_align': self.horizontal_align.value,
            'vertical_align': self.vertical_align.value,
            'text_wrap': self.text_wrap,
            'number_format': self.number_format.value,
            'custom_format': self.custom_format,
            'locked': self.locked,
            'hidden': self.hidden
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CellStyle':
        """Create from dictionary."""
        return cls(
            font_family=data.get('font_family', 'Arial'),
            font_size=data.get('font_size', 11),
            font_color=data.get('font_color', '#000000'),
            bold=data.get('bold', False),
            italic=data.get('italic', False),
            underline=data.get('underline', False),
            strikethrough=data.get('strikethrough', False),
            background_color=data.get('background_color'),
            border_top=data.get('border_top'),
            border_bottom=data.get('border_bottom'),
            border_left=data.get('border_left'),
            border_right=data.get('border_right'),
            border_color=data.get('border_color', '#000000'),
            horizontal_align=HorizontalAlignment(data.get('horizontal_align', 'left')),
            vertical_align=VerticalAlignment(data.get('vertical_align', 'middle')),
            text_wrap=data.get('text_wrap', False),
            number_format=NumberFormat(data.get('number_format', 'general')),
            custom_format=data.get('custom_format'),
            locked=data.get('locked', True),
            hidden=data.get('hidden', False)
        )


@dataclass
class Cell:
    """Represents a single cell."""

    row: int
    col: int
    value: Any = None
    formula: Optional[str] = None
    style: CellStyle = field(default_factory=CellStyle)
    comment: Optional[str] = None
    validation: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'row': self.row,
            'col': self.col,
            'value': self.value,
            'formula': self.formula,
            'style': self.style.to_dict(),
            'comment': self.comment,
            'validation': self.validation
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Cell':
        """Create from dictionary."""
        return cls(
            row=data['row'],
            col=data['col'],
            value=data.get('value'),
            formula=data.get('formula'),
            style=CellStyle.from_dict(data.get('style', {})),
            comment=data.get('comment'),
            validation=data.get('validation')
        )


class CellManager:
    """Manage cells in a spreadsheet."""

    def __init__(self, rows: int = 1000, cols: int = 26):
        """
        Initialize cell manager.

        Args:
            rows: Initial number of rows
            cols: Initial number of columns
        """
        self.rows = rows
        self.cols = cols
        self.cells: Dict[Tuple[int, int], Cell] = {}
        self.merged_cells: List[Tuple[int, int, int, int]] = []  # (start_row, start_col, end_row, end_col)
        self.row_heights: Dict[int, float] = {}
        self.col_widths: Dict[int, float] = {}
        self.default_row_height: float = 20.0
        self.default_col_width: float = 100.0

        # Undo/redo stacks
        self.undo_stack: List[Dict[str, Any]] = []
        self.redo_stack: List[Dict[str, Any]] = []
        self.max_undo_size = 100

    def get_cell(self, row: int, col: int) -> Cell:
        """
        Get or create a cell.

        Args:
            row: Row index (0-based)
            col: Column index (0-based)

        Returns:
            Cell instance
        """
        if (row, col) not in self.cells:
            self.cells[(row, col)] = Cell(row=row, col=col)
        return self.cells[(row, col)]

    def set_cell_value(self, row: int, col: int, value: Any,
                       record_undo: bool = True) -> None:
        """
        Set cell value.

        Args:
            row: Row index
            col: Column index
            value: Cell value
            record_undo: Whether to record in undo stack
        """
        if record_undo:
            old_value = self.get_cell(row, col).value
            self._record_undo({
                'action': 'set_value',
                'row': row,
                'col': col,
                'old_value': old_value,
                'new_value': value
            })

        cell = self.get_cell(row, col)
        cell.value = value

    def set_cell_formula(self, row: int, col: int, formula: str,
                        record_undo: bool = True) -> None:
        """
        Set cell formula.

        Args:
            row: Row index
            col: Column index
            formula: Formula string
            record_undo: Whether to record in undo stack
        """
        if record_undo:
            old_formula = self.get_cell(row, col).formula
            self._record_undo({
                'action': 'set_formula',
                'row': row,
                'col': col,
                'old_formula': old_formula,
                'new_formula': formula
            })

        cell = self.get_cell(row, col)
        cell.formula = formula

    def set_cell_style(self, row: int, col: int, style: CellStyle,
                      record_undo: bool = True) -> None:
        """
        Set cell style.

        Args:
            row: Row index
            col: Column index
            style: CellStyle instance
            record_undo: Whether to record in undo stack
        """
        if record_undo:
            old_style = copy.deepcopy(self.get_cell(row, col).style)
            self._record_undo({
                'action': 'set_style',
                'row': row,
                'col': col,
                'old_style': old_style,
                'new_style': style
            })

        cell = self.get_cell(row, col)
        cell.style = style

    def apply_style_to_range(self, start_row: int, start_col: int,
                           end_row: int, end_col: int, style: CellStyle) -> None:
        """
        Apply style to a range of cells.

        Args:
            start_row: Starting row
            start_col: Starting column
            end_row: Ending row
            end_col: Ending column
            style: Style to apply
        """
        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                self.set_cell_style(row, col, copy.deepcopy(style), record_undo=False)

        # Record single undo action for range
        self._record_undo({
            'action': 'apply_style_range',
            'start_row': start_row,
            'start_col': start_col,
            'end_row': end_row,
            'end_col': end_col,
            'style': style
        })

    def merge_cells(self, start_row: int, start_col: int,
                   end_row: int, end_col: int) -> None:
        """
        Merge a range of cells.

        Args:
            start_row: Starting row
            start_col: Starting column
            end_row: Ending row
            end_col: Ending column
        """
        merge_info = (start_row, start_col, end_row, end_col)
        if merge_info not in self.merged_cells:
            self.merged_cells.append(merge_info)
            self._record_undo({
                'action': 'merge',
                'merge_info': merge_info
            })

    def unmerge_cells(self, start_row: int, start_col: int,
                     end_row: int, end_col: int) -> None:
        """
        Unmerge cells.

        Args:
            start_row: Starting row
            start_col: Starting column
            end_row: Ending row
            end_col: Ending column
        """
        merge_info = (start_row, start_col, end_row, end_col)
        if merge_info in self.merged_cells:
            self.merged_cells.remove(merge_info)
            self._record_undo({
                'action': 'unmerge',
                'merge_info': merge_info
            })

    def copy_cells(self, start_row: int, start_col: int,
                  end_row: int, end_col: int) -> List[List[Cell]]:
        """
        Copy a range of cells.

        Args:
            start_row: Starting row
            start_col: Starting column
            end_row: Ending row
            end_col: Ending column

        Returns:
            2D list of copied cells
        """
        copied = []
        for row in range(start_row, end_row + 1):
            row_cells = []
            for col in range(start_col, end_col + 1):
                cell = self.get_cell(row, col)
                row_cells.append(copy.deepcopy(cell))
            copied.append(row_cells)
        return copied

    def paste_cells(self, start_row: int, start_col: int,
                   cells: List[List[Cell]], paste_values: bool = True,
                   paste_formats: bool = True) -> None:
        """
        Paste cells.

        Args:
            start_row: Starting row for paste
            start_col: Starting column for paste
            cells: 2D list of cells to paste
            paste_values: Whether to paste values
            paste_formats: Whether to paste formats
        """
        for row_offset, row_cells in enumerate(cells):
            for col_offset, source_cell in enumerate(row_cells):
                target_row = start_row + row_offset
                target_col = start_col + col_offset

                target_cell = self.get_cell(target_row, target_col)

                if paste_values:
                    target_cell.value = source_cell.value
                    target_cell.formula = source_cell.formula

                if paste_formats:
                    target_cell.style = copy.deepcopy(source_cell.style)

    def insert_row(self, row: int, count: int = 1) -> None:
        """
        Insert rows.

        Args:
            row: Row index to insert at
            count: Number of rows to insert
        """
        # Shift cells down
        new_cells = {}
        for (r, c), cell in self.cells.items():
            if r >= row:
                new_cell = copy.deepcopy(cell)
                new_cell.row = r + count
                new_cells[(r + count, c)] = new_cell
            else:
                new_cells[(r, c)] = cell

        self.cells = new_cells
        self.rows += count

        self._record_undo({
            'action': 'insert_row',
            'row': row,
            'count': count
        })

    def insert_column(self, col: int, count: int = 1) -> None:
        """
        Insert columns.

        Args:
            col: Column index to insert at
            count: Number of columns to insert
        """
        # Shift cells right
        new_cells = {}
        for (r, c), cell in self.cells.items():
            if c >= col:
                new_cell = copy.deepcopy(cell)
                new_cell.col = c + count
                new_cells[(r, c + count)] = new_cell
            else:
                new_cells[(r, c)] = cell

        self.cells = new_cells
        self.cols += count

        self._record_undo({
            'action': 'insert_column',
            'col': col,
            'count': count
        })

    def delete_row(self, row: int, count: int = 1) -> None:
        """
        Delete rows.

        Args:
            row: Starting row index
            count: Number of rows to delete
        """
        # Remove cells in deleted rows and shift cells up
        new_cells = {}
        for (r, c), cell in self.cells.items():
            if r < row:
                new_cells[(r, c)] = cell
            elif r >= row + count:
                new_cell = copy.deepcopy(cell)
                new_cell.row = r - count
                new_cells[(r - count, c)] = new_cell

        self.cells = new_cells
        self.rows -= count

        self._record_undo({
            'action': 'delete_row',
            'row': row,
            'count': count
        })

    def delete_column(self, col: int, count: int = 1) -> None:
        """
        Delete columns.

        Args:
            col: Starting column index
            count: Number of columns to delete
        """
        # Remove cells in deleted columns and shift cells left
        new_cells = {}
        for (r, c), cell in self.cells.items():
            if c < col:
                new_cells[(r, c)] = cell
            elif c >= col + count:
                new_cell = copy.deepcopy(cell)
                new_cell.col = c - count
                new_cells[(r, c - count)] = new_cell

        self.cells = new_cells
        self.cols -= count

        self._record_undo({
            'action': 'delete_column',
            'col': col,
            'count': count
        })

    def set_row_height(self, row: int, height: float) -> None:
        """Set row height."""
        self.row_heights[row] = height

    def set_column_width(self, col: int, width: float) -> None:
        """Set column width."""
        self.col_widths[col] = width

    def get_row_height(self, row: int) -> float:
        """Get row height."""
        return self.row_heights.get(row, self.default_row_height)

    def get_column_width(self, col: int) -> float:
        """Get column width."""
        return self.col_widths.get(col, self.default_col_width)

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert cells to DataFrame.

        Returns:
            DataFrame with cell values
        """
        # Determine actual size
        max_row = max((r for r, c in self.cells.keys()), default=0) + 1
        max_col = max((c for r, c in self.cells.keys()), default=0) + 1

        # Create data matrix
        data = [[None] * max_col for _ in range(max_row)]

        for (row, col), cell in self.cells.items():
            if row < max_row and col < max_col:
                data[row][col] = cell.value

        return pd.DataFrame(data)

    def from_dataframe(self, df: pd.DataFrame) -> None:
        """
        Load data from DataFrame.

        Args:
            df: DataFrame to load
        """
        self.cells.clear()

        for row_idx, row in df.iterrows():
            for col_idx, value in enumerate(row):
                if pd.notna(value):
                    self.set_cell_value(row_idx, col_idx, value, record_undo=False)

        self.rows = len(df)
        self.cols = len(df.columns)

    def undo(self) -> bool:
        """
        Undo last action.

        Returns:
            bool: True if undo was successful
        """
        if not self.undo_stack:
            return False

        action = self.undo_stack.pop()
        self.redo_stack.append(action)

        # Revert action
        if action['action'] == 'set_value':
            self.set_cell_value(action['row'], action['col'], action['old_value'],
                              record_undo=False)
        elif action['action'] == 'set_formula':
            self.set_cell_formula(action['row'], action['col'], action['old_formula'],
                                record_undo=False)
        elif action['action'] == 'set_style':
            self.set_cell_style(action['row'], action['col'], action['old_style'],
                              record_undo=False)
        # ... handle other actions

        return True

    def redo(self) -> bool:
        """
        Redo last undone action.

        Returns:
            bool: True if redo was successful
        """
        if not self.redo_stack:
            return False

        action = self.redo_stack.pop()
        self.undo_stack.append(action)

        # Redo action
        if action['action'] == 'set_value':
            self.set_cell_value(action['row'], action['col'], action['new_value'],
                              record_undo=False)
        elif action['action'] == 'set_formula':
            self.set_cell_formula(action['row'], action['col'], action['new_formula'],
                                record_undo=False)
        elif action['action'] == 'set_style':
            self.set_cell_style(action['row'], action['col'], action['new_style'],
                              record_undo=False)
        # ... handle other actions

        return True

    def _record_undo(self, action: Dict[str, Any]) -> None:
        """Record an action in the undo stack."""
        self.undo_stack.append(action)
        if len(self.undo_stack) > self.max_undo_size:
            self.undo_stack.pop(0)

        # Clear redo stack when new action is recorded
        self.redo_stack.clear()

    def clear(self) -> None:
        """Clear all cells."""
        self.cells.clear()
        self.merged_cells.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()


def column_letter(col: int) -> str:
    """
    Convert column index to letter (0 -> A, 25 -> Z, 26 -> AA).

    Args:
        col: Column index (0-based)

    Returns:
        Column letter(s)
    """
    result = ""
    col += 1  # Make 1-based

    while col > 0:
        col -= 1
        result = chr(ord('A') + (col % 26)) + result
        col //= 26

    return result


def column_index(letter: str) -> int:
    """
    Convert column letter to index (A -> 0, Z -> 25, AA -> 26).

    Args:
        letter: Column letter(s)

    Returns:
        Column index (0-based)
    """
    result = 0
    for char in letter.upper():
        result = result * 26 + (ord(char) - ord('A') + 1)
    return result - 1


def cell_reference(row: int, col: int) -> str:
    """
    Get cell reference (e.g., A1, B2).

    Args:
        row: Row index (0-based)
        col: Column index (0-based)

    Returns:
        Cell reference string
    """
    return f"{column_letter(col)}{row + 1}"
