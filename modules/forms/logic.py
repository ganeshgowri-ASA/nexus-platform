"""
Conditional Logic Module

Provides conditional logic, branching, skip logic, calculations, and piping functionality.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
import uuid


class ConditionOperator(Enum):
    """Operators for conditional logic"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_OR_EQUAL = "greater_or_equal"
    LESS_OR_EQUAL = "less_or_equal"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IN = "in"
    NOT_IN = "not_in"


class ActionType(Enum):
    """Types of actions to perform when conditions are met"""
    SHOW_FIELD = "show_field"
    HIDE_FIELD = "hide_field"
    SHOW_PAGE = "show_page"
    HIDE_PAGE = "hide_page"
    JUMP_TO_PAGE = "jump_to_page"
    SKIP_TO_FIELD = "skip_to_field"
    SET_VALUE = "set_value"
    CALCULATE = "calculate"
    SHOW_MESSAGE = "show_message"
    SUBMIT_FORM = "submit_form"
    REQUIRE_FIELD = "require_field"
    UNREQUIRE_FIELD = "unrequire_field"


class LogicOperator(Enum):
    """Logical operators for combining conditions"""
    AND = "and"
    OR = "or"


@dataclass
class Condition:
    """Represents a single condition"""
    field_id: str
    operator: ConditionOperator
    value: Any = None

    def evaluate(self, form_data: Dict[str, Any]) -> bool:
        """
        Evaluate the condition against form data

        Args:
            form_data: Current form data

        Returns:
            True if condition is met, False otherwise
        """
        field_value = form_data.get(self.field_id)

        if self.operator == ConditionOperator.EQUALS:
            return field_value == self.value

        elif self.operator == ConditionOperator.NOT_EQUALS:
            return field_value != self.value

        elif self.operator == ConditionOperator.CONTAINS:
            if isinstance(field_value, (list, str)):
                return self.value in field_value
            return False

        elif self.operator == ConditionOperator.NOT_CONTAINS:
            if isinstance(field_value, (list, str)):
                return self.value not in field_value
            return True

        elif self.operator == ConditionOperator.GREATER_THAN:
            try:
                return float(field_value) > float(self.value)
            except (ValueError, TypeError):
                return False

        elif self.operator == ConditionOperator.LESS_THAN:
            try:
                return float(field_value) < float(self.value)
            except (ValueError, TypeError):
                return False

        elif self.operator == ConditionOperator.GREATER_OR_EQUAL:
            try:
                return float(field_value) >= float(self.value)
            except (ValueError, TypeError):
                return False

        elif self.operator == ConditionOperator.LESS_OR_EQUAL:
            try:
                return float(field_value) <= float(self.value)
            except (ValueError, TypeError):
                return False

        elif self.operator == ConditionOperator.IS_EMPTY:
            return field_value is None or field_value == "" or field_value == []

        elif self.operator == ConditionOperator.IS_NOT_EMPTY:
            return field_value is not None and field_value != "" and field_value != []

        elif self.operator == ConditionOperator.STARTS_WITH:
            return str(field_value).startswith(str(self.value))

        elif self.operator == ConditionOperator.ENDS_WITH:
            return str(field_value).endswith(str(self.value))

        elif self.operator == ConditionOperator.IN:
            return field_value in self.value if isinstance(self.value, list) else False

        elif self.operator == ConditionOperator.NOT_IN:
            return field_value not in self.value if isinstance(self.value, list) else True

        return False


@dataclass
class Action:
    """Represents an action to perform"""
    action_type: ActionType
    target_id: str
    value: Any = None


