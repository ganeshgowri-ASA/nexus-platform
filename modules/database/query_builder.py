"""
Visual Query Builder

Drag-and-drop SQL query builder with support for joins, filters,
aggregations, subqueries, and no-code interface.
"""

from typing import Dict, Any, List, Optional, Set, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
import re


class JoinType(Enum):
    """SQL join types"""
    INNER = "INNER JOIN"
    LEFT = "LEFT JOIN"
    RIGHT = "RIGHT JOIN"
    FULL = "FULL OUTER JOIN"
    CROSS = "CROSS JOIN"


class OperatorType(Enum):
    """Filter operator types"""
    EQUALS = "="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    LIKE = "LIKE"
    NOT_LIKE = "NOT LIKE"
    IN = "IN"
    NOT_IN = "NOT IN"
    IS_NULL = "IS NULL"
    IS_NOT_NULL = "IS NOT NULL"
    BETWEEN = "BETWEEN"


class AggregateFunction(Enum):
    """Aggregate functions"""
    COUNT = "COUNT"
    SUM = "SUM"
    AVG = "AVG"
    MIN = "MIN"
    MAX = "MAX"
    GROUP_CONCAT = "GROUP_CONCAT"


class SortOrder(Enum):
    """Sort order"""
    ASC = "ASC"
    DESC = "DESC"


@dataclass
class TableRef:
    """Table reference in query"""
    name: str
    alias: Optional[str] = None
    schema: Optional[str] = None

    def to_sql(self) -> str:
        """Convert to SQL"""
        parts = []
        if self.schema:
            parts.append(f"{self.schema}.{self.name}")
        else:
            parts.append(self.name)

        if self.alias:
            parts.append(f"AS {self.alias}")

        return " ".join(parts)

    def get_identifier(self) -> str:
        """Get table identifier (alias or name)"""
        return self.alias or self.name


@dataclass
class Column:
    """Column reference"""
    name: str
    table: Optional[str] = None
    alias: Optional[str] = None
    aggregate: Optional[AggregateFunction] = None

    def to_sql(self) -> str:
        """Convert to SQL"""
        # Build column reference
        if self.table:
            col_ref = f"{self.table}.{self.name}"
        else:
            col_ref = self.name

        # Apply aggregate function
        if self.aggregate:
            col_ref = f"{self.aggregate.value}({col_ref})"

        # Add alias
        if self.alias:
            col_ref = f"{col_ref} AS {self.alias}"

        return col_ref


@dataclass
class Join:
    """JOIN clause"""
    join_type: JoinType
    table: TableRef
    on_left: Column
    on_right: Column

    def to_sql(self) -> str:
        """Convert to SQL"""
        return (
            f"{self.join_type.value} {self.table.to_sql()} "
            f"ON {self.on_left.to_sql()} = {self.on_right.to_sql()}"
        )


@dataclass
class Filter:
    """WHERE clause filter"""
    column: Column
    operator: OperatorType
    value: Optional[Any] = None
    value2: Optional[Any] = None  # For BETWEEN
    logic: str = "AND"  # AND/OR

    def to_sql(self, use_params: bool = True) -> tuple[str, Dict[str, Any]]:
        """Convert to SQL with optional parameterization"""
        params = {}
        col_sql = self.column.to_sql()

        if self.operator in (OperatorType.IS_NULL, OperatorType.IS_NOT_NULL):
            sql = f"{col_sql} {self.operator.value}"
        elif self.operator == OperatorType.BETWEEN:
            if use_params:
                param1 = f"p_{id(self)}_1"
                param2 = f"p_{id(self)}_2"
                sql = f"{col_sql} BETWEEN :{param1} AND :{param2}"
                params[param1] = self.value
                params[param2] = self.value2
            else:
                sql = f"{col_sql} BETWEEN {self._format_value(self.value)} AND {self._format_value(self.value2)}"
        elif self.operator in (OperatorType.IN, OperatorType.NOT_IN):
            if use_params:
                param = f"p_{id(self)}"
                sql = f"{col_sql} {self.operator.value} (:{param})"
                params[param] = tuple(self.value) if isinstance(self.value, list) else self.value
            else:
                values = ", ".join(self._format_value(v) for v in self.value)
                sql = f"{col_sql} {self.operator.value} ({values})"
        else:
            if use_params:
                param = f"p_{id(self)}"
                sql = f"{col_sql} {self.operator.value} :{param}"
                params[param] = self.value
            else:
                sql = f"{col_sql} {self.operator.value} {self._format_value(self.value)}"

        return sql, params

    def _format_value(self, value: Any) -> str:
        """Format value for SQL"""
        if value is None:
            return "NULL"
        elif isinstance(value, str):
            return f"'{value.replace('\'', '\'\'')}'"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        elif isinstance(value, datetime):
            return f"'{value.isoformat()}'"
        else:
            return f"'{str(value)}'"


