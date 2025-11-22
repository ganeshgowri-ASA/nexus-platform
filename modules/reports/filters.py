"""
NEXUS Reports Builder - Filters and Parameters Module
Advanced filtering system with parameters, drill-down capabilities, and dynamic filters
"""

import pandas as pd
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, date, timedelta
import re


class FilterOperator(Enum):
    """Operators for filtering"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL = "lte"
    BETWEEN = "between"
    IN = "in"
    NOT_IN = "not_in"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    REGEX = "regex"


class ParameterType(Enum):
    """Types of report parameters"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    LIST = "list"
    MULTISELECT = "multiselect"


@dataclass
class FilterCondition:
    """Represents a single filter condition"""
    column: str
    operator: FilterOperator
    value: Any
    case_sensitive: bool = True

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply this filter condition to a DataFrame"""
        if self.column not in df.columns:
            return df

        if self.operator == FilterOperator.EQUALS:
            if self.case_sensitive or not isinstance(self.value, str):
                return df[df[self.column] == self.value]
            else:
                return df[df[self.column].str.lower() == self.value.lower()]

        elif self.operator == FilterOperator.NOT_EQUALS:
            if self.case_sensitive or not isinstance(self.value, str):
                return df[df[self.column] != self.value]
            else:
                return df[df[self.column].str.lower() != self.value.lower()]

        elif self.operator == FilterOperator.CONTAINS:
            if self.case_sensitive:
                return df[df[self.column].astype(str).str.contains(str(self.value), na=False)]
            else:
                return df[df[self.column].astype(str).str.lower().str.contains(str(self.value).lower(), na=False)]

        elif self.operator == FilterOperator.NOT_CONTAINS:
            if self.case_sensitive:
                return df[~df[self.column].astype(str).str.contains(str(self.value), na=False)]
            else:
                return df[~df[self.column].astype(str).str.lower().str.contains(str(self.value).lower(), na=False)]

        elif self.operator == FilterOperator.STARTS_WITH:
            if self.case_sensitive:
                return df[df[self.column].astype(str).str.startswith(str(self.value), na=False)]
            else:
                return df[df[self.column].astype(str).str.lower().str.startswith(str(self.value).lower(), na=False)]

        elif self.operator == FilterOperator.ENDS_WITH:
            if self.case_sensitive:
                return df[df[self.column].astype(str).str.endswith(str(self.value), na=False)]
            else:
                return df[df[self.column].astype(str).str.lower().str.endswith(str(self.value).lower(), na=False)]

        elif self.operator == FilterOperator.GREATER_THAN:
            return df[df[self.column] > self.value]

        elif self.operator == FilterOperator.GREATER_THAN_OR_EQUAL:
            return df[df[self.column] >= self.value]

        elif self.operator == FilterOperator.LESS_THAN:
            return df[df[self.column] < self.value]

        elif self.operator == FilterOperator.LESS_THAN_OR_EQUAL:
            return df[df[self.column] <= self.value]

        elif self.operator == FilterOperator.BETWEEN:
            if isinstance(self.value, (list, tuple)) and len(self.value) == 2:
                return df[(df[self.column] >= self.value[0]) & (df[self.column] <= self.value[1])]
            return df

        elif self.operator == FilterOperator.IN:
            if isinstance(self.value, (list, tuple, set)):
                return df[df[self.column].isin(self.value)]
            return df

        elif self.operator == FilterOperator.NOT_IN:
            if isinstance(self.value, (list, tuple, set)):
                return df[~df[self.column].isin(self.value)]
            return df

        elif self.operator == FilterOperator.IS_NULL:
            return df[df[self.column].isna()]

        elif self.operator == FilterOperator.IS_NOT_NULL:
            return df[df[self.column].notna()]

        elif self.operator == FilterOperator.REGEX:
            return df[df[self.column].astype(str).str.match(str(self.value), na=False)]

        return df

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'column': self.column,
            'operator': self.operator.value,
            'value': self.value,
            'case_sensitive': self.case_sensitive
        }


@dataclass
class Parameter:
    """Report parameter that can be set by users"""
    name: str
    label: str
    parameter_type: ParameterType
    default_value: Any = None
    required: bool = False
    description: str = ""
    options: Optional[List[Any]] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    validation_regex: Optional[str] = None

    def __post_init__(self):
        if self.options is None and self.parameter_type in [ParameterType.LIST, ParameterType.MULTISELECT]:
            self.options = []

    def validate(self, value: Any) -> bool:
        """Validate parameter value"""
        if self.required and value is None:
            return False

        if value is None:
            return True

        # Type validation
        if self.parameter_type == ParameterType.INTEGER:
            if not isinstance(value, int):
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    return False

        elif self.parameter_type == ParameterType.FLOAT:
            if not isinstance(value, (int, float)):
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    return False

        elif self.parameter_type == ParameterType.BOOLEAN:
            if not isinstance(value, bool):
                return False

        elif self.parameter_type == ParameterType.DATE:
            if not isinstance(value, (date, datetime)):
                try:
                    datetime.strptime(str(value), '%Y-%m-%d')
                except ValueError:
                    return False

        elif self.parameter_type == ParameterType.DATETIME:
            if not isinstance(value, datetime):
                return False

        elif self.parameter_type in [ParameterType.LIST, ParameterType.MULTISELECT]:
            if self.options and value not in self.options:
                return False

        # Range validation
        if self.min_value is not None and value < self.min_value:
            return False

        if self.max_value is not None and value > self.max_value:
            return False

        # Regex validation
        if self.validation_regex and isinstance(value, str):
            if not re.match(self.validation_regex, value):
                return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'label': self.label,
            'parameter_type': self.parameter_type.value,
            'default_value': self.default_value,
            'required': self.required,
            'description': self.description,
            'options': self.options,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'validation_regex': self.validation_regex
        }


class FilterGroup:
    """Group of filters with AND/OR logic"""

    def __init__(self, logic: str = "AND"):
        self.logic = logic.upper()  # AND or OR
        self.conditions: List[FilterCondition] = []
        self.subgroups: List['FilterGroup'] = []

    def add_condition(self, condition: FilterCondition):
        """Add a filter condition"""
        self.conditions.append(condition)

    def add_subgroup(self, subgroup: 'FilterGroup'):
        """Add a nested filter group"""
        self.subgroups.append(subgroup)

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply all filters in this group"""
        if not self.conditions and not self.subgroups:
            return df

        results = []

        # Apply all conditions
        for condition in self.conditions:
            results.append(condition.apply(df))

        # Apply all subgroups
        for subgroup in self.subgroups:
            results.append(subgroup.apply(df))

        # Combine results based on logic
        if self.logic == "AND":
            # Find intersection of all results
            result = results[0]
            for r in results[1:]:
                result = result.merge(r, how='inner')
            return result
        else:  # OR
            # Find union of all results
            result = pd.concat(results).drop_duplicates()
            return result

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'logic': self.logic,
            'conditions': [c.to_dict() for c in self.conditions],
            'subgroups': [s.to_dict() for s in self.subgroups]
        }


