"""Conditional formatting for spreadsheet cells."""
from typing import Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class ConditionType(Enum):
    """Conditional formatting condition types."""
    CELL_VALUE = "cell_value"
    FORMULA = "formula"
    COLOR_SCALE = "color_scale"
    DATA_BAR = "data_bar"
    ICON_SET = "icon_set"
    TEXT_CONTAINS = "text_contains"
    DATE_OCCURRING = "date_occurring"
    DUPLICATE_VALUES = "duplicate_values"
    UNIQUE_VALUES = "unique_values"
    TOP_BOTTOM = "top_bottom"


class ComparisonOperator(Enum):
    """Comparison operators."""
    EQUAL = "equal"
    NOT_EQUAL = "not_equal"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    BETWEEN = "between"
    NOT_BETWEEN = "not_between"


@dataclass
class ConditionalFormat:
    """Conditional formatting rule."""

    condition_type: ConditionType
    operator: Optional[ComparisonOperator] = None
    value1: Optional[Any] = None
    value2: Optional[Any] = None
    formula: Optional[str] = None

    # Formatting to apply
    font_color: Optional[str] = None
    background_color: Optional[str] = None
    bold: Optional[bool] = None
    italic: Optional[bool] = None

    # For color scale
    min_color: Optional[str] = None
    mid_color: Optional[str] = None
    max_color: Optional[str] = None

    # For data bar
    bar_color: Optional[str] = None
    show_value: bool = True

    # For icon set
    icon_set_name: Optional[str] = None

    # Priority (lower number = higher priority)
    priority: int = 0
    stop_if_true: bool = False

    def matches(self, value: Any, context: Optional[dict] = None) -> bool:
        """
        Check if value matches the condition.

        Args:
            value: Cell value to check
            context: Optional context for formula evaluation

        Returns:
            bool: True if condition matches
        """
        if self.condition_type == ConditionType.CELL_VALUE:
            return self._check_cell_value(value)

        elif self.condition_type == ConditionType.TEXT_CONTAINS:
            return self._check_text_contains(value)

        elif self.condition_type == ConditionType.FORMULA:
            return self._check_formula(value, context)

        elif self.condition_type == ConditionType.DUPLICATE_VALUES:
            return self._check_duplicate(value, context)

        elif self.condition_type == ConditionType.UNIQUE_VALUES:
            return not self._check_duplicate(value, context)

        return False

    def _check_cell_value(self, value: Any) -> bool:
        """Check cell value condition."""
        if not self.operator:
            return False

        try:
            val = float(value) if isinstance(value, (int, float, str)) else value
            val1 = float(self.value1) if self.value1 is not None else None
            val2 = float(self.value2) if self.value2 is not None else None

            if self.operator == ComparisonOperator.EQUAL:
                return val == val1
            elif self.operator == ComparisonOperator.NOT_EQUAL:
                return val != val1
            elif self.operator == ComparisonOperator.GREATER_THAN:
                return val > val1
            elif self.operator == ComparisonOperator.LESS_THAN:
                return val < val1
            elif self.operator == ComparisonOperator.GREATER_EQUAL:
                return val >= val1
            elif self.operator == ComparisonOperator.LESS_EQUAL:
                return val <= val1
            elif self.operator == ComparisonOperator.BETWEEN:
                return val1 <= val <= val2
            elif self.operator == ComparisonOperator.NOT_BETWEEN:
                return not (val1 <= val <= val2)

        except (ValueError, TypeError):
            return False

        return False

    def _check_text_contains(self, value: Any) -> bool:
        """Check text contains condition."""
        if self.value1 is None:
            return False
        return str(self.value1).lower() in str(value).lower()

    def _check_formula(self, value: Any, context: Optional[dict]) -> bool:
        """Check formula condition."""
        # In production, evaluate the formula
        return False

    def _check_duplicate(self, value: Any, context: Optional[dict]) -> bool:
        """Check if value is duplicate."""
        if not context or 'all_values' not in context:
            return False
        all_values = context['all_values']
        return all_values.count(value) > 1

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'condition_type': self.condition_type.value,
            'operator': self.operator.value if self.operator else None,
            'value1': self.value1,
            'value2': self.value2,
            'formula': self.formula,
            'font_color': self.font_color,
            'background_color': self.background_color,
            'bold': self.bold,
            'italic': self.italic,
            'min_color': self.min_color,
            'mid_color': self.mid_color,
            'max_color': self.max_color,
            'bar_color': self.bar_color,
            'show_value': self.show_value,
            'icon_set_name': self.icon_set_name,
            'priority': self.priority,
            'stop_if_true': self.stop_if_true
        }