@dataclass
class OrderBy:
    """ORDER BY clause"""
    column: Column
    order: SortOrder = SortOrder.ASC

    def to_sql(self) -> str:
        """Convert to SQL"""
        return f"{self.column.to_sql()} {self.order.value}"


@dataclass
class GroupBy:
    """GROUP BY clause"""
    columns: List[Column] = field(default_factory=list)
    having: List[Filter] = field(default_factory=list)

    def to_sql(self, use_params: bool = True) -> tuple[str, Dict[str, Any]]:
        """Convert to SQL"""
        if not self.columns:
            return "", {}

        params = {}
        group_sql = "GROUP BY " + ", ".join(col.to_sql() for col in self.columns)

        if self.having:
            having_parts = []
            for filter_obj in self.having:
                filter_sql, filter_params = filter_obj.to_sql(use_params)
                having_parts.append(filter_sql)
                params.update(filter_params)

            having_sql = " HAVING " + f" {self.having[0].logic} ".join(having_parts)
            group_sql += having_sql

        return group_sql, params


@dataclass
class Subquery:
    """Subquery"""
    query: 'Query'
    alias: str

    def to_sql(self, use_params: bool = True) -> tuple[str, Dict[str, Any]]:
        """Convert to SQL"""
        subquery_sql, params = self.query.to_sql(use_params)
        return f"({subquery_sql}) AS {self.alias}", params


