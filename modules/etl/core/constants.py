"""Constants and enums for ETL module."""
from enum import Enum


class SourceType(str, Enum):
    """Data source types."""

    CSV = "csv"
    JSON = "json"
    XML = "xml"
    EXCEL = "excel"
    SQL = "sql"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"
    API = "api"
    REST_API = "rest_api"
    GRAPHQL = "graphql"
    S3 = "s3"
    FTP = "ftp"
    SFTP = "sftp"
    KAFKA = "kafka"
    RABBITMQ = "rabbitmq"


class TransformationType(str, Enum):
    """Transformation types."""

    RENAME_COLUMNS = "rename_columns"
    SELECT_COLUMNS = "select_columns"
    DROP_COLUMNS = "drop_columns"
    FILTER_ROWS = "filter_rows"
    CONVERT_TYPE = "convert_type"
    FILL_NULL = "fill_null"
    DROP_NULL = "drop_null"
    REPLACE_VALUE = "replace_value"
    AGGREGATE = "aggregate"
    GROUP_BY = "group_by"
    JOIN = "join"
    MERGE = "merge"
    CONCAT = "concat"
    PIVOT = "pivot"
    UNPIVOT = "unpivot"
    SORT = "sort"
    DEDUPLICATE = "deduplicate"
    CUSTOM_FUNCTION = "custom_function"
    REGEX_EXTRACT = "regex_extract"
    STRING_OPERATION = "string_operation"
    DATE_OPERATION = "date_operation"
    MATH_OPERATION = "math_operation"


class ExecutionStatus(str, Enum):
    """ETL execution statuses."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class ValidationRule(str, Enum):
    """Data validation rule types."""

    NOT_NULL = "not_null"
    UNIQUE = "unique"
    RANGE = "range"
    REGEX = "regex"
    TYPE_CHECK = "type_check"
    CUSTOM = "custom"
    FOREIGN_KEY = "foreign_key"
    MIN_LENGTH = "min_length"
    MAX_LENGTH = "max_length"
    IN_LIST = "in_list"
