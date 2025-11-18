"""Data models for log entries and search."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LogLevelEnum(str, Enum):
    """Log level enumeration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogEntry(BaseModel):
    """Model for a log entry."""

    timestamp: datetime
    level: LogLevelEnum
    logger_name: str
    message: str
    app: str = "nexus"
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    traceback: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    extra: Optional[Dict[str, Any]] = None

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class LogSearchQuery(BaseModel):
    """Model for log search query parameters."""

    start_time: Optional[datetime] = Field(
        None, description="Start of time range for search"
    )
    end_time: Optional[datetime] = Field(
        None, description="End of time range for search"
    )
    level: Optional[LogLevelEnum] = Field(
        None, description="Filter by log level"
    )
    logger_name: Optional[str] = Field(
        None, description="Filter by logger name"
    )
    request_id: Optional[str] = Field(
        None, description="Filter by request ID"
    )
    user_id: Optional[str] = Field(
        None, description="Filter by user ID"
    )
    search_text: Optional[str] = Field(
        None, description="Search in log messages"
    )
    error_type: Optional[str] = Field(
        None, description="Filter by error type"
    )
    limit: int = Field(
        100, ge=1, le=1000, description="Maximum number of results"
    )
    offset: int = Field(
        0, ge=0, description="Offset for pagination"
    )
    sort_order: str = Field(
        "desc", description="Sort order: 'asc' or 'desc'"
    )

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class LogSearchResponse(BaseModel):
    """Model for log search response."""

    logs: List[LogEntry]
    total_count: int
    offset: int
    limit: int
    has_more: bool

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class LogStats(BaseModel):
    """Model for log statistics."""

    total_logs: int
    error_count: int
    warning_count: int
    info_count: int
    debug_count: int
    critical_count: int
    time_range: Dict[str, datetime]
    top_errors: List[Dict[str, Any]]
    logs_per_hour: List[Dict[str, Any]]

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}
