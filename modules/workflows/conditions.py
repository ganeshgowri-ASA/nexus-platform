"""
NEXUS Workflow Conditions
Conditional logic, filters, loops, and data transformations
"""

from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import re
import json
import operator


class ConditionType(Enum):
    """Types of conditions"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN = "less_than"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    MATCHES_REGEX = "matches_regex"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"
    IS_TRUE = "is_true"
    IS_FALSE = "is_false"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    BETWEEN = "between"
    AND = "and"
    OR = "or"
    NOT = "not"


class FilterOperation(Enum):
    """Filter operations"""
    MAP = "map"
    FILTER = "filter"
    REDUCE = "reduce"
    SORT = "sort"
    UNIQUE = "unique"
    FLATTEN = "flatten"
    GROUP_BY = "group_by"
    LIMIT = "limit"
    SKIP = "skip"


@dataclass
class Condition:
    """Single condition"""
    field: str
    operator: ConditionType
    value: Any
    case_sensitive: bool = True


@dataclass
class ConditionGroup:
    """Group of conditions with logical operator"""
    conditions: List[Union[Condition, 'ConditionGroup']]
    operator: ConditionType  # AND or OR
    negate: bool = False


class ConditionEvaluator:
    """Evaluates conditions against data"""

    def __init__(self):
        self.operators = {
            ConditionType.EQUALS: operator.eq,
            ConditionType.NOT_EQUALS: operator.ne,
            ConditionType.GREATER_THAN: operator.gt,
            ConditionType.GREATER_THAN_OR_EQUAL: operator.ge,
            ConditionType.LESS_THAN: operator.lt,
            ConditionType.LESS_THAN_OR_EQUAL: operator.le,
        }

    def evaluate(
        self,
        condition: Union[Condition, ConditionGroup],
        data: Dict[str, Any]
    ) -> bool:
        """Evaluate a condition or condition group"""
        if isinstance(condition, ConditionGroup):
            return self._evaluate_group(condition, data)
        else:
            return self._evaluate_condition(condition, data)

    def _evaluate_condition(self, condition: Condition, data: Dict[str, Any]) -> bool:
        """Evaluate a single condition"""
        # Get field value
        field_value = self._get_field_value(data, condition.field)

        # Handle case sensitivity for string comparisons
        if isinstance(field_value, str) and isinstance(condition.value, str):
            if not condition.case_sensitive:
                field_value = field_value.lower()
                condition.value = condition.value.lower()

        # Evaluate based on operator
        if condition.operator in self.operators:
            op = self.operators[condition.operator]
            return op(field_value, condition.value)

        elif condition.operator == ConditionType.CONTAINS:
            return condition.value in field_value

        elif condition.operator == ConditionType.NOT_CONTAINS:
            return condition.value not in field_value

        elif condition.operator == ConditionType.STARTS_WITH:
            return str(field_value).startswith(str(condition.value))

        elif condition.operator == ConditionType.ENDS_WITH:
            return str(field_value).endswith(str(condition.value))

        elif condition.operator == ConditionType.MATCHES_REGEX:
            return bool(re.match(condition.value, str(field_value)))

        elif condition.operator == ConditionType.IN_LIST:
            return field_value in condition.value

        elif condition.operator == ConditionType.NOT_IN_LIST:
            return field_value not in condition.value

        elif condition.operator == ConditionType.IS_EMPTY:
            return not field_value or len(field_value) == 0

        elif condition.operator == ConditionType.IS_NOT_EMPTY:
            return bool(field_value) and len(field_value) > 0

        elif condition.operator == ConditionType.IS_TRUE:
            return bool(field_value) is True

        elif condition.operator == ConditionType.IS_FALSE:
            return bool(field_value) is False

        elif condition.operator == ConditionType.IS_NULL:
            return field_value is None

        elif condition.operator == ConditionType.IS_NOT_NULL:
            return field_value is not None

        elif condition.operator == ConditionType.BETWEEN:
            min_val, max_val = condition.value
            return min_val <= field_value <= max_val

        return False

    def _evaluate_group(self, group: ConditionGroup, data: Dict[str, Any]) -> bool:
        """Evaluate a condition group"""
        results = [self.evaluate(cond, data) for cond in group.conditions]

        if group.operator == ConditionType.AND:
            result = all(results)
        elif group.operator == ConditionType.OR:
            result = any(results)
        else:
            result = False

        if group.negate:
            result = not result

        return result

    def _get_field_value(self, data: Dict[str, Any], field: str) -> Any:
        """Get field value from data, supporting nested paths"""
        parts = field.split('.')
        value = data

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif isinstance(value, list) and part.isdigit():
                index = int(part)
                value = value[index] if index < len(value) else None
            else:
                return None

        return value


class DataFilter:
    """Filters and transforms data"""

    def filter(
        self,
        data: List[Dict[str, Any]],
        condition: Union[Condition, ConditionGroup]
    ) -> List[Dict[str, Any]]:
        """Filter data based on condition"""
        evaluator = ConditionEvaluator()
        return [item for item in data if evaluator.evaluate(condition, item)]

    def map(
        self,
        data: List[Dict[str, Any]],
        transformation: Callable[[Dict[str, Any]], Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Map transformation over data"""
        return [transformation(item) for item in data]

    def reduce(
        self,
        data: List[Any],
        operation: str,
        initial: Any = None
    ) -> Any:
        """Reduce data to single value"""
        if not data:
            return initial

        if operation == "sum":
            return sum(data)
        elif operation == "avg":
            return sum(data) / len(data)
        elif operation == "min":
            return min(data)
        elif operation == "max":
            return max(data)
        elif operation == "count":
            return len(data)
        elif operation == "concat":
            return ''.join(str(x) for x in data)
        elif operation == "join":
            return ', '.join(str(x) for x in data)

        return initial

    def sort(
        self,
        data: List[Dict[str, Any]],
        field: str,
        descending: bool = False
    ) -> List[Dict[str, Any]]:
        """Sort data by field"""
        return sorted(
            data,
            key=lambda x: self._get_nested_value(x, field),
            reverse=descending
        )

    def unique(
        self,
        data: List[Dict[str, Any]],
        field: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get unique items"""
        if field:
            seen = set()
            result = []
            for item in data:
                value = self._get_nested_value(item, field)
                if value not in seen:
                    seen.add(value)
                    result.append(item)
            return result
        else:
            # For simple lists
            return list(set(data))

    def flatten(self, data: List[List[Any]]) -> List[Any]:
        """Flatten nested lists"""
        result = []
        for item in data:
            if isinstance(item, list):
                result.extend(item)
            else:
                result.append(item)
        return result

    def group_by(
        self,
        data: List[Dict[str, Any]],
        field: str
    ) -> Dict[Any, List[Dict[str, Any]]]:
        """Group data by field"""
        groups = {}
        for item in data:
            key = self._get_nested_value(item, field)
            if key not in groups:
                groups[key] = []
            groups[key].append(item)
        return groups

    def limit(self, data: List[Any], count: int) -> List[Any]:
        """Limit number of items"""
        return data[:count]

    def skip(self, data: List[Any], count: int) -> List[Any]:
        """Skip number of items"""
        return data[count:]

    def _get_nested_value(self, data: Dict[str, Any], field: str) -> Any:
        """Get nested field value"""
        parts = field.split('.')
        value = data

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None

        return value


class LoopController:
    """Controls loop execution in workflows"""

    async def for_each(
        self,
        items: List[Any],
        action: Callable[[Any, int], Any]
    ) -> List[Any]:
        """Execute action for each item"""
        results = []
        for index, item in enumerate(items):
            result = await action(item, index)
            results.append(result)
        return results

    async def while_loop(
        self,
        condition: Callable[[], bool],
        action: Callable[[], Any],
        max_iterations: int = 1000
    ) -> List[Any]:
        """Execute action while condition is true"""
        results = []
        iterations = 0

        while condition() and iterations < max_iterations:
            result = await action()
            results.append(result)
            iterations += 1

        return results

    async def parallel_for_each(
        self,
        items: List[Any],
        action: Callable[[Any], Any],
        max_concurrent: int = 10
    ) -> List[Any]:
        """Execute action for each item in parallel"""
        import asyncio

        semaphore = asyncio.Semaphore(max_concurrent)

        async def bounded_action(item):
            async with semaphore:
                return await action(item)

        tasks = [bounded_action(item) for item in items]
        results = await asyncio.gather(*tasks)

        return results


class BranchController:
    """Controls branching logic in workflows"""

    async def if_then_else(
        self,
        condition: bool,
        then_action: Callable[[], Any],
        else_action: Optional[Callable[[], Any]] = None
    ) -> Any:
        """Execute if-then-else logic"""
        if condition:
            return await then_action()
        elif else_action:
            return await else_action()
        return None

    async def switch(
        self,
        value: Any,
        cases: Dict[Any, Callable[[], Any]],
        default: Optional[Callable[[], Any]] = None
    ) -> Any:
        """Execute switch-case logic"""
        if value in cases:
            return await cases[value]()
        elif default:
            return await default()
        return None


class DataTransformer:
    """Transforms data between formats"""

    def transform(
        self,
        data: Any,
        transformations: List[Dict[str, Any]]
    ) -> Any:
        """Apply series of transformations"""
        result = data

        for transform in transformations:
            transform_type = transform.get('type')

            if transform_type == 'select':
                result = self._select_fields(result, transform['fields'])

            elif transform_type == 'rename':
                result = self._rename_fields(result, transform['mapping'])

            elif transform_type == 'add':
                result = self._add_field(result, transform['field'], transform['value'])

            elif transform_type == 'remove':
                result = self._remove_fields(result, transform['fields'])

            elif transform_type == 'convert':
                result = self._convert_type(result, transform['field'], transform['to_type'])

            elif transform_type == 'format':
                result = self._format_field(result, transform['field'], transform['format'])

            elif transform_type == 'calculate':
                result = self._calculate_field(result, transform['field'], transform['expression'])

        return result

    def _select_fields(self, data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """Select specific fields"""
        return {k: v for k, v in data.items() if k in fields}

    def _rename_fields(self, data: Dict[str, Any], mapping: Dict[str, str]) -> Dict[str, Any]:
        """Rename fields"""
        result = data.copy()
        for old_name, new_name in mapping.items():
            if old_name in result:
                result[new_name] = result.pop(old_name)
        return result

    def _add_field(self, data: Dict[str, Any], field: str, value: Any) -> Dict[str, Any]:
        """Add a new field"""
        result = data.copy()
        result[field] = value
        return result

    def _remove_fields(self, data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """Remove fields"""
        return {k: v for k, v in data.items() if k not in fields}

    def _convert_type(self, data: Dict[str, Any], field: str, to_type: str) -> Dict[str, Any]:
        """Convert field type"""
        result = data.copy()
        if field in result:
            value = result[field]

            if to_type == 'string':
                result[field] = str(value)
            elif to_type == 'int':
                result[field] = int(value)
            elif to_type == 'float':
                result[field] = float(value)
            elif to_type == 'bool':
                result[field] = bool(value)
            elif to_type == 'json':
                result[field] = json.loads(value) if isinstance(value, str) else value

        return result

    def _format_field(self, data: Dict[str, Any], field: str, format_str: str) -> Dict[str, Any]:
        """Format field value"""
        result = data.copy()
        if field in result:
            value = result[field]

            if isinstance(value, datetime):
                result[field] = value.strftime(format_str)
            elif isinstance(value, (int, float)):
                result[field] = format_str.format(value)
            else:
                result[field] = format_str.format(str(value))

        return result

    def _calculate_field(self, data: Dict[str, Any], field: str, expression: str) -> Dict[str, Any]:
        """Calculate field from expression"""
        result = data.copy()

        # Simple expression evaluation
        # In production, use a safe expression evaluator
        try:
            value = eval(expression, {"__builtins__": {}}, data)
            result[field] = value
        except Exception:
            pass

        return result


class ExpressionEvaluator:
    """Evaluates expressions safely"""

    def evaluate(self, expression: str, context: Dict[str, Any]) -> Any:
        """Evaluate an expression"""
        # This is a simplified version
        # In production, use libraries like simpleeval or build a proper parser

        # Handle basic operations
        expression = expression.strip()

        # Variable substitution
        for key, value in context.items():
            expression = expression.replace(f"{{{key}}}", str(value))

        # Try to evaluate
        try:
            # Safe evaluation with limited builtins
            safe_dict = {
                '__builtins__': {},
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'sum': sum,
                'min': min,
                'max': max,
            }
            safe_dict.update(context)

            return eval(expression, safe_dict, {})
        except Exception as e:
            raise ValueError(f"Failed to evaluate expression: {expression}, error: {str(e)}")


# Global instances
condition_evaluator = ConditionEvaluator()
data_filter = DataFilter()
loop_controller = LoopController()
branch_controller = BranchController()
data_transformer = DataTransformer()
expression_evaluator = ExpressionEvaluator()