class Query:
    """
    SQL Query Builder

    Visual, no-code query builder with support for complex queries.
    """

    def __init__(self):
        self.select_columns: List[Column] = []
        self.from_table: Optional[TableRef] = None
        self.joins: List[Join] = []
        self.filters: List[Filter] = []
        self.group_by: Optional[GroupBy] = None
        self.order_by: List[OrderBy] = []
        self.limit: Optional[int] = None
        self.offset: Optional[int] = None
        self.distinct: bool = False
        self.subqueries: Dict[str, Subquery] = {}

    def select(self, *columns: Union[str, Column]) -> 'Query':
        """Add SELECT columns"""
        for col in columns:
            if isinstance(col, str):
                self.select_columns.append(Column(name=col))
            else:
                self.select_columns.append(col)
        return self

    def from_(self, table: Union[str, TableRef]) -> 'Query':
        """Set FROM table"""
        if isinstance(table, str):
            self.from_table = TableRef(name=table)
        else:
            self.from_table = table
        return self

    def join(
        self,
        table: Union[str, TableRef],
        on_left: Union[str, Column],
        on_right: Union[str, Column],
        join_type: JoinType = JoinType.INNER
    ) -> 'Query':
        """Add JOIN"""
        if isinstance(table, str):
            table = TableRef(name=table)
        if isinstance(on_left, str):
            on_left = Column(name=on_left)
        if isinstance(on_right, str):
            on_right = Column(name=on_right)

        self.joins.append(Join(
            join_type=join_type,
            table=table,
            on_left=on_left,
            on_right=on_right
        ))
        return self

    def where(
        self,
        column: Union[str, Column],
        operator: OperatorType,
        value: Any = None,
        logic: str = "AND"
    ) -> 'Query':
        """Add WHERE filter"""
        if isinstance(column, str):
            column = Column(name=column)

        self.filters.append(Filter(
            column=column,
            operator=operator,
            value=value,
            logic=logic
        ))
        return self

    def group(self, *columns: Union[str, Column]) -> 'Query':
        """Add GROUP BY"""
        if not self.group_by:
            self.group_by = GroupBy()

        for col in columns:
            if isinstance(col, str):
                self.group_by.columns.append(Column(name=col))
            else:
                self.group_by.columns.append(col)
        return self

    def having(
        self,
        column: Union[str, Column],
        operator: OperatorType,
        value: Any,
        logic: str = "AND"
    ) -> 'Query':
        """Add HAVING filter"""
        if not self.group_by:
            self.group_by = GroupBy()

        if isinstance(column, str):
            column = Column(name=column)

        self.group_by.having.append(Filter(
            column=column,
            operator=operator,
            value=value,
            logic=logic
        ))
        return self

    def order(self, column: Union[str, Column], order: SortOrder = SortOrder.ASC) -> 'Query':
        """Add ORDER BY"""
        if isinstance(column, str):
            column = Column(name=column)

        self.order_by.append(OrderBy(column=column, order=order))
        return self

    def limit_offset(self, limit: Optional[int] = None, offset: Optional[int] = None) -> 'Query':
        """Set LIMIT and OFFSET"""
        self.limit = limit
        self.offset = offset
        return self

    def set_distinct(self, distinct: bool = True) -> 'Query':
        """Set DISTINCT"""
        self.distinct = distinct
        return self

    def to_sql(self, use_params: bool = True) -> tuple[str, Dict[str, Any]]:
        """
        Convert to SQL query

        Args:
            use_params: Use parameterized queries (safer)

        Returns:
            Tuple of (SQL string, parameters dict)
        """
        if not self.from_table:
            raise ValueError("FROM table not specified")

        params = {}
        parts = []

        # SELECT
        select_part = "SELECT DISTINCT" if self.distinct else "SELECT"
        if self.select_columns:
            columns_sql = ", ".join(col.to_sql() for col in self.select_columns)
        else:
            columns_sql = "*"
        parts.append(f"{select_part} {columns_sql}")

        # FROM
        parts.append(f"FROM {self.from_table.to_sql()}")

        # JOINs
        for join in self.joins:
            parts.append(join.to_sql())

        # WHERE
        if self.filters:
            where_parts = []
            for filter_obj in self.filters:
                filter_sql, filter_params = filter_obj.to_sql(use_params)
                where_parts.append(filter_sql)
                params.update(filter_params)

            where_clause = f" {self.filters[0].logic} ".join(where_parts)
            parts.append(f"WHERE {where_clause}")

        # GROUP BY & HAVING
        if self.group_by:
            group_sql, group_params = self.group_by.to_sql(use_params)
            parts.append(group_sql)
            params.update(group_params)

        # ORDER BY
        if self.order_by:
            order_sql = ", ".join(ob.to_sql() for ob in self.order_by)
            parts.append(f"ORDER BY {order_sql}")

        # LIMIT & OFFSET
        if self.limit is not None:
            parts.append(f"LIMIT {self.limit}")
        if self.offset is not None:
            parts.append(f"OFFSET {self.offset}")

        sql = "\n".join(parts)
        return sql, params

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "select_columns": [
                {
                    "name": col.name,
                    "table": col.table,
                    "alias": col.alias,
                    "aggregate": col.aggregate.value if col.aggregate else None
                }
                for col in self.select_columns
            ],
            "from_table": {
                "name": self.from_table.name,
                "alias": self.from_table.alias,
                "schema": self.from_table.schema
            } if self.from_table else None,
            "joins": [
                {
                    "type": join.join_type.value,
                    "table": join.table.name,
                    "on_left": join.on_left.name,
                    "on_right": join.on_right.name
                }
                for join in self.joins
            ],
            "filters": [
                {
                    "column": f.column.name,
                    "operator": f.operator.value,
                    "value": f.value,
                    "logic": f.logic
                }
                for f in self.filters
            ],
            "distinct": self.distinct,
            "limit": self.limit,
            "offset": self.offset
        }

    def clone(self) -> 'Query':
        """Create a copy of this query"""
        new_query = Query()
        new_query.select_columns = self.select_columns.copy()
        new_query.from_table = self.from_table
        new_query.joins = self.joins.copy()
        new_query.filters = self.filters.copy()
        new_query.group_by = self.group_by
        new_query.order_by = self.order_by.copy()
        new_query.limit = self.limit
        new_query.offset = self.offset
        new_query.distinct = self.distinct
        return new_query


