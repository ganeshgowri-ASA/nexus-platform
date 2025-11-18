"""
Utility helper functions
"""
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import json
from pathlib import Path


def generate_id() -> str:
    """Generate a unique ID"""
    return str(uuid.uuid4())


def generate_short_id() -> str:
    """Generate a short unique ID"""
    return uuid.uuid4().hex[:12]


def current_timestamp() -> datetime:
    """Get current timestamp"""
    return datetime.utcnow()


def format_timestamp(dt: datetime, format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime to string"""
    return dt.strftime(format)


def parse_timestamp(timestamp_str: str, format: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """Parse string to datetime"""
    return datetime.strptime(timestamp_str, format)


def add_time(dt: datetime, **kwargs) -> datetime:
    """Add time to datetime"""
    return dt + timedelta(**kwargs)


def safe_json_loads(data: str, default: Any = None) -> Any:
    """Safely load JSON data"""
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(data: Any, default: str = "{}") -> str:
    """Safely dump data to JSON"""
    try:
        return json.dumps(data)
    except (TypeError, ValueError):
        return default


def ensure_path(path: str) -> Path:
    """Ensure path exists and return Path object"""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def read_file(file_path: str) -> Optional[str]:
    """Read file content"""
    try:
        with open(file_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return None


def write_file(file_path: str, content: str) -> bool:
    """Write content to file"""
    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            f.write(content)
        return True
    except Exception:
        return False


def file_exists(file_path: str) -> bool:
    """Check if file exists"""
    return Path(file_path).exists()


def delete_file(file_path: str) -> bool:
    """Delete file"""
    try:
        Path(file_path).unlink()
        return True
    except FileNotFoundError:
        return False