class FilterManager:
    """Manages filters and parameters for reports"""

    def __init__(self):
        self.filter_groups: List[FilterGroup] = []
        self.parameters: Dict[str, Parameter] = {}
        self.parameter_values: Dict[str, Any] = {}

    def add_filter_group(self, group: FilterGroup):
        """Add a filter group"""
        self.filter_groups.append(group)

    def add_parameter(self, parameter: Parameter):
        """Add a parameter"""
        self.parameters[parameter.name] = parameter
        if parameter.default_value is not None:
            self.parameter_values[parameter.name] = parameter.default_value

    def set_parameter_value(self, name: str, value: Any) -> bool:
        """Set parameter value"""
        if name not in self.parameters:
            return False

        parameter = self.parameters[name]
        if not parameter.validate(value):
            return False

        self.parameter_values[name] = value
        return True

    def get_parameter_value(self, name: str) -> Any:
        """Get parameter value"""
        return self.parameter_values.get(name)

    def validate_parameters(self) -> List[str]:
        """Validate all parameters and return errors"""
        errors = []

        for name, parameter in self.parameters.items():
            value = self.parameter_values.get(name)

            if parameter.required and value is None:
                errors.append(f"Parameter '{parameter.label}' is required")

            if value is not None and not parameter.validate(value):
                errors.append(f"Invalid value for parameter '{parameter.label}'")

        return errors

    def apply_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply all filters to DataFrame"""
        result = df.copy()

        for group in self.filter_groups:
            result = group.apply(result)

        return result

    def get_filter_summary(self) -> Dict[str, Any]:
        """Get summary of active filters"""
        return {
            'filter_groups': len(self.filter_groups),
            'total_conditions': sum(len(g.conditions) for g in self.filter_groups),
            'parameters': len(self.parameters),
            'parameter_values': self.parameter_values.copy()
        }

    def clear_filters(self):
        """Clear all filters"""
        self.filter_groups.clear()

    def clear_parameters(self):
        """Reset parameters to default values"""
        self.parameter_values.clear()
        for parameter in self.parameters.values():
            if parameter.default_value is not None:
                self.parameter_values[parameter.name] = parameter.default_value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'filter_groups': [g.to_dict() for g in self.filter_groups],
            'parameters': {name: p.to_dict() for name, p in self.parameters.items()},
            'parameter_values': self.parameter_values
        }


class DrillDownManager:
    """Manages drill-down capabilities for hierarchical data"""

    def __init__(self):
        self.hierarchy: List[str] = []
        self.current_level: int = 0
        self.breadcrumbs: List[Dict[str, Any]] = []

    def set_hierarchy(self, columns: List[str]):
        """Set the drill-down hierarchy"""
        self.hierarchy = columns
        self.current_level = 0
        self.breadcrumbs.clear()

    def drill_down(self, value: Any) -> bool:
        """Drill down to next level"""
        if self.current_level >= len(self.hierarchy) - 1:
            return False

        self.breadcrumbs.append({
            'level': self.current_level,
            'column': self.hierarchy[self.current_level],
            'value': value
        })

        self.current_level += 1
        return True

    def drill_up(self) -> bool:
        """Drill up to previous level"""
        if self.current_level <= 0:
            return False

        self.breadcrumbs.pop()
        self.current_level -= 1
        return True

    def reset(self):
        """Reset to top level"""
        self.current_level = 0
        self.breadcrumbs.clear()

    def get_current_filters(self) -> FilterGroup:
        """Get filters for current drill-down level"""
        group = FilterGroup(logic="AND")

        for crumb in self.breadcrumbs:
            condition = FilterCondition(
                column=crumb['column'],
                operator=FilterOperator.EQUALS,
                value=crumb['value']
            )
            group.add_condition(condition)

        return group

    def get_current_level_column(self) -> Optional[str]:
        """Get the column for the current level"""
        if self.current_level < len(self.hierarchy):
            return self.hierarchy[self.current_level]
        return None

    def apply_drill_down(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply drill-down filters to DataFrame"""
        filter_group = self.get_current_filters()
        return filter_group.apply(df)

    def get_breadcrumb_path(self) -> str:
        """Get breadcrumb path as string"""
        if not self.breadcrumbs:
            return "All"

        path_parts = [f"{crumb['column']}: {crumb['value']}" for crumb in self.breadcrumbs]
        return " > ".join(path_parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'hierarchy': self.hierarchy,
            'current_level': self.current_level,
            'breadcrumbs': self.breadcrumbs
        }


