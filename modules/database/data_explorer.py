"""
Data Explorer

Browse tables, filter/sort data, perform CRUD operations,
bulk operations, and export data.
"""

from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
import csv
import io
from enum import Enum


class ExportFormat(Enum):
    """Export format types"""
    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"
    SQL = "sql"
    XML = "xml"


@dataclass
class FilterCondition:
    """Data filter condition"""
    column: str
    operator: str  # =, !=, >, <, >=, <=, LIKE, IN, etc.
    value: Any
    logic: str = "AND"  # AND/OR


@dataclass
class SortCondition:
    """Data sort condition"""
    column: str
    ascending: bool = True


@dataclass
class PaginationInfo:
    """Pagination information"""
    page: int = 1
    page_size: int = 50
    total_records: int = 0
    total_pages: int = 0

    def get_offset(self) -> int:
        """Get SQL OFFSET value"""
        return (self.page - 1) * self.page_size

    def set_total_records(self, total: int) -> None:
        """Set total records and calculate pages"""
        self.total_records = total
        self.total_pages = (total + self.page_size - 1) // self.page_size


@dataclass
class DataGrid:
    """Data grid result"""
    columns: List[str]
    rows: List[Dict[str, Any]]
    pagination: PaginationInfo
    total_records: int
    query_time_ms: float


