"""
Schema Designer

Visual database schema designer with ER diagrams, table designer,
relationships, indexes, constraints, and migrations.
"""

from typing import Dict, Any, List, Optional, Set, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json


class DataType(Enum):
    """SQL data types"""
    # Numeric
    INTEGER = "INTEGER"
    BIGINT = "BIGINT"
    SMALLINT = "SMALLINT"
    DECIMAL = "DECIMAL"
    NUMERIC = "NUMERIC"
    FLOAT = "FLOAT"
    REAL = "REAL"
    DOUBLE = "DOUBLE PRECISION"

    # String
    VARCHAR = "VARCHAR"
    CHAR = "CHAR"
    TEXT = "TEXT"
    MEDIUMTEXT = "MEDIUMTEXT"
    LONGTEXT = "LONGTEXT"

    # Date/Time
    DATE = "DATE"
    TIME = "TIME"
    TIMESTAMP = "TIMESTAMP"
    DATETIME = "DATETIME"

    # Boolean
    BOOLEAN = "BOOLEAN"

    # Binary
    BLOB = "BLOB"
    BYTEA = "BYTEA"

    # JSON
    JSON = "JSON"
    JSONB = "JSONB"

    # UUID
    UUID = "UUID"


class RelationshipType(Enum):
    """Entity relationship types"""
    ONE_TO_ONE = "1:1"
    ONE_TO_MANY = "1:N"
    MANY_TO_MANY = "N:M"


class ConstraintType(Enum):
    """Constraint types"""
    PRIMARY_KEY = "PRIMARY KEY"
    FOREIGN_KEY = "FOREIGN KEY"
    UNIQUE = "UNIQUE"
    CHECK = "CHECK"
    NOT_NULL = "NOT NULL"
    DEFAULT = "DEFAULT"


class IndexType(Enum):
    """Index types"""
    BTREE = "BTREE"
    HASH = "HASH"
    GIN = "GIN"
    GIST = "GIST"
    BRIN = "BRIN"


class OnAction(Enum):
    """Foreign key actions"""
    CASCADE = "CASCADE"
    SET_NULL = "SET NULL"
    SET_DEFAULT = "SET DEFAULT"
    RESTRICT = "RESTRICT"
    NO_ACTION = "NO ACTION"


@dataclass
class ColumnDefinition:
    """Table column definition"""
    name: str
    data_type: DataType
    length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None
    nullable: bool = True
    default: Optional[str] = None
    auto_increment: bool = False
    comment: Optional[str] = None

    def to_sql(self, dialect: str = "postgresql") -> str:
        """Convert to SQL DDL"""
        parts = [self.name]

        # Data type with length/precision
        type_str = self.data_type.value
        if self.length:
            type_str += f"({self.length})"
        elif self.precision:
            if self.scale:
                type_str += f"({self.precision},{self.scale})"
            else:
                type_str += f"({self.precision})"

        parts.append(type_str)

        # Constraints
        if not self.nullable:
            parts.append("NOT NULL")

        if self.default:
            parts.append(f"DEFAULT {self.default}")

        if self.auto_increment:
            if dialect == "postgresql":
                parts.insert(1, "SERIAL" if self.data_type == DataType.INTEGER else "BIGSERIAL")
            elif dialect == "mysql":
                parts.append("AUTO_INCREMENT")

        return " ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "data_type": self.data_type.value,
            "length": self.length,
            "precision": self.precision,
            "scale": self.scale,
            "nullable": self.nullable,
            "default": self.default,
            "auto_increment": self.auto_increment,
            "comment": self.comment
        }