class DateRangeFilter:
    """Specialized filter for date ranges"""

    def __init__(self, column: str):
        self.column = column
        self.start_date: Optional[datetime] = None
        self.end_date: Optional[datetime] = None
        self.preset: Optional[str] = None

    def set_custom_range(self, start: datetime, end: datetime):
        """Set custom date range"""
        self.start_date = start
        self.end_date = end
        self.preset = None

    def set_preset(self, preset: str):
        """Set date range preset"""
        now = datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)

        if preset == "today":
            self.start_date = today
            self.end_date = now
        elif preset == "yesterday":
            self.start_date = today - timedelta(days=1)
            self.end_date = today
        elif preset == "last_7_days":
            self.start_date = today - timedelta(days=7)
            self.end_date = now
        elif preset == "last_30_days":
            self.start_date = today - timedelta(days=30)
            self.end_date = now
        elif preset == "this_month":
            self.start_date = today.replace(day=1)
            self.end_date = now
        elif preset == "last_month":
            first_of_this_month = today.replace(day=1)
            self.end_date = first_of_this_month
            self.start_date = (first_of_this_month - timedelta(days=1)).replace(day=1)
        elif preset == "this_year":
            self.start_date = today.replace(month=1, day=1)
            self.end_date = now
        elif preset == "last_year":
            self.start_date = today.replace(year=today.year-1, month=1, day=1)
            self.end_date = today.replace(year=today.year-1, month=12, day=31)

        self.preset = preset

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply date range filter"""
        if self.column not in df.columns:
            return df

        if self.start_date is None or self.end_date is None:
            return df

        # Convert column to datetime if needed
        df_copy = df.copy()
        df_copy[self.column] = pd.to_datetime(df_copy[self.column])

        # Apply filter
        return df_copy[(df_copy[self.column] >= self.start_date) & (df_copy[self.column] <= self.end_date)]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'column': self.column,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'preset': self.preset
        }