class ConditionalFormatManager:
    """Manage conditional formatting rules."""

    def __init__(self):
        """Initialize manager."""
        self.rules: dict[tuple[int, int, int, int], List[ConditionalFormat]] = {}

    def add_rule(self, start_row: int, start_col: int, end_row: int, end_col: int,
                rule: ConditionalFormat) -> None:
        """
        Add conditional formatting rule to a range.

        Args:
            start_row: Starting row
            start_col: Starting column
            end_row: Ending row
            end_col: Ending column
            rule: Conditional format rule
        """
        range_key = (start_row, start_col, end_row, end_col)
        if range_key not in self.rules:
            self.rules[range_key] = []
        self.rules[range_key].append(rule)

        # Sort by priority
        self.rules[range_key].sort(key=lambda r: r.priority)

    def get_format_for_cell(self, row: int, col: int, value: Any,
                          context: Optional[dict] = None) -> Optional[ConditionalFormat]:
        """
        Get conditional format for a cell.

        Args:
            row: Row index
            col: Column index
            value: Cell value
            context: Optional context

        Returns:
            Conditional format if matches, None otherwise
        """
        # Check all ranges that contain this cell
        for (sr, sc, er, ec), rules in self.rules.items():
            if sr <= row <= er and sc <= col <= ec:
                for rule in rules:
                    if rule.matches(value, context):
                        if rule.stop_if_true:
                            return rule
                        return rule

        return None

    def create_color_scale(self, start_row: int, start_col: int, end_row: int, end_col: int,
                          min_color: str = "#FF0000", mid_color: str = "#FFFF00",
                          max_color: str = "#00FF00") -> ConditionalFormat:
        """
        Create color scale formatting.

        Args:
            start_row: Starting row
            start_col: Starting column
            end_row: Ending row
            end_col: Ending column
            min_color: Color for minimum value
            mid_color: Color for middle value
            max_color: Color for maximum value

        Returns:
            Conditional format rule
        """
        rule = ConditionalFormat(
            condition_type=ConditionType.COLOR_SCALE,
            min_color=min_color,
            mid_color=mid_color,
            max_color=max_color
        )
        self.add_rule(start_row, start_col, end_row, end_col, rule)
        return rule

    def create_data_bar(self, start_row: int, start_col: int, end_row: int, end_col: int,
                       bar_color: str = "#0070C0", show_value: bool = True) -> ConditionalFormat:
        """
        Create data bar formatting.

        Args:
            start_row: Starting row
            start_col: Starting column
            end_row: Ending row
            end_col: Ending column
            bar_color: Bar color
            show_value: Whether to show value

        Returns:
            Conditional format rule
        """
        rule = ConditionalFormat(
            condition_type=ConditionType.DATA_BAR,
            bar_color=bar_color,
            show_value=show_value
        )
        self.add_rule(start_row, start_col, end_row, end_col, rule)
        return rule

    def create_icon_set(self, start_row: int, start_col: int, end_row: int, end_col: int,
                       icon_set_name: str = "3TrafficLights") -> ConditionalFormat:
        """
        Create icon set formatting.

        Args:
            start_row: Starting row
            start_col: Starting column
            end_row: Ending row
            end_col: Ending column
            icon_set_name: Icon set name

        Returns:
            Conditional format rule
        """
        rule = ConditionalFormat(
            condition_type=ConditionType.ICON_SET,
            icon_set_name=icon_set_name
        )
        self.add_rule(start_row, start_col, end_row, end_col, rule)
        return rule

    def highlight_duplicates(self, start_row: int, start_col: int, end_row: int, end_col: int,
                           background_color: str = "#FFC7CE", font_color: str = "#9C0006") -> ConditionalFormat:
        """
        Highlight duplicate values.

        Args:
            start_row: Starting row
            start_col: Starting column
            end_row: Ending row
            end_col: Ending column
            background_color: Background color
            font_color: Font color

        Returns:
            Conditional format rule
        """
        rule = ConditionalFormat(
            condition_type=ConditionType.DUPLICATE_VALUES,
            background_color=background_color,
            font_color=font_color
        )
        self.add_rule(start_row, start_col, end_row, end_col, rule)
        return rule