@dataclass
class Index:
    """Table index"""
    name: str
    columns: List[str]
    unique: bool = False
    index_type: IndexType = IndexType.BTREE
    where: Optional[str] = None  # Partial index

    def to_sql(self, table_name: str, dialect: str = "postgresql") -> str:
        """Convert to SQL DDL"""
        unique_str = "UNIQUE " if self.unique else ""
        columns_str = ", ".join(self.columns)

        if dialect == "postgresql":
            type_str = f"USING {self.index_type.value}" if self.index_type != IndexType.BTREE else ""
            where_str = f" WHERE {self.where}" if self.where else ""
            return f"CREATE {unique_str}INDEX {self.name} ON {table_name} {type_str} ({columns_str}){where_str}"
        else:
            return f"CREATE {unique_str}INDEX {self.name} ON {table_name} ({columns_str})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "columns": self.columns,
            "unique": self.unique,
            "index_type": self.index_type.value,
            "where": self.where
        }


@dataclass
class ForeignKey:
    """Foreign key constraint"""
    name: str
    columns: List[str]
    ref_table: str
    ref_columns: List[str]
    on_delete: OnAction = OnAction.NO_ACTION
    on_update: OnAction = OnAction.NO_ACTION

    def to_sql(self) -> str:
        """Convert to SQL DDL"""
        columns_str = ", ".join(self.columns)
        ref_columns_str = ", ".join(self.ref_columns)

        return (
            f"CONSTRAINT {self.name} FOREIGN KEY ({columns_str}) "
            f"REFERENCES {self.ref_table}({ref_columns_str}) "
            f"ON DELETE {self.on_delete.value} "
            f"ON UPDATE {self.on_update.value}"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "columns": self.columns,
            "ref_table": self.ref_table,
            "ref_columns": self.ref_columns,
            "on_delete": self.on_delete.value,
            "on_update": self.on_update.value
        }


@dataclass
class TableDefinition:
    """Table definition"""
    name: str
    columns: List[ColumnDefinition] = field(default_factory=list)
    primary_key: List[str] = field(default_factory=list)
    foreign_keys: List[ForeignKey] = field(default_factory=list)
    indexes: List[Index] = field(default_factory=list)
    unique_constraints: List[List[str]] = field(default_factory=list)
    check_constraints: Dict[str, str] = field(default_factory=dict)
    comment: Optional[str] = None
    schema: Optional[str] = None

    # Visual properties for ER diagram
    position_x: int = 0
    position_y: int = 0

    def get_full_name(self) -> str:
        """Get full table name with schema"""
        if self.schema:
            return f"{self.schema}.{self.name}"
        return self.name

    def add_column(self, column: ColumnDefinition) -> None:
        """Add a column"""
        if any(c.name == column.name for c in self.columns):
            raise ValueError(f"Column '{column.name}' already exists")
        self.columns.append(column)

    def remove_column(self, column_name: str) -> None:
        """Remove a column"""
        self.columns = [c for c in self.columns if c.name != column_name]

        # Remove from constraints
        self.primary_key = [pk for pk in self.primary_key if pk != column_name]
        self.foreign_keys = [
            fk for fk in self.foreign_keys
            if column_name not in fk.columns
        ]
        self.indexes = [
            idx for idx in self.indexes
            if column_name not in idx.columns
        ]

    def get_column(self, column_name: str) -> Optional[ColumnDefinition]:
        """Get column by name"""
        for col in self.columns:
            if col.name == column_name:
                return col
        return None

    def to_create_sql(self, dialect: str = "postgresql") -> str:
        """Generate CREATE TABLE SQL"""
        lines = [f"CREATE TABLE {self.get_full_name()} ("]

        # Columns
        column_defs = [f"  {col.to_sql(dialect)}" for col in self.columns]

        # Primary key
        if self.primary_key:
            pk_cols = ", ".join(self.primary_key)
            column_defs.append(f"  PRIMARY KEY ({pk_cols})")

        # Foreign keys
        for fk in self.foreign_keys:
            column_defs.append(f"  {fk.to_sql()}")

        # Unique constraints
        for idx, unique_cols in enumerate(self.unique_constraints):
            cols_str = ", ".join(unique_cols)
            column_defs.append(f"  CONSTRAINT {self.name}_unique_{idx} UNIQUE ({cols_str})")

        # Check constraints
        for name, condition in self.check_constraints.items():
            column_defs.append(f"  CONSTRAINT {name} CHECK ({condition})")

        lines.append(",\n".join(column_defs))
        lines.append(")")

        sql = "\n".join(lines) + ";"

        # Add comment
        if self.comment and dialect == "postgresql":
            sql += f"\n\nCOMMENT ON TABLE {self.get_full_name()} IS '{self.comment}';"

        return sql

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "schema": self.schema,
            "columns": [col.to_dict() for col in self.columns],
            "primary_key": self.primary_key,
            "foreign_keys": [fk.to_dict() for fk in self.foreign_keys],
            "indexes": [idx.to_dict() for idx in self.indexes],
            "unique_constraints": self.unique_constraints,
            "check_constraints": self.check_constraints,
            "comment": self.comment,
            "position_x": self.position_x,
            "position_y": self.position_y
        }