class DataExplorer:
    """
    Data Explorer

    Browse and manipulate table data with filtering, sorting,
    pagination, and CRUD operations.
    """

    def __init__(self, connection):
        """
        Initialize data explorer

        Args:
            connection: DatabaseConnection instance
        """
        self.connection = connection
        self.current_table: Optional[str] = None
        self.filters: List[FilterCondition] = []
        self.sorts: List[SortCondition] = []
        self.pagination = PaginationInfo()

    def browse_table(
        self,
        table_name: str,
        columns: Optional[List[str]] = None,
        filters: Optional[List[FilterCondition]] = None,
        sorts: Optional[List[SortCondition]] = None,
        page: int = 1,
        page_size: int = 50
    ) -> DataGrid:
        """
        Browse table data with filters and pagination

        Args:
            table_name: Table name
            columns: Columns to select (None = all)
            filters: Filter conditions
            sorts: Sort conditions
            page: Page number
            page_size: Records per page

        Returns:
            DataGrid with results
        """
        self.current_table = table_name
        self.filters = filters or []
        self.sorts = sorts or []
        self.pagination.page = page
        self.pagination.page_size = page_size

        start_time = datetime.now()

        # Build SELECT query
        query, params = self._build_select_query(table_name, columns)

        # Get total count
        count_query, count_params = self._build_count_query(table_name)
        count_result = self.connection.execute_query(count_query, count_params)
        total_records = list(count_result[0].values())[0] if count_result else 0

        # Execute query
        results = self.connection.execute_query(query, params)

        # Calculate query time
        query_time = (datetime.now() - start_time).total_seconds() * 1000

        # Update pagination
        self.pagination.set_total_records(total_records)

        # Get columns
        columns_list = list(results[0].keys()) if results else []

        return DataGrid(
            columns=columns_list,
            rows=results,
            pagination=self.pagination,
            total_records=total_records,
            query_time_ms=query_time
        )

    def _build_select_query(
        self,
        table_name: str,
        columns: Optional[List[str]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """Build SELECT query with filters, sorts, and pagination"""
        params = {}

        # SELECT clause
        if columns:
            select_clause = ", ".join(columns)
        else:
            select_clause = "*"

        query_parts = [f"SELECT {select_clause} FROM {table_name}"]

        # WHERE clause
        if self.filters:
            where_parts = []
            for i, filter_cond in enumerate(self.filters):
                param_name = f"filter_{i}"
                where_parts.append(f"{filter_cond.column} {filter_cond.operator} :{param_name}")
                params[param_name] = filter_cond.value

            logic = self.filters[0].logic if self.filters else "AND"
            where_clause = f" {logic} ".join(where_parts)
            query_parts.append(f"WHERE {where_clause}")

        # ORDER BY clause
        if self.sorts:
            order_parts = []
            for sort_cond in self.sorts:
                direction = "ASC" if sort_cond.ascending else "DESC"
                order_parts.append(f"{sort_cond.column} {direction}")

            order_clause = ", ".join(order_parts)
            query_parts.append(f"ORDER BY {order_clause}")

        # LIMIT and OFFSET
        query_parts.append(f"LIMIT {self.pagination.page_size}")
        query_parts.append(f"OFFSET {self.pagination.get_offset()}")

        query = " ".join(query_parts)
        return query, params

    def _build_count_query(self, table_name: str) -> Tuple[str, Dict[str, Any]]:
        """Build COUNT query"""
        params = {}
        query_parts = [f"SELECT COUNT(*) as total FROM {table_name}"]

        # WHERE clause (same as select query)
        if self.filters:
            where_parts = []
            for i, filter_cond in enumerate(self.filters):
                param_name = f"filter_{i}"
                where_parts.append(f"{filter_cond.column} {filter_cond.operator} :{param_name}")
                params[param_name] = filter_cond.value

            logic = self.filters[0].logic if self.filters else "AND"
            where_clause = f" {logic} ".join(where_parts)
            query_parts.append(f"WHERE {where_clause}")

        query = " ".join(query_parts)
        return query, params

    def insert_row(self, table_name: str, data: Dict[str, Any]) -> int:
        """
        Insert a new row

        Args:
            table_name: Table name
            data: Column-value pairs

        Returns:
            Number of rows inserted
        """
        columns = list(data.keys())
        placeholders = [f":{col}" for col in columns]

        query = (
            f"INSERT INTO {table_name} ({', '.join(columns)}) "
            f"VALUES ({', '.join(placeholders)})"
        )

        return self.connection.execute_command(query, data)

    def update_row(
        self,
        table_name: str,
        data: Dict[str, Any],
        where: Dict[str, Any]
    ) -> int:
        """
        Update row(s)

        Args:
            table_name: Table name
            data: Column-value pairs to update
            where: WHERE conditions

        Returns:
            Number of rows updated
        """
        # SET clause
        set_parts = [f"{col} = :set_{col}" for col in data.keys()]
        set_clause = ", ".join(set_parts)

        # WHERE clause
        where_parts = [f"{col} = :where_{col}" for col in where.keys()]
        where_clause = " AND ".join(where_parts)

        query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"

        # Combine parameters
        params = {f"set_{k}": v for k, v in data.items()}
        params.update({f"where_{k}": v for k, v in where.items()})

        return self.connection.execute_command(query, params)

    def delete_row(self, table_name: str, where: Dict[str, Any]) -> int:
        """
        Delete row(s)

        Args:
            table_name: Table name
            where: WHERE conditions

        Returns:
            Number of rows deleted
        """
        where_parts = [f"{col} = :{col}" for col in where.keys()]
        where_clause = " AND ".join(where_parts)

        query = f"DELETE FROM {table_name} WHERE {where_clause}"

        return self.connection.execute_command(query, where)

    def bulk_insert(self, table_name: str, rows: List[Dict[str, Any]]) -> int:
        """
        Bulk insert rows

        Args:
            table_name: Table name
            rows: List of row data

        Returns:
            Total rows inserted
        """
        if not rows:
            return 0

        total_inserted = 0

        with self.connection.transaction():
            for row in rows:
                total_inserted += self.insert_row(table_name, row)

        return total_inserted

    def bulk_update(
        self,
        table_name: str,
        updates: List[Dict[str, Any]],
        key_column: str
    ) -> int:
        """
        Bulk update rows

        Args:
            table_name: Table name
            updates: List of updates with key column
            key_column: Column to use as key

        Returns:
            Total rows updated
        """
        if not updates:
            return 0

        total_updated = 0

        with self.connection.transaction():
            for update in updates:
                if key_column not in update:
                    continue

                where = {key_column: update[key_column]}
                data = {k: v for k, v in update.items() if k != key_column}

                total_updated += self.update_row(table_name, data, where)

        return total_updated

    def bulk_delete(self, table_name: str, conditions: List[Dict[str, Any]]) -> int:
        """
        Bulk delete rows

        Args:
            table_name: Table name
            conditions: List of WHERE conditions

        Returns:
            Total rows deleted
        """
        if not conditions:
            return 0

        total_deleted = 0

        with self.connection.transaction():
            for condition in conditions:
                total_deleted += self.delete_row(table_name, condition)

        return total_deleted

    def truncate_table(self, table_name: str) -> None:
        """Truncate table (delete all rows)"""
        query = f"TRUNCATE TABLE {table_name}"
        self.connection.execute_command(query)

    def export_data(
        self,
        table_name: str,
        format: ExportFormat,
        filepath: Optional[str] = None,
        filters: Optional[List[FilterCondition]] = None,
        columns: Optional[List[str]] = None
    ) -> Union[str, bytes]:
        """
        Export table data

        Args:
            table_name: Table name
            format: Export format
            filepath: Output file path (optional)
            filters: Filter conditions
            columns: Columns to export

        Returns:
            Exported data as string or bytes
        """
        # Get data
        old_filters = self.filters
        self.filters = filters or []

        # Get all data (no pagination)
        query, params = self._build_select_query(table_name, columns)
        query = query.split("LIMIT")[0]  # Remove pagination
        results = self.connection.execute_query(query, params)

        self.filters = old_filters

        # Export based on format
        if format == ExportFormat.CSV:
            output = self._export_to_csv(results)
        elif format == ExportFormat.JSON:
            output = self._export_to_json(results)
        elif format == ExportFormat.SQL:
            output = self._export_to_sql(table_name, results)
        elif format == ExportFormat.XML:
            output = self._export_to_xml(table_name, results)
        else:
            raise ValueError(f"Unsupported format: {format}")

        # Save to file if path provided
        if filepath:
            mode = 'wb' if isinstance(output, bytes) else 'w'
            with open(filepath, mode) as f:
                f.write(output)

        return output

    def _export_to_csv(self, data: List[Dict[str, Any]]) -> str:
        """Export to CSV"""
        if not data:
            return ""

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

        return output.getvalue()

    def _export_to_json(self, data: List[Dict[str, Any]]) -> str:
        """Export to JSON"""
        return json.dumps(data, indent=2, default=str)

    def _export_to_sql(self, table_name: str, data: List[Dict[str, Any]]) -> str:
        """Export to SQL INSERT statements"""
        if not data:
            return ""

        sql_lines = []

        for row in data:
            columns = list(row.keys())
            values = []

            for col in columns:
                value = row[col]
                if value is None:
                    values.append("NULL")
                elif isinstance(value, str):
                    values.append(f"'{value.replace('\'', '\'\'')}'")
                elif isinstance(value, (int, float)):
                    values.append(str(value))
                elif isinstance(value, bool):
                    values.append("TRUE" if value else "FALSE")
                elif isinstance(value, datetime):
                    values.append(f"'{value.isoformat()}'")
                else:
                    values.append(f"'{str(value)}'")

            columns_str = ", ".join(columns)
            values_str = ", ".join(values)
            sql_lines.append(f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str});")

        return "\n".join(sql_lines)

    def _export_to_xml(self, table_name: str, data: List[Dict[str, Any]]) -> str:
        """Export to XML"""
        lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        lines.append(f'<{table_name}_data>')

        for row in data:
            lines.append(f'  <row>')
            for key, value in row.items():
                lines.append(f'    <{key}>{self._escape_xml(str(value))}</{key}>')
            lines.append(f'  </row>')

        lines.append(f'</{table_name}_data>')
        return "\n".join(lines)

    def _escape_xml(self, text: str) -> str:
        """Escape XML special characters"""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;"))

    def import_data(
        self,
        table_name: str,
        format: ExportFormat,
        data: Union[str, bytes],
        truncate: bool = False
    ) -> int:
        """
        Import data into table

        Args:
            table_name: Table name
            format: Import format
            data: Data to import
            truncate: Truncate table before import

        Returns:
            Number of rows imported
        """
        if truncate:
            self.truncate_table(table_name)

        # Parse data based on format
        if format == ExportFormat.CSV:
            rows = self._import_from_csv(data)
        elif format == ExportFormat.JSON:
            rows = self._import_from_json(data)
        else:
            raise ValueError(f"Unsupported import format: {format}")

        # Bulk insert
        return self.bulk_insert(table_name, rows)

    def _import_from_csv(self, data: str) -> List[Dict[str, Any]]:
        """Import from CSV"""
        input_stream = io.StringIO(data)
        reader = csv.DictReader(input_stream)
        return list(reader)

    def _import_from_json(self, data: str) -> List[Dict[str, Any]]:
        """Import from JSON"""
        return json.loads(data)

    def search_table(
        self,
        table_name: str,
        search_text: str,
        columns: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Full-text search across table

        Args:
            table_name: Table name
            search_text: Text to search
            columns: Columns to search (None = all text columns)

        Returns:
            Matching rows
        """
        # Get table schema to find text columns
        schema = self.connection.get_table_schema(table_name)

        if columns is None:
            # Find text columns
            columns = []
            for col_info in schema:
                col_name = col_info.get('column_name') or col_info.get('name') or col_info.get('Field')
                data_type = str(col_info.get('data_type', '') or col_info.get('Type', '')).upper()

                if any(t in data_type for t in ['CHAR', 'TEXT', 'VARCHAR']):
                    columns.append(col_name)

        if not columns:
            return []

        # Build search query
        search_pattern = f"%{search_text}%"
        where_parts = [f"{col} LIKE :search" for col in columns]
        where_clause = " OR ".join(where_parts)

        query = f"SELECT * FROM {table_name} WHERE {where_clause}"
        params = {"search": search_pattern}

        return self.connection.execute_query(query, params)

    def get_distinct_values(
        self,
        table_name: str,
        column: str,
        limit: int = 100
    ) -> List[Any]:
        """
        Get distinct values for a column

        Args:
            table_name: Table name
            column: Column name
            limit: Maximum values to return

        Returns:
            List of distinct values
        """
        query = f"SELECT DISTINCT {column} FROM {table_name} ORDER BY {column} LIMIT {limit}"
        results = self.connection.execute_query(query)
        return [row[column] for row in results]

    def get_column_statistics(
        self,
        table_name: str,
        column: str
    ) -> Dict[str, Any]:
        """
        Get statistics for a column

        Args:
            table_name: Table name
            column: Column name

        Returns:
            Statistics dict
        """
        query = f"""
            SELECT
                COUNT(*) as count,
                COUNT({column}) as non_null_count,
                COUNT(DISTINCT {column}) as distinct_count,
                MIN({column}) as min_value,
                MAX({column}) as max_value
            FROM {table_name}
        """

        result = self.connection.execute_query(query)
        if result:
            stats = result[0]
            stats['null_count'] = stats['count'] - stats['non_null_count']
            return stats

        return {}

    def duplicate_table(
        self,
        source_table: str,
        target_table: str,
        with_data: bool = True,
        where: Optional[str] = None
    ) -> int:
        """
        Duplicate table

        Args:
            source_table: Source table name
            target_table: Target table name
            with_data: Copy data as well
            where: Optional WHERE clause for data

        Returns:
            Number of rows copied
        """
        # Create table structure
        create_query = f"CREATE TABLE {target_table} AS SELECT * FROM {source_table} WHERE 1=0"
        self.connection.execute_command(create_query)

        if not with_data:
            return 0

        # Copy data
        where_clause = f"WHERE {where}" if where else ""
        insert_query = f"INSERT INTO {target_table} SELECT * FROM {source_table} {where_clause}"
        return self.connection.execute_command(insert_query)

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get table information

        Args:
            table_name: Table name

        Returns:
            Table info dict
        """
        # Get row count
        count_query = f"SELECT COUNT(*) as total FROM {table_name}"
        count_result = self.connection.execute_query(count_query)
        row_count = count_result[0]['total'] if count_result else 0

        # Get schema
        schema = self.connection.get_table_schema(table_name)

        return {
            "name": table_name,
            "row_count": row_count,
            "column_count": len(schema),
            "columns": schema
        }
