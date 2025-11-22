"""
NEXUS Platform - Global Constants

Centralized constants, enums, and configuration values
used across the NEXUS platform.
"""

from enum import Enum, IntEnum


class EventType(str, Enum):
    """Event types for analytics tracking."""

    # User Events
    USER_SIGNUP = "user_signup"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"

    # Page Events
    PAGE_VIEW = "page_view"
    PAGE_EXIT = "page_exit"
    PAGE_SCROLL = "page_scroll"

    # Click Events
    BUTTON_CLICK = "button_click"
    LINK_CLICK = "link_click"
    ELEMENT_CLICK = "element_click"

    # Form Events
    FORM_START = "form_start"
    FORM_SUBMIT = "form_submit"
    FORM_ERROR = "form_error"
    FORM_ABANDON = "form_abandon"

    # Module Events
    MODULE_OPEN = "module_open"
    MODULE_CLOSE = "module_close"
    MODULE_INTERACTION = "module_interaction"

    # Document Events
    DOCUMENT_CREATE = "document_create"
    DOCUMENT_OPEN = "document_open"
    DOCUMENT_EDIT = "document_edit"
    DOCUMENT_SAVE = "document_save"
    DOCUMENT_DELETE = "document_delete"
    DOCUMENT_SHARE = "document_share"
    DOCUMENT_DOWNLOAD = "document_download"

    # AI Events
    AI_QUERY = "ai_query"
    AI_RESPONSE = "ai_response"
    AI_ERROR = "ai_error"

    # Error Events
    ERROR_CLIENT = "error_client"
    ERROR_SERVER = "error_server"
    ERROR_API = "error_api"

    # Conversion Events
    GOAL_COMPLETED = "goal_completed"
    CONVERSION = "conversion"
    CHECKOUT_START = "checkout_start"
    CHECKOUT_COMPLETE = "checkout_complete"
    PURCHASE = "purchase"

    # Search Events
    SEARCH_QUERY = "search_query"
    SEARCH_RESULT_CLICK = "search_result_click"

    # Session Events
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    SESSION_TIMEOUT = "session_timeout"

    # Custom Events
    CUSTOM = "custom"


class MetricType(str, Enum):
    """Metric types for analytics."""

    # Count Metrics
    COUNT = "count"
    UNIQUE_COUNT = "unique_count"

    # Aggregation Metrics
    SUM = "sum"
    AVERAGE = "average"
    MEDIAN = "median"
    MIN = "min"
    MAX = "max"

    # Time Metrics
    DURATION = "duration"
    FREQUENCY = "frequency"

    # Conversion Metrics
    CONVERSION_RATE = "conversion_rate"
    BOUNCE_RATE = "bounce_rate"
    EXIT_RATE = "exit_rate"

    # Engagement Metrics
    ENGAGEMENT_RATE = "engagement_rate"
    RETENTION_RATE = "retention_rate"
    CHURN_RATE = "churn_rate"

    # Distribution Metrics
    PERCENTILE = "percentile"
    DISTRIBUTION = "distribution"


class AggregationPeriod(str, Enum):
    """Time periods for data aggregation."""

    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class ExportFormat(str, Enum):
    """Supported export formats."""

    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"
    PDF = "pdf"
    PARQUET = "parquet"


class AnalyticsStatus(str, Enum):
    """Status codes for analytics operations."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ChartType(str, Enum):
    """Chart types for visualizations."""

    LINE = "line"
    BAR = "bar"
    AREA = "area"
    PIE = "pie"
    DONUT = "donut"
    SCATTER = "scatter"
    BUBBLE = "bubble"
    HEATMAP = "heatmap"
    FUNNEL = "funnel"
    GAUGE = "gauge"
    TABLE = "table"
    METRIC = "metric"


class AttributionModel(str, Enum):
    """Attribution models for conversion tracking."""

    FIRST_TOUCH = "first_touch"
    LAST_TOUCH = "last_touch"
    LINEAR = "linear"
    TIME_DECAY = "time_decay"
    POSITION_BASED = "position_based"
    DATA_DRIVEN = "data_driven"


class CohortType(str, Enum):
    """Cohort analysis types."""

    ACQUISITION = "acquisition"
    BEHAVIORAL = "behavioral"
    RETENTION = "retention"
    REVENUE = "revenue"


class FunnelStepStatus(str, Enum):
    """Funnel step completion status."""

    ENTERED = "entered"
    COMPLETED = "completed"
    DROPPED = "dropped"
    CONVERTED = "converted"


class ABTestStatus(str, Enum):
    """A/B test status."""

    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ABTestVariant(str, Enum):
    """A/B test variant identifiers."""

    CONTROL = "control"
    VARIANT_A = "variant_a"
    VARIANT_B = "variant_b"
    VARIANT_C = "variant_c"


class SessionReplayStatus(str, Enum):
    """Session replay recording status."""

    RECORDING = "recording"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class Priority(IntEnum):
    """Task priority levels."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