@dataclass
class Relationship:
    """Entity relationship for ER diagram"""
    name: str
    from_table: str
    to_table: str
    from_columns: List[str]
    to_columns: List[str]
    relationship_type: RelationshipType
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "from_table": self.from_table,
            "to_table": self.to_table,
            "from_columns": self.from_columns,
            "to_columns": self.to_columns,
            "relationship_type": self.relationship_type.value,
            "description": self.description
        }


class Schema:
    """Database schema"""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.tables: Dict[str, TableDefinition] = {}
        self.relationships: List[Relationship] = []
        self.created_at = datetime.now()
        self.modified_at = datetime.now()

    def add_table(self, table: TableDefinition) -> None:
        """Add a table"""
        if table.name in self.tables:
            raise ValueError(f"Table '{table.name}' already exists")
        self.tables[table.name] = table
        self.modified_at = datetime.now()

    def remove_table(self, table_name: str) -> None:
        """Remove a table"""
        if table_name not in self.tables:
            raise ValueError(f"Table '{table_name}' not found")

        # Remove relationships
        self.relationships = [
            rel for rel in self.relationships
            if rel.from_table != table_name and rel.to_table != table_name
        ]

        # Remove foreign keys referencing this table
        for table in self.tables.values():
            table.foreign_keys = [
                fk for fk in table.foreign_keys
                if fk.ref_table != table_name
            ]

        del self.tables[table_name]
        self.modified_at = datetime.now()

    def get_table(self, table_name: str) -> Optional[TableDefinition]:
        """Get table by name"""
        return self.tables.get(table_name)

    def add_relationship(self, relationship: Relationship) -> None:
        """Add a relationship"""
        if relationship.from_table not in self.tables:
            raise ValueError(f"Table '{relationship.from_table}' not found")
        if relationship.to_table not in self.tables:
            raise ValueError(f"Table '{relationship.to_table}' not found")

        self.relationships.append(relationship)
        self.modified_at = datetime.now()

    def get_table_relationships(self, table_name: str) -> List[Relationship]:
        """Get all relationships for a table"""
        return [
            rel for rel in self.relationships
            if rel.from_table == table_name or rel.to_table == table_name
        ]

    def generate_ddl(self, dialect: str = "postgresql") -> str:
        """Generate DDL for entire schema"""
        ddl_parts = []

        # Create tables
        for table in self.tables.values():
            ddl_parts.append(table.to_create_sql(dialect))
            ddl_parts.append("")

        # Create indexes
        for table in self.tables.values():
            for index in table.indexes:
                ddl_parts.append(index.to_sql(table.name, dialect) + ";")

        return "\n".join(ddl_parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "tables": {
                name: table.to_dict()
                for name, table in self.tables.items()
            },
            "relationships": [rel.to_dict() for rel in self.relationships],
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat()
        }

    def to_er_diagram_data(self) -> Dict[str, Any]:
        """Generate data for ER diagram visualization"""
        nodes = []
        edges = []

        # Create nodes for tables
        for table in self.tables.values():
            node = {
                "id": table.name,
                "label": table.name,
                "x": table.position_x,
                "y": table.position_y,
                "columns": [
                    {
                        "name": col.name,
                        "type": col.data_type.value,
                        "pk": col.name in table.primary_key,
                        "nullable": col.nullable
                    }
                    for col in table.columns
                ]
            }
            nodes.append(node)

        # Create edges for relationships
        for rel in self.relationships:
            edge = {
                "from": rel.from_table,
                "to": rel.to_table,
                "label": rel.relationship_type.value,
                "description": rel.description
            }
            edges.append(edge)

        return {"nodes": nodes, "edges": edges}