class QueryBuilder:
    """
    Query Builder with template support and query history
    """

    def __init__(self):
        self.queries: Dict[str, Query] = {}
        self.templates: Dict[str, Dict[str, Any]] = {}
        self.history: List[Dict[str, Any]] = []

    def create_query(self, name: Optional[str] = None) -> Query:
        """Create a new query"""
        query = Query()
        if name:
            self.queries[name] = query
        return query

    def save_query(self, name: str, query: Query, description: str = "") -> None:
        """Save a query"""
        self.queries[name] = query
        self.add_to_history(name, query, description)

    def get_query(self, name: str) -> Query:
        """Get a saved query"""
        if name not in self.queries:
            raise ValueError(f"Query '{name}' not found")
        return self.queries[name]

    def delete_query(self, name: str) -> None:
        """Delete a saved query"""
        if name in self.queries:
            del self.queries[name]

    def list_queries(self) -> List[str]:
        """List all saved queries"""
        return list(self.queries.keys())

    def save_template(self, name: str, query: Query, description: str = "", tags: List[str] = None) -> None:
        """Save a query template"""
        self.templates[name] = {
            "query": query.to_dict(),
            "description": description,
            "tags": tags or [],
            "created_at": datetime.now().isoformat()
        }

    def get_template(self, name: str) -> Query:
        """Get a query template"""
        if name not in self.templates:
            raise ValueError(f"Template '{name}' not found")

        # Reconstruct query from dict
        template_data = self.templates[name]["query"]
        query = Query()

        # Reconstruct from_table
        if template_data["from_table"]:
            query.from_table = TableRef(**template_data["from_table"])

        # Reconstruct select columns
        for col_data in template_data["select_columns"]:
            col = Column(
                name=col_data["name"],
                table=col_data["table"],
                alias=col_data["alias"]
            )
            if col_data["aggregate"]:
                col.aggregate = AggregateFunction(col_data["aggregate"])
            query.select_columns.append(col)

        # Other properties
        query.distinct = template_data["distinct"]
        query.limit = template_data["limit"]
        query.offset = template_data["offset"]

        return query

    def list_templates(self, tag: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all templates, optionally filtered by tag"""
        templates = []
        for name, data in self.templates.items():
            if tag and tag not in data["tags"]:
                continue
            templates.append({
                "name": name,
                "description": data["description"],
                "tags": data["tags"],
                "created_at": data["created_at"]
            })
        return templates

    def add_to_history(self, name: str, query: Query, description: str = "") -> None:
        """Add query to history"""
        sql, params = query.to_sql()
        self.history.append({
            "name": name,
            "description": description,
            "sql": sql,
            "params": params,
            "timestamp": datetime.now().isoformat()
        })

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get query history"""
        return self.history[-limit:]

    def export_queries(self, filepath: str) -> None:
        """Export queries to JSON file"""
        data = {
            "queries": {
                name: query.to_dict()
                for name, query in self.queries.items()
            },
            "templates": self.templates,
            "exported_at": datetime.now().isoformat()
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def import_queries(self, filepath: str) -> None:
        """Import queries from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Import queries
        for name, query_dict in data.get("queries", {}).items():
            query = self._dict_to_query(query_dict)
            self.queries[name] = query

        # Import templates
        self.templates.update(data.get("templates", {}))

    def _dict_to_query(self, query_dict: Dict[str, Any]) -> Query:
        """Convert dictionary to Query object"""
        query = Query()

        if query_dict.get("from_table"):
            query.from_table = TableRef(**query_dict["from_table"])

        for col_data in query_dict.get("select_columns", []):
            col = Column(
                name=col_data["name"],
                table=col_data.get("table"),
                alias=col_data.get("alias")
            )
            if col_data.get("aggregate"):
                col.aggregate = AggregateFunction(col_data["aggregate"])
            query.select_columns.append(col)

        query.distinct = query_dict.get("distinct", False)
        query.limit = query_dict.get("limit")
        query.offset = query_dict.get("offset")

        return query