# Analytics Constants
DEFAULT_SESSION_TIMEOUT = 1800  # 30 minutes in seconds
MAX_EVENT_PROPERTIES = 100
MAX_PROPERTY_NAME_LENGTH = 255
MAX_PROPERTY_VALUE_LENGTH = 4096
MAX_BATCH_SIZE = 10000
MAX_QUERY_RESULTS = 100000
DEFAULT_PAGE_SIZE = 100

# Time Constants
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 86400
SECONDS_PER_WEEK = 604800
SECONDS_PER_MONTH = 2592000  # 30 days
SECONDS_PER_YEAR = 31536000  # 365 days

# Retention Constants
MIN_RETENTION_DAYS = 7
DEFAULT_RETENTION_DAYS = 90
MAX_RETENTION_DAYS = 3650  # 10 years

# Rate Limiting
DEFAULT_RATE_LIMIT_PER_MINUTE = 100
DEFAULT_RATE_LIMIT_PER_HOUR = 1000
DEFAULT_RATE_LIMIT_PER_DAY = 10000

# Export Constants
MAX_EXPORT_ROWS = 1_000_000
EXPORT_CHUNK_SIZE = 10_000
EXPORT_TIMEOUT_SECONDS = 300

# Cache Constants
CACHE_TTL_SHORT = 60  # 1 minute
CACHE_TTL_MEDIUM = 300  # 5 minutes
CACHE_TTL_LONG = 3600  # 1 hour
CACHE_TTL_DAY = 86400  # 24 hours

# Database Constants
DB_POOL_SIZE = 20
DB_MAX_OVERFLOW = 10
DB_POOL_TIMEOUT = 30
DB_POOL_RECYCLE = 3600

# Module Names
MODULES = [
    "analytics",
    "word",
    "excel",
    "powerpoint",
    "projects",
    "email",
    "chat",
    "flowcharts",
    "meetings",
    "calendar",
    "tasks",
    "notes",
    "files",
    "contacts",
    "reports",
    "dashboard",
    "settings",
    "admin",
    "notifications",
    "search",
    "help",
    "api",
    "integrations",
    "security",
]

# HTTP Status Codes
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_204_NO_CONTENT = 204
HTTP_400_BAD_REQUEST = 400
HTTP_401_UNAUTHORIZED = 401
HTTP_403_FORBIDDEN = 403
HTTP_404_NOT_FOUND = 404
HTTP_422_UNPROCESSABLE_ENTITY = 422
HTTP_429_TOO_MANY_REQUESTS = 429
HTTP_500_INTERNAL_SERVER_ERROR = 500
HTTP_503_SERVICE_UNAVAILABLE = 503

# Error Messages
ERROR_INVALID_INPUT = "Invalid input data"
ERROR_NOT_FOUND = "Resource not found"
ERROR_UNAUTHORIZED = "Unauthorized access"
ERROR_RATE_LIMIT = "Rate limit exceeded"
ERROR_SERVER = "Internal server error"
ERROR_DATABASE = "Database error"
ERROR_CACHE = "Cache error"
ERROR_EXPORT = "Export error"

# Success Messages
SUCCESS_CREATED = "Resource created successfully"
SUCCESS_UPDATED = "Resource updated successfully"
SUCCESS_DELETED = "Resource deleted successfully"
SUCCESS_EXPORTED = "Data exported successfully"