class SchemaDesigner:
    """
    Visual Schema Designer

    Design database schemas with ER diagrams, manage tables, relationships,
    indexes, and constraints.
    """

    def __init__(self):
        self.schemas: Dict[str, Schema] = {}
        self.active_schema: Optional[str] = None

    def create_schema(self, name: str, description: str = "") -> Schema:
        """Create a new schema"""
        if name in self.schemas:
            raise ValueError(f"Schema '{name}' already exists")

        schema = Schema(name, description)
        self.schemas[name] = schema
        self.active_schema = name
        return schema

    def get_schema(self, name: Optional[str] = None) -> Schema:
        """Get schema by name or active schema"""
        schema_name = name or self.active_schema
        if not schema_name:
            raise ValueError("No schema specified and no active schema")
        if schema_name not in self.schemas:
            raise ValueError(f"Schema '{schema_name}' not found")
        return self.schemas[schema_name]

    def delete_schema(self, name: str) -> None:
        """Delete a schema"""
        if name not in self.schemas:
            raise ValueError(f"Schema '{name}' not found")
        del self.schemas[name]
        if self.active_schema == name:
            self.active_schema = None

    def set_active_schema(self, name: str) -> None:
        """Set active schema"""
        if name not in self.schemas:
            raise ValueError(f"Schema '{name}' not found")
        self.active_schema = name

    def list_schemas(self) -> List[Dict[str, Any]]:
        """List all schemas"""
        return [
            {
                "name": name,
                "description": schema.description,
                "tables": len(schema.tables),
                "created_at": schema.created_at.isoformat(),
                "modified_at": schema.modified_at.isoformat()
            }
            for name, schema in self.schemas.items()
        ]

    def create_table_builder(self, table_name: str) -> 'TableBuilder':
        """Create a table builder"""
        return TableBuilder(table_name)

    def import_from_database(self, connection, schema_name: str = "imported") -> Schema:
        """Import schema from existing database"""
        schema = self.create_schema(schema_name, "Imported from database")

        # Get tables
        tables = connection.get_tables()

        for table_name in tables:
            # Get table schema
            columns_info = connection.get_table_schema(table_name)

            # Create table definition
            table = TableDefinition(name=table_name)

            # Add columns
            for col_info in columns_info:
                column = self._convert_column_info(col_info)
                table.add_column(column)

            schema.add_table(table)

        return schema

    def _convert_column_info(self, col_info: Dict[str, Any]) -> ColumnDefinition:
        """Convert database column info to ColumnDefinition"""
        # This is a simplified conversion - real implementation would need
        # to handle different database types and their specific column info formats
        data_type_str = col_info.get("data_type", "TEXT").upper()

        try:
            data_type = DataType[data_type_str]
        except KeyError:
            data_type = DataType.TEXT

        return ColumnDefinition(
            name=col_info.get("column_name", ""),
            data_type=data_type,
            nullable=col_info.get("is_nullable", "YES") == "YES",
            default=col_info.get("column_default")
        )

    def export_schema(self, schema_name: str, filepath: str, format: str = "json") -> None:
        """Export schema to file"""
        schema = self.get_schema(schema_name)

        if format == "json":
            with open(filepath, 'w') as f:
                json.dump(schema.to_dict(), f, indent=2)
        elif format == "sql":
            with open(filepath, 'w') as f:
                f.write(schema.generate_ddl())
        else:
            raise ValueError(f"Unsupported format: {format}")

    def import_schema(self, filepath: str) -> Schema:
        """Import schema from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        schema = Schema(data["name"], data.get("description", ""))

        # Import tables
        for table_name, table_data in data.get("tables", {}).items():
            table = self._dict_to_table(table_data)
            schema.add_table(table)

        # Import relationships
        for rel_data in data.get("relationships", []):
            rel = Relationship(
                name=rel_data["name"],
                from_table=rel_data["from_table"],
                to_table=rel_data["to_table"],
                from_columns=rel_data["from_columns"],
                to_columns=rel_data["to_columns"],
                relationship_type=RelationshipType(rel_data["relationship_type"]),
                description=rel_data.get("description")
            )
            schema.add_relationship(rel)

        self.schemas[schema.name] = schema
        return schema

    def _dict_to_table(self, table_data: Dict[str, Any]) -> TableDefinition:
        """Convert dictionary to TableDefinition"""
        table = TableDefinition(
            name=table_data["name"],
            schema=table_data.get("schema"),
            comment=table_data.get("comment"),
            position_x=table_data.get("position_x", 0),
            position_y=table_data.get("position_y", 0)
        )

        # Add columns
        for col_data in table_data.get("columns", []):
            col = ColumnDefinition(
                name=col_data["name"],
                data_type=DataType(col_data["data_type"]),
                length=col_data.get("length"),
                precision=col_data.get("precision"),
                scale=col_data.get("scale"),
                nullable=col_data.get("nullable", True),
                default=col_data.get("default"),
                auto_increment=col_data.get("auto_increment", False),
                comment=col_data.get("comment")
            )
            table.add_column(col)

        # Add constraints
        table.primary_key = table_data.get("primary_key", [])
        table.unique_constraints = table_data.get("unique_constraints", [])
        table.check_constraints = table_data.get("check_constraints", {})

        return table


class TableBuilder:
    """Fluent interface for building tables"""

    def __init__(self, name: str):
        self.table = TableDefinition(name=name)

    def add_column(
        self,
        name: str,
        data_type: DataType,
        **kwargs
    ) -> 'TableBuilder':
        """Add a column"""
        column = ColumnDefinition(name=name, data_type=data_type, **kwargs)
        self.table.add_column(column)
        return self

    def primary_key(self, *columns: str) -> 'TableBuilder':
        """Set primary key"""
        self.table.primary_key = list(columns)
        return self

    def add_foreign_key(
        self,
        columns: List[str],
        ref_table: str,
        ref_columns: List[str],
        name: Optional[str] = None,
        **kwargs
    ) -> 'TableBuilder':
        """Add foreign key"""
        if not name:
            name = f"fk_{self.table.name}_{'_'.join(columns)}"

        fk = ForeignKey(
            name=name,
            columns=columns,
            ref_table=ref_table,
            ref_columns=ref_columns,
            **kwargs
        )
        self.table.foreign_keys.append(fk)
        return self

    def add_index(
        self,
        columns: List[str],
        name: Optional[str] = None,
        **kwargs
    ) -> 'TableBuilder':
        """Add index"""
        if not name:
            name = f"idx_{self.table.name}_{'_'.join(columns)}"

        index = Index(name=name, columns=columns, **kwargs)
        self.table.indexes.append(index)
        return self

    def add_unique(self, *columns: str) -> 'TableBuilder':
        """Add unique constraint"""
        self.table.unique_constraints.append(list(columns))
        return self

    def add_check(self, name: str, condition: str) -> 'TableBuilder':
        """Add check constraint"""
        self.table.check_constraints[name] = condition
        return self

    def set_comment(self, comment: str) -> 'TableBuilder':
        """Set table comment"""
        self.table.comment = comment
        return self

    def build(self) -> TableDefinition:
        """Build and return table"""
        return self.table