@dataclass
class LogicRule:
    """Represents a complete logic rule with conditions and actions"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    conditions: List[Condition] = field(default_factory=list)
    logic_operator: LogicOperator = LogicOperator.AND
    actions: List[Action] = field(default_factory=list)
    enabled: bool = True

    def evaluate(self, form_data: Dict[str, Any]) -> bool:
        """
        Evaluate all conditions in this rule

        Args:
            form_data: Current form data

        Returns:
            True if rule conditions are met, False otherwise
        """
        if not self.enabled or not self.conditions:
            return False

        results = [condition.evaluate(form_data) for condition in self.conditions]

        if self.logic_operator == LogicOperator.AND:
            return all(results)
        else:  # OR
            return any(results)

    def execute_actions(self, form_data: Dict[str, Any]) -> List[Action]:
        """
        Execute actions if conditions are met

        Args:
            form_data: Current form data

        Returns:
            List of actions to perform
        """
        if self.evaluate(form_data):
            return self.actions
        return []


class ConditionalLogic:
    """Manager for conditional logic rules"""

    def __init__(self):
        self.rules: Dict[str, LogicRule] = {}

    def add_rule(self, rule: LogicRule) -> None:
        """Add a logic rule"""
        self.rules[rule.id] = rule

    def remove_rule(self, rule_id: str) -> None:
        """Remove a logic rule"""
        self.rules.pop(rule_id, None)

    def get_rule(self, rule_id: str) -> Optional[LogicRule]:
        """Get a logic rule by ID"""
        return self.rules.get(rule_id)

    def evaluate_all(self, form_data: Dict[str, Any]) -> List[Action]:
        """
        Evaluate all rules and return actions to perform

        Args:
            form_data: Current form data

        Returns:
            List of actions to perform
        """
        actions = []
        for rule in self.rules.values():
            if rule.enabled:
                rule_actions = rule.execute_actions(form_data)
                actions.extend(rule_actions)
        return actions

    def get_visible_fields(self, form_data: Dict[str, Any],
                          all_field_ids: List[str]) -> List[str]:
        """
        Determine which fields should be visible based on logic rules

        Args:
            form_data: Current form data
            all_field_ids: List of all field IDs in the form

        Returns:
            List of visible field IDs
        """
        visible = set(all_field_ids)
        actions = self.evaluate_all(form_data)

        for action in actions:
            if action.action_type == ActionType.HIDE_FIELD:
                visible.discard(action.target_id)
            elif action.action_type == ActionType.SHOW_FIELD:
                visible.add(action.target_id)

        return list(visible)

    def get_required_fields(self, form_data: Dict[str, Any],
                          initially_required: List[str]) -> List[str]:
        """
        Determine which fields are required based on logic rules

        Args:
            form_data: Current form data
            initially_required: List of field IDs that are initially required

        Returns:
            List of required field IDs
        """
        required = set(initially_required)
        actions = self.evaluate_all(form_data)

        for action in actions:
            if action.action_type == ActionType.REQUIRE_FIELD:
                required.add(action.target_id)
            elif action.action_type == ActionType.UNREQUIRE_FIELD:
                required.discard(action.target_id)

        return list(required)

    def clear_rules(self) -> None:
        """Clear all logic rules"""
        self.rules.clear()


class Calculator:
    """Handles calculations and computed fields"""

    @staticmethod
    def calculate(formula: str, form_data: Dict[str, Any]) -> Optional[float]:
        """
        Calculate a value based on a formula and form data

        Args:
            formula: Formula string (e.g., "{field1} + {field2}")
            form_data: Current form data

        Returns:
            Calculated value or None if calculation fails
        """
        try:
            # Replace field references with values
            expression = formula
            for field_id, value in form_data.items():
                placeholder = "{" + field_id + "}"
                if placeholder in expression:
                    try:
                        num_value = float(value) if value else 0
                        expression = expression.replace(placeholder, str(num_value))
                    except (ValueError, TypeError):
                        expression = expression.replace(placeholder, "0")

            # Evaluate the expression safely
            # Only allow basic math operations
            allowed_chars = set("0123456789+-*/(). ")
            if not all(c in allowed_chars for c in expression):
                return None

            result = eval(expression, {"__builtins__": {}}, {})
            return float(result)

        except Exception:
            return None

    @staticmethod
    def sum_fields(field_ids: List[str], form_data: Dict[str, Any]) -> float:
        """Sum values from multiple fields"""
        total = 0.0
        for field_id in field_ids:
            value = form_data.get(field_id, 0)
            try:
                total += float(value)
            except (ValueError, TypeError):
                continue
        return total

    @staticmethod
    def average_fields(field_ids: List[str], form_data: Dict[str, Any]) -> Optional[float]:
        """Calculate average of values from multiple fields"""
        values = []
        for field_id in field_ids:
            value = form_data.get(field_id)
            try:
                values.append(float(value))
            except (ValueError, TypeError):
                continue

        if not values:
            return None

        return sum(values) / len(values)

    @staticmethod
    def count_filled_fields(field_ids: List[str], form_data: Dict[str, Any]) -> int:
        """Count how many fields are filled"""
        count = 0
        for field_id in field_ids:
            value = form_data.get(field_id)
            if value is not None and value != "" and value != []:
                count += 1
        return count


class Piping:
    """Handles answer piping (inserting answers from one field into another)"""

    @staticmethod
    def pipe_text(text: str, form_data: Dict[str, Any]) -> str:
        """
        Replace placeholders in text with form data values

        Args:
            text: Text with placeholders like {{field_id}}
            form_data: Current form data

        Returns:
            Text with placeholders replaced
        """
        result = text
        for field_id, value in form_data.items():
            placeholder = "{{" + field_id + "}}"
            if placeholder in result:
                result = result.replace(placeholder, str(value) if value else "")
        return result

    @staticmethod
    def get_piped_value(field_id: str, form_data: Dict[str, Any]) -> Any:
        """Get value from another field for piping"""
        return form_data.get(field_id)


class BranchingLogic:
    """Handles page branching and skip logic"""

    def __init__(self):
        self.page_jumps: Dict[str, Dict[Any, int]] = {}  # field_id -> {value: page_number}

    def add_branch(self, field_id: str, value: Any, target_page: int) -> None:
        """
        Add a branching rule

        Args:
            field_id: ID of the field that triggers branching
            value: Value that triggers the branch
            target_page: Page number to jump to
        """
        if field_id not in self.page_jumps:
            self.page_jumps[field_id] = {}
        self.page_jumps[field_id][value] = target_page

    def get_next_page(self, current_page: int, form_data: Dict[str, Any]) -> int:
        """
        Determine the next page based on branching logic

        Args:
            current_page: Current page number
            form_data: Current form data

        Returns:
            Next page number
        """
        # Check if any field on current page triggers a branch
        for field_id, branches in self.page_jumps.items():
            field_value = form_data.get(field_id)
            if field_value in branches:
                return branches[field_value]

        # Default: go to next page
        return current_page + 1

    def clear_branches(self) -> None:
        """Clear all branching rules"""
        self.page_jumps.clear()


class LogicRuleBuilder:
    """Builder pattern for creating logic rules"""

    def __init__(self, name: str = ""):
        self.rule = LogicRule(name=name)

    def add_condition(self, field_id: str, operator: ConditionOperator,
                     value: Any = None) -> "LogicRuleBuilder":
        """Add a condition to the rule"""
        condition = Condition(field_id=field_id, operator=operator, value=value)
        self.rule.conditions.append(condition)
        return self

    def set_logic_operator(self, operator: LogicOperator) -> "LogicRuleBuilder":
        """Set the logic operator (AND/OR)"""
        self.rule.logic_operator = operator
        return self

    def add_action(self, action_type: ActionType, target_id: str,
                  value: Any = None) -> "LogicRuleBuilder":
        """Add an action to the rule"""
        action = Action(action_type=action_type, target_id=target_id, value=value)
        self.rule.actions.append(action)
        return self

    def build(self) -> LogicRule:
        """Build and return the logic rule"""
        return self.rule


# Common logic rule patterns
class CommonLogicPatterns:
    """Pre-defined common logic patterns"""

    @staticmethod
    def show_field_if_equals(trigger_field: str, trigger_value: Any,
                           target_field: str) -> LogicRule:
        """Show a field if another field equals a value"""
        return LogicRuleBuilder(f"Show {target_field} if {trigger_field} = {trigger_value}") \
            .add_condition(trigger_field, ConditionOperator.EQUALS, trigger_value) \
            .add_action(ActionType.SHOW_FIELD, target_field) \
            .build()

    @staticmethod
    def require_field_if_not_empty(trigger_field: str, target_field: str) -> LogicRule:
        """Require a field if another field is not empty"""
        return LogicRuleBuilder(f"Require {target_field} if {trigger_field} is filled") \
            .add_condition(trigger_field, ConditionOperator.IS_NOT_EMPTY) \
            .add_action(ActionType.REQUIRE_FIELD, target_field) \
            .build()

    @staticmethod
    def skip_to_page_if_yes(trigger_field: str, target_page: int) -> LogicRule:
        """Skip to a page if user answers yes"""
        return LogicRuleBuilder(f"Jump to page {target_page} if yes") \
            .add_condition(trigger_field, ConditionOperator.EQUALS, "Yes") \
            .add_action(ActionType.JUMP_TO_PAGE, str(target_page), target_page) \
            .build()
